import frappe
from frappe.utils import add_months, flt, getdate

# Marketing dashboard — lead-volume, conversion, bulk-status and repeat-
# contribution views over CRM Leads (+ their converted deals and the ERPNext
# Sales Orders of marketing-sourced accounts). Every number is computed live.
#
# NOTE on "Sub-Source": CRM Lead has no sub_source field, so the second
# breakdown uses `industry` (the only populated secondary lead dimension) and is
# labelled accordingly. "Marketing-sourced" = lead/deal source in a marketing set.

MARKETING_SOURCES = ("Campaign", "Advertisement", "Website", "Exhibition", "Digital Marketing", "Events")

SOURCE_COLORS = ["#2490EF", "#8A5EF7", "#F5A623", "#22C55E", "#0891B2", "#E5484D", "#6B7280"]


def _has_sales_order():
	return frappe.db.exists("DocType", "Sales Order")


def _won_statuses():
	return [s.name for s in frappe.get_all("CRM Deal Status", filters={"type": "Won"}, fields=["name"])]


def _open_statuses():
	return [
		s.name
		for s in frappe.get_all("CRM Deal Status", filters={"type": ["in", ["Open", "Ongoing"]]}, fields=["name"])
	]


def _lead_volume(leads, today):
	month_start = today.replace(day=1)
	prev_start = getdate(add_months(month_start, -1))
	prev_end = getdate(month_start)
	q_month = ((today.month - 1) // 3) * 3 + 1
	q_start = today.replace(month=q_month, day=1)
	year_start = today.replace(month=1, day=1)

	mtd = prev = quarter = year = 0
	not_contacted = 0
	for l in leads:
		created = getdate(l.creation)
		if created >= month_start:
			mtd += 1
		if prev_start <= created < prev_end:
			prev += 1
		if created >= q_start:
			quarter += 1
		if created >= year_start:
			year += 1
		if not l.first_responded_on and (today - created).days > 7:
			not_contacted += 1

	return {
		"uploaded_mtd": mtd,
		"prev_month": prev,
		"this_quarter": quarter,
		"this_year": year,
		"not_contacted_7d": not_contacted,
	}


def _by_source(leads):
	src = {}
	for l in leads:
		key = l.source or "Unknown"
		src[key] = src.get(key, 0) + 1
	rows = sorted([{"label": k, "count": v} for k, v in src.items()], key=lambda r: r["count"], reverse=True)
	for i, r in enumerate(rows):
		r["color"] = SOURCE_COLORS[i % len(SOURCE_COLORS)]
	return rows


def _by_industry(leads):
	ind = {}
	for l in leads:
		if l.industry:
			ind[l.industry] = ind.get(l.industry, 0) + 1
	return sorted([{"label": k, "count": v} for k, v in ind.items()], key=lambda r: r["count"], reverse=True)


def _conversion(leads, today):
	month_start = today.replace(day=1)
	converted = [l for l in leads if l.converted]
	total = len(leads)

	# No converted-date field → use lead.modified as the conversion timestamp proxy.
	converted_mtd = sum(1 for l in converted if getdate(l.modified) >= month_start)

	durations = [(getdate(l.modified) - getdate(l.creation)).days for l in converted]
	avg_days = round(sum(durations) / len(durations)) if durations else 0

	by_salesperson = {}
	for l in converted:
		key = l.lead_owner or "Unassigned"
		by_salesperson[key] = by_salesperson.get(key, 0) + 1
	sp_rows = sorted(
		[{"ae": k, "count": v} for k, v in by_salesperson.items()], key=lambda r: r["count"], reverse=True
	)

	# Conversion rate per source.
	src_total, src_conv = {}, {}
	for l in leads:
		key = l.source or "Unknown"
		src_total[key] = src_total.get(key, 0) + 1
		if l.converted:
			src_conv[key] = src_conv.get(key, 0) + 1
	conv_by_source = sorted(
		[
			{"label": k, "pct": round(src_conv.get(k, 0) / src_total[k] * 100), "converted": src_conv.get(k, 0), "total": src_total[k]}
			for k in src_total
		],
		key=lambda r: r["pct"],
		reverse=True,
	)

	# Marketing contribution to open pipeline (same basis as the CEO dashboard).
	open_statuses = _open_statuses()
	deals = frappe.get_all(
		"CRM Deal",
		filters={"status": ["in", open_statuses]} if open_statuses else {},
		fields=["deal_value", "annual_revenue", "source"],
	)
	total_pipe = sum(flt(d.deal_value) or flt(d.annual_revenue) for d in deals)
	mkt_pipe = sum(flt(d.deal_value) or flt(d.annual_revenue) for d in deals if d.source in MARKETING_SOURCES)

	return {
		"converted_mtd": converted_mtd,
		"conversion_rate": round(len(converted) / total * 100) if total else 0,
		"avg_days_to_conversion": avg_days,
		"by_salesperson": sp_rows,
		"conv_by_source": conv_by_source,
		"contribution_pct": round(mkt_pipe / total_pipe * 100) if total_pipe else 0,
	}


def _bulk(leads, today):
	rows = []
	for l in leads:
		age = (today - getdate(l.creation)).days
		contacted = bool(l.first_responded_on)
		rows.append(
			{
				"name": l.name,
				"lead_name": l.lead_name or l.name,
				"company": l.organization or "—",
				"source": l.source or "—",
				"industry": l.industry or "—",
				"ae": l.lead_owner,
				"status": l.status or "—",
				"days": age,
				"contacted": contacted,
				"last_activity_days": (today - getdate(l.modified)).days,
				"stale": (not contacted) and age > 14,
			}
		)
	rows.sort(key=lambda r: r["days"], reverse=True)
	stale = [r for r in rows if r["stale"]]
	return {"rows": rows[:60], "total": len(rows), "stale_count": len(stale)}


def _repeat_contribution(today):
	"""Revenue and repeat-buyer share for marketing-sourced accounts."""
	# Organizations whose originating deal came from a marketing source.
	mkt_org_names = set()
	for d in frappe.get_all(
		"CRM Deal",
		filters={"source": ["in", MARKETING_SOURCES], "organization": ["is", "set"]},
		fields=["organization"],
	):
		if d.organization:
			mkt_org_names.add(d.organization)

	revenue_from_mktg = 0.0
	now_repeat = 0
	total_mktg_accounts = len(mkt_org_names)
	contribution_pct = 0

	if mkt_org_names and _has_sales_order():
		orgs = frappe.get_all(
			"CRM Organization",
			filters={"name": ["in", list(mkt_org_names)], "erpnext_customer": ["is", "set"]},
			fields=["name", "erpnext_customer"],
		)
		cust_ids = [o.erpnext_customer for o in orgs if o.erpnext_customer]
		if cust_ids:
			rows = frappe.get_all(
				"Sales Order",
				filters={"docstatus": 1, "customer": ["in", cust_ids]},
				fields=["customer", "sum(base_grand_total) as value", "count(name) as orders"],
				group_by="customer",
			)
			for r in rows:
				revenue_from_mktg += flt(r.value)
				if r.orders and r.orders > 1:
					now_repeat += 1
			total_revenue = flt(frappe.db.get_value("Sales Order", {"docstatus": 1}, "sum(base_grand_total)"))
			contribution_pct = round(revenue_from_mktg / total_revenue * 100) if total_revenue else 0

	return {
		"revenue_from_mktg": revenue_from_mktg,
		"now_repeat_buyers": now_repeat,
		"total_mktg_accounts": total_mktg_accounts,
		"contribution_pct": contribution_pct,
		"has_orders": _has_sales_order(),
	}


@frappe.whitelist()
def get_marketing_dashboard() -> dict:
	"""Marketing dashboard — lead volume, conversion, bulk status and repeat
	contribution, computed live from CRM Leads / Deals / Organizations and
	ERPNext Sales Orders. No mock data."""
	today = getdate()
	leads = frappe.get_all(
		"CRM Lead",
		fields=[
			"name", "lead_name", "organization", "source", "industry", "status",
			"lead_owner", "converted", "first_responded_on", "creation", "modified",
		],
	)
	return {
		"lead_volume": _lead_volume(leads, today),
		"by_source": _by_source(leads),
		"by_industry": _by_industry(leads),
		"conversion": _conversion(leads, today),
		"bulk": _bulk(leads, today),
		"repeat": _repeat_contribution(today),
	}
