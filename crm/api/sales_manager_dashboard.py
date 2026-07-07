import frappe
from frappe.utils import add_days, flt, getdate, now_datetime

# ---------------------------------------------------------------------------
# Team scoping
# ---------------------------------------------------------------------------
# "My team" = the account executives who own the organizations the logged-in
# Sales Manager manages (CRM Organization.sales_manager == session user). If the
# session user manages no organizations (common on small / freshly-seeded data)
# we fall back to a whole-company view so the dashboard is still populated, and
# flag it with is_fallback so the UI can say so. No numbers are ever faked.


def _open_statuses():
	return [
		s.name
		for s in frappe.get_all(
			"CRM Deal Status",
			filters={"type": ["in", ["Open", "Ongoing"]]},
			fields=["name", "position"],
			order_by="position",
		)
	]


def _team():
	me = frappe.session.user
	managed = frappe.get_all(
		"CRM Organization",
		filters={"sales_manager": me},
		fields=["name", "account_owner"],
	)
	if managed:
		org_names = [o.name for o in managed]
		aes = sorted({o.account_owner for o in managed if o.account_owner})
		if not aes:
			aes = [me]
		return aes, org_names, False
	# Fallback — no managed orgs mapped to this user.
	all_orgs = [o.name for o in frappe.get_all("CRM Organization", fields=["name"])]
	aes = sorted(
		{
			d.deal_owner
			for d in frappe.get_all("CRM Deal", filters={"deal_owner": ["is", "set"]}, fields=["deal_owner"])
			if d.deal_owner
		}
	)
	return aes, all_orgs, True


def _value(d):
	return flt(d.deal_value) or flt(d.annual_revenue)


def _pipeline(team_aes, is_fallback, statuses):
	filters = {"status": ["in", statuses]} if statuses else {}
	if not is_fallback and team_aes:
		filters["deal_owner"] = ["in", team_aes]
	deals = frappe.get_all(
		"CRM Deal",
		filters=filters,
		fields=[
			"name",
			"organization",
			"organization_name",
			"deal_owner",
			"status",
			"deal_value",
			"annual_revenue",
			"product_category",
			"territory",
			"modified",
		],
	)

	total_value = sum(_value(d) for d in deals)

	# Per-AE pipeline value + open deal count.
	by_ae_map = {}
	for d in deals:
		ae = d.deal_owner or "Unassigned"
		row = by_ae_map.setdefault(ae, {"ae": ae, "value": 0, "deals": 0})
		row["value"] += _value(d)
		row["deals"] += 1
	by_ae = sorted(by_ae_map.values(), key=lambda r: r["value"], reverse=True)

	# By stage (open statuses, ordered).
	by_stage = []
	for name in statuses:
		group = [d for d in deals if d.status == name]
		if group:
			by_stage.append({"stage": name, "count": len(group), "value": sum(_value(d) for d in group)})

	# By product category.
	cat = {}
	for d in deals:
		if d.product_category:
			cat[d.product_category] = cat.get(d.product_category, 0) + _value(d)
	by_category = sorted(
		[
			{"category": k, "value": v, "pct": round(v / total_value * 100) if total_value else 0}
			for k, v in cat.items()
		],
		key=lambda r: r["value"],
		reverse=True,
	)

	# Each AE's stage distribution (matrix of counts).
	dist_stages = [s["stage"] for s in by_stage]
	dist_map = {}
	for d in deals:
		ae = d.deal_owner or "Unassigned"
		row = dist_map.setdefault(ae, {s: 0 for s in dist_stages})
		if d.status in row:
			row[d.status] += 1
	stage_dist = sorted(
		[
			{"ae": ae, "dist": [counts[s] for s in dist_stages], "total": sum(counts.values())}
			for ae, counts in dist_map.items()
		],
		key=lambda r: r["total"],
		reverse=True,
	)

	deal_rows = [
		{
			"name": d.name,
			"organization": d.organization,
			"organization_name": d.organization_name or d.organization,
			"stage": d.status,
			"category": d.product_category,
			"ae": d.deal_owner,
			"value": _value(d),
		}
		for d in deals
	]

	return {
		"team_value": total_value,
		"team_open_count": len(deals),
		"open_statuses": statuses,
		"by_ae": by_ae,
		"by_stage": by_stage,
		"by_category": by_category,
		"stage_dist": {"stages": dist_stages, "rows": stage_dist},
		"deals": deal_rows,
	}


def _leads(team_aes, is_fallback):
	filters = {}
	if not is_fallback and team_aes:
		filters["lead_owner"] = ["in", team_aes]
	leads = frappe.get_all(
		"CRM Lead",
		filters=filters,
		fields=["name", "lead_name", "organization", "lead_owner", "first_responded_on", "creation", "converted"],
	)
	active = [l for l in leads if not l.converted]
	actioned = sum(1 for l in active if l.first_responded_on)
	not_actioned = len(active) - actioned

	cutoff = add_days(getdate(), -7)
	stale = [
		l
		for l in active
		if not l.first_responded_on and getdate(l.creation) < cutoff
	]
	stale.sort(key=lambda l: l.creation)
	today = getdate()
	not_contacted_7d = [
		{
			"name": l.name,
			"lead_name": l.lead_name or l.name,
			"organization": l.organization,
			"ae": l.lead_owner,
			"days": (today - getdate(l.creation)).days,
		}
		for l in stale[:15]
	]

	return {
		"assigned": len(active),
		"actioned": actioned,
		"not_actioned": not_actioned,
		"not_contacted_7d_count": len(stale),
		"not_contacted_7d": not_contacted_7d,
	}


def _activity(team_aes, org_names, is_fallback):
	now = now_datetime()
	today = getdate()

	# Overdue open tasks grouped by assignee.
	task_filters = {"status": ["in", ["Backlog", "Todo", "In Progress"]], "due_date": ["<", now]}
	if not is_fallback and team_aes:
		task_filters["assigned_to"] = ["in", team_aes]
	tasks = frappe.get_all("CRM Task", filters=task_filters, fields=["assigned_to"])
	overdue = {}
	for t in tasks:
		ae = t.assigned_to or "Unassigned"
		overdue[ae] = overdue.get(ae, 0) + 1
	overdue_by_ae = sorted(
		[{"ae": ae, "count": c} for ae, c in overdue.items()], key=lambda r: r["count"], reverse=True
	)

	# Calls logged this week grouped by caller.
	week_start = add_days(today, -today.weekday())
	call_filters = {"start_time": [">=", week_start]}
	if not is_fallback and team_aes:
		call_filters["caller"] = ["in", team_aes]
	calls = frappe.get_all("CRM Call Log", filters=call_filters, fields=["caller"])
	call_map = {}
	for c in calls:
		if c.caller:
			call_map[c.caller] = call_map.get(c.caller, 0) + 1
	calls_week = sorted(
		[{"ae": ae, "calls": n} for ae, n in call_map.items()], key=lambda r: r["calls"], reverse=True
	)

	# Managed accounts with no update in 30 days (proxy for "no logged activity").
	cutoff = add_days(today, -30)
	no_activity = []
	if org_names:
		orgs = frappe.get_all(
			"CRM Organization",
			filters={"name": ["in", org_names], "modified": ["<", cutoff]},
			fields=["name", "organization_name", "account_owner", "modified"],
		)
		for o in orgs:
			no_activity.append(
				{
					"organization": o.name,
					"organization_name": o.organization_name or o.name,
					"owner": o.account_owner,
					"days": (today - getdate(o.modified)).days,
				}
			)
		no_activity.sort(key=lambda r: r["days"], reverse=True)

	return {
		"overdue_by_ae": overdue_by_ae,
		"calls_week": calls_week,
		"no_activity_30d_count": len(no_activity),
		"no_activity_30d": no_activity[:12],
	}


def _technical(team_aes, is_fallback, statuses):
	base = {}
	if not is_fallback and team_aes:
		base["deal_owner"] = ["in", team_aes]

	# Technical assignments awaiting response.
	pending_filters = dict(base)
	pending_filters.update({"assign_to_tech_team": 1, "evaluation_end": ["is", "not set"]})
	if statuses:
		pending_filters["status"] = ["in", statuses]
	pending = frappe.get_all(
		"CRM Deal",
		filters=pending_filters,
		fields=["name", "organization", "organization_name", "deal_owner", "assigned_tech_member", "modified"],
	)
	today = getdate()
	tech_pending = [
		{
			"name": p.name,
			"organization": p.organization,
			"organization_name": p.organization_name or p.organization,
			"ae": p.deal_owner,
			"tech_member": p.assigned_tech_member,
			"days": (today - getdate(p.modified)).days,
		}
		for p in pending
	]
	tech_pending.sort(key=lambda r: r["days"], reverse=True)

	# Average first-response time across the team's deals.
	resp_filters = dict(base)
	resp_filters["first_response_time"] = [">", 0]
	resp = frappe.db.get_value(
		"CRM Deal",
		resp_filters,
		["avg(first_response_time) as avg", "count(name) as n"],
		as_dict=True,
	)

	# Trials in progress (trial required, outcome not yet recorded).
	trial_filters = dict(base)
	trial_filters.update({"trial_required": 1, "trial_outcome": ["in", ["", None]]})
	if statuses:
		trial_filters["status"] = ["in", statuses]
	trial_rows = frappe.get_all(
		"CRM Deal",
		filters=trial_filters,
		fields=["name", "organization", "organization_name", "deal_owner", "product_category", "evaluation_end"],
	)
	trials = [
		{
			"name": t.name,
			"organization": t.organization,
			"organization_name": t.organization_name or t.organization,
			"ae": t.deal_owner,
			"product": t.product_category or "—",
			"expected": t.evaluation_end,
		}
		for t in trial_rows
	]

	# Trial conversion for the team (outcome recorded).
	conv_filters = dict(base)
	conv_filters["trial_outcome"] = ["in", ["Successful", "Partial", "Unsuccessful"]]
	outcomes = frappe.get_all("CRM Deal", filters=conv_filters, fields=["trial_outcome"])
	successful = sum(1 for o in outcomes if o.trial_outcome == "Successful")

	return {
		"tech_pending_count": len(tech_pending),
		"tech_pending": tech_pending[:12],
		"avg_response_seconds": flt(resp.avg) if resp else 0,
		"avg_response_count": (resp.n if resp else 0) or 0,
		"trials_count": len(trials),
		"trials": trials[:12],
		"trial_conversion": {
			"total": len(outcomes),
			"successful": successful,
			"rate": round(successful / len(outcomes) * 100) if outcomes else 0,
		},
	}


def _dormancy(org_names):
	today = getdate()
	at_risk, dormant = [], []
	if org_names:
		orgs = frappe.get_all(
			"CRM Organization",
			filters={"name": ["in", org_names], "last_order": ["is", "set"]},
			fields=["name", "organization_name", "account_owner", "last_order"],
		)
		for o in orgs:
			days = (today - getdate(o.last_order)).days
			row = {
				"organization": o.name,
				"organization_name": o.organization_name or o.name,
				"owner": o.account_owner,
				"last_order": o.last_order,
				"days": days,
			}
			if 20 <= days <= 30:
				at_risk.append(row)
			elif days > 30:
				dormant.append(row)
	at_risk.sort(key=lambda r: r["days"], reverse=True)
	dormant.sort(key=lambda r: r["days"], reverse=True)
	return {"at_risk": at_risk[:12], "dormant": dormant[:12]}


def _waiting_time(team_aes, is_fallback, statuses):
	filters = {"status": ["in", statuses]} if statuses else {}
	if not is_fallback and team_aes:
		filters["deal_owner"] = ["in", team_aes]
	deals = frappe.get_all("CRM Deal", filters=filters, fields=["status", "modified"])
	today = getdate()
	buckets = {}
	for d in deals:
		buckets.setdefault(d.status, []).append((today - getdate(d.modified)).days)
	rows = [
		{"stage": name, "avg_days": round(sum(v) / len(v)), "count": len(v)}
		for name, v in buckets.items()
		if v
	]
	rows.sort(key=lambda r: r["avg_days"], reverse=True)
	return rows


@frappe.whitelist()
def get_sales_manager_dashboard() -> dict:
	"""Sales Manager dashboard metrics for the logged-in manager's team, computed
	live from CRM Deals / Leads / Tasks / Call Logs / Organizations. No mock data."""
	statuses = _open_statuses()
	team_aes, org_names, is_fallback = _team()
	return {
		"is_fallback": is_fallback,
		"team": team_aes,
		"pipeline": _pipeline(team_aes, is_fallback, statuses),
		"leads": _leads(team_aes, is_fallback),
		"activity": _activity(team_aes, org_names, is_fallback),
		"technical": _technical(team_aes, is_fallback, statuses),
		"dormancy": _dormancy(org_names),
		"waiting_time": _waiting_time(team_aes, is_fallback, statuses),
	}
