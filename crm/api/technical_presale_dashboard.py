import frappe
from frappe.utils import flt, get_datetime, getdate, now_datetime

# Technical Pre-Sale dashboard — the CRM Pipeline phase only. "Technical
# assignment records" = CRM Deals routed to the tech team (assign_to_tech_team=1),
# with the technical engineer in `assigned_tech_member`. Response time is the
# deal's first_response_time (Duration, seconds). Trials use trial_outcome /
# evaluation_start / evaluation_end. Every number is live; nothing is faked.

# SLA response bands, in seconds. (label, tag, theme, low, high) — high None = open-ended.
BANDS = [
	("< 2h", "Excellent", "green", 0, 7200),
	("2–4h", "Acceptable", "blue", 7200, 14400),
	("4–8h", "Amber", "amber", 14400, 28800),
	("8–24h", "Amber/Red", "amber", 28800, 86400),
	("24–48h", "Breach", "red", 86400, 172800),
	("> 48h", "Critical", "red", 172800, None),
]


def _scope(view):
	"""Deal filter fragment: my assignments vs the whole team."""
	if view == "my":
		return {"assigned_tech_member": frappe.session.user}
	return {}


def _band_index(seconds):
	for i, (_, _, _, low, high) in enumerate(BANDS):
		if seconds >= low and (high is None or seconds < high):
			return i
	return len(BANDS) - 1


def _response_bands(view):
	filters = {"assign_to_tech_team": 1, "first_response_time": [">", 0]}
	filters.update(_scope(view))
	rows = frappe.get_all("CRM Deal", filters=filters, fields=["first_response_time"])
	counts = [0] * len(BANDS)
	for r in rows:
		counts[_band_index(flt(r.first_response_time))] += 1
	bands = [
		{"label": BANDS[i][0], "tag": BANDS[i][1], "theme": BANDS[i][2], "count": counts[i]}
		for i in range(len(BANDS))
	]
	# "My Average Response — This Month" (spec): restrict the average to responses
	# given in the current month (first_responded_on in this month).
	month_filters = dict(filters)
	month_filters["first_responded_on"] = [">=", getdate().replace(day=1)]
	avg = frappe.db.get_value("CRM Deal", month_filters, "avg(first_response_time)")
	return {"bands": bands, "total": sum(counts), "avg_seconds": flt(avg)}


def _open_assignments(view):
	filters = {
		"assign_to_tech_team": 1,
		"assigned_tech_member": ["is", "set"],
		"status": ["in", ["Tech Assignment", "Demo/Making"]],
	}
	filters.update(_scope(view))
	rows = frappe.get_all(
		"CRM Deal",
		filters=filters,
		fields=[
			"name", "organization", "organization_name", "product_category",
			"product_sub_category", "assigned_tech_member", "evaluation_start",
			"communication_status", "creation",
		],
	)
	now = now_datetime()
	out = []
	for r in rows:
		start = get_datetime(r.evaluation_start) if r.evaluation_start else get_datetime(r.creation)
		elapsed_h = round((now - start).total_seconds() / 3600, 1)
		out.append(
			{
				"name": r.name,
				"organization": r.organization,
				"organization_name": r.organization_name or r.organization,
				"product": r.product_category or "—",
				"sub_category": r.product_sub_category or "—",
				"tech_member": r.assigned_tech_member,
				"evaluation_start": r.evaluation_start,
				"communication_status": r.communication_status or "—",
				"elapsed_hours": elapsed_h,
			}
		)
	out.sort(key=lambda o: o["elapsed_hours"], reverse=True)
	overdue = [o for o in out if o["elapsed_hours"] >= 4]
	return {"open": out, "open_count": len(out), "overdue_count": len(overdue)}


def _trials(view):
	scope = _scope(view)
	base = {"trial_required": 1}
	base.update(scope)

	# "Trials I Managed This Month" (spec): trials whose outcome was concluded in
	# the current month (evaluation_end in this month).
	outcome_filters = dict(base)
	outcome_filters["trial_outcome"] = ["in", ["Successful", "Partial", "Unsuccessful"]]
	outcome_filters["evaluation_end"] = [">=", getdate().replace(day=1)]
	rows = frappe.get_all(
		"CRM Deal",
		filters=outcome_filters,
		fields=["trial_outcome", "evaluation_start", "evaluation_end"],
	)
	total = len(rows)
	first_attempt = sum(1 for r in rows if r.trial_outcome == "Successful")
	partial = sum(1 for r in rows if r.trial_outcome == "Partial")
	unsuccessful = sum(1 for r in rows if r.trial_outcome == "Unsuccessful")

	durations = [
		(getdate(r.evaluation_end) - getdate(r.evaluation_start)).days
		for r in rows
		if r.evaluation_start and r.evaluation_end
	]
	avg_duration = round(sum(durations) / len(durations)) if durations else 0

	return {
		"total": total,
		"first_attempt": first_attempt,
		"partial": partial,
		"unsuccessful": unsuccessful,
		"conversion_rate": round(first_attempt / total * 100) if total else 0,
		"avg_duration_days": avg_duration,
	}


def _engineers():
	"""Distinct tech engineers who carry assignments."""
	rows = frappe.get_all(
		"CRM Deal",
		filters={"assign_to_tech_team": 1, "assigned_tech_member": ["is", "set"]},
		fields=["assigned_tech_member"],
		distinct=True,
	)
	return [r.assigned_tech_member for r in rows if r.assigned_tech_member]


def _team_view():
	engineers = _engineers()

	# Per-engineer response distribution (< 2h / 2–8h / > 8h) + avg.
	team_response = []
	for eng in engineers:
		rows = frappe.get_all(
			"CRM Deal",
			filters={"assign_to_tech_team": 1, "assigned_tech_member": eng, "first_response_time": [">", 0]},
			fields=["first_response_time"],
		)
		if not rows:
			continue
		fast = sum(1 for r in rows if flt(r.first_response_time) < 7200)
		mid = sum(1 for r in rows if 7200 <= flt(r.first_response_time) < 28800)
		slow = sum(1 for r in rows if flt(r.first_response_time) >= 28800)
		avg = sum(flt(r.first_response_time) for r in rows) / len(rows)
		team_response.append(
			{"engineer": eng, "fast": fast, "mid": mid, "slow": slow, "avg_seconds": avg}
		)
	team_response.sort(key=lambda e: e["avg_seconds"])

	# Assignments by sub-category (workload).
	sub_rows = frappe.get_all(
		"CRM Deal",
		filters={"assign_to_tech_team": 1, "product_sub_category": ["is", "set"]},
		fields=["product_sub_category"],
	)
	sub_map = {}
	for r in sub_rows:
		sub_map[r.product_sub_category] = sub_map.get(r.product_sub_category, 0) + 1
	by_sub = sorted(
		[{"label": k, "count": v} for k, v in sub_map.items()], key=lambda r: r["count"], reverse=True
	)

	# Trial conversion ranked by engineer.
	conv_by_engineer = []
	resp_by_engineer = []
	for eng in engineers:
		trials = frappe.get_all(
			"CRM Deal",
			filters={"trial_required": 1, "assigned_tech_member": eng, "trial_outcome": ["in", ["Successful", "Partial", "Unsuccessful"]]},
			fields=["trial_outcome"],
		)
		if trials:
			won = sum(1 for t in trials if t.trial_outcome == "Successful")
			conv_by_engineer.append({"engineer": eng, "rate": round(won / len(trials) * 100)})
		avg = frappe.db.get_value(
			"CRM Deal",
			{"assign_to_tech_team": 1, "assigned_tech_member": eng, "first_response_time": [">", 0]},
			"avg(first_response_time)",
		)
		if avg:
			resp_by_engineer.append({"engineer": eng, "avg_seconds": flt(avg)})
	conv_by_engineer.sort(key=lambda e: e["rate"], reverse=True)
	resp_by_engineer.sort(key=lambda e: e["avg_seconds"])

	return {
		"team_response": team_response,
		"by_sub_category": by_sub,
		"conv_by_engineer": conv_by_engineer,
		"resp_by_engineer": resp_by_engineer,
	}


@frappe.whitelist()
def get_technical_presale_dashboard(view: str = "my") -> dict:
	"""Technical Pre-Sale dashboard. view = 'my' (assignments where I am the
	assigned tech member) or 'team' (whole tech team / head view). All metrics are
	computed live from CRM Deal technical fields. No mock data."""
	if view not in ("my", "team"):
		view = "my"
	return {
		"view": view,
		"response": _response_bands(view),
		"open_assignments": _open_assignments(view),
		"trials": _trials(view),
		"team": _team_view() if view == "team" else None,
	}
