import frappe
from frappe.utils import add_days, add_months, flt, getdate

# Lead sources treated as marketing-originated for the "Marketing Contribution"
# metric. Adjust to match the client's channel taxonomy.
MARKETING_SOURCES = ("Campaign", "Advertisement", "Website", "Exhibition", "Digital Marketing", "Events")


def _open_statuses():
	"""Pipeline = deal statuses that are neither Won nor Lost."""
	return [
		s.name
		for s in frappe.get_all(
			"CRM Deal Status",
			filters={"type": ["in", ["Open", "Ongoing"]]},
			fields=["name", "position"],
			order_by="position",
		)
	]


def _period_bounds(period):
	"""(start, end, prev_start, prev_end, ly_start, ly_end) for the selected period.
	prev = the equal-length window immediately before; ly = the same window a year ago."""
	today = getdate()
	if period == "quarter":
		start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
		prev_start = getdate(add_months(start, -3))
	elif period == "ytd":
		start = today.replace(month=1, day=1)
		prev_start = getdate(add_months(start, -12))
	else:
		start = today.replace(day=1)
		prev_start = getdate(add_months(start, -1))
	prev_end = add_days(start, -1)
	ly_start = getdate(add_months(start, -12))
	ly_end = getdate(add_months(today, -12))
	return start, today, prev_start, prev_end, ly_start, ly_end


def _so_sum(start, end, customers=None):
	if not frappe.db.exists("DocType", "Sales Order"):
		return 0
	filters = {"docstatus": 1, "transaction_date": ["between", [start, end]]}
	if customers is not None:
		if not customers:
			return 0
		filters["customer"] = ["in", customers]
	return flt(
		frappe.db.get_value("Sales Order", filters, "sum(base_grand_total)")
	)


def _so_count_by_customer(customers, start, end):
	if not customers or not frappe.db.exists("DocType", "Sales Order"):
		return {}
	rows = frappe.get_all(
		"Sales Order",
		filters={
			"docstatus": 1,
			"customer": ["in", customers],
			"transaction_date": ["between", [start, end]],
		},
		fields=["customer", "count(name) as orders"],
		group_by="customer",
	)
	return {r.customer: r.orders for r in rows}


def _pipeline(period):
	statuses = _open_statuses()
	deals = frappe.get_all(
		"CRM Deal",
		filters={"status": ["in", statuses]} if statuses else {},
		fields=[
			"name",
			"organization",
			"status",
			"deal_value",
			"annual_revenue",
			"territory",
			"product_category",
			"source",
		],
	)

	def value(d):
		return flt(d.deal_value) or flt(d.annual_revenue)

	total_value = sum(value(d) for d in deals)

	deal_rows = [
		{
			"name": d.name,
			"organization": d.organization,
			"stage": d.status,
			"category": d.product_category,
			"region": d.territory or "Unassigned",
			"value": value(d),
		}
		for d in deals
	]

	category = {}
	for d in deals:
		if d.product_category:
			category[d.product_category] = category.get(d.product_category, 0) + value(d)
	by_category = sorted(
		[
			{"category": k, "value": v, "pct": round(v / total_value * 100) if total_value else 0}
			for k, v in category.items()
		],
		key=lambda r: r["value"],
		reverse=True,
	)

	mkt_value = sum(value(d) for d in deals if d.source in MARKETING_SOURCES)

	by_stage = []
	for name in statuses:
		group = [d for d in deals if d.status == name]
		if group:
			by_stage.append(
				{"stage": name, "count": len(group), "value": sum(value(d) for d in group)}
			)

	region = {}
	for d in deals:
		key = d.territory or "Unassigned"
		region[key] = region.get(key, 0) + value(d)
	by_region = sorted(
		[{"region": k, "value": v} for k, v in region.items()],
		key=lambda r: r["value"],
		reverse=True,
	)

	start, today, prev_start, prev_end, ly_start, ly_end = _period_bounds(period)
	new_accounts = frappe.db.count(
		"CRM Organization", {"creation": ["between", [start, add_days(today, 1)]]}
	)

	rev_now = _so_sum(start, today)
	rev_prev = _so_sum(prev_start, prev_end)
	rev_ly = _so_sum(ly_start, ly_end)

	return {
		"total_value": total_value,
		"open_count": len(deals),
		"open_statuses": statuses,
		"deals": deal_rows,
		"revenue_booked": rev_now,
		"revenue_prev": rev_prev,
		"revenue_last_year": rev_ly,
		"new_accounts": new_accounts,
		"by_stage": by_stage,
		"by_category": by_category,
		"by_region": by_region,
		"marketing_value": mkt_value,
		"marketing_pct": round(mkt_value / total_value * 100) if total_value else 0,
	}


def _account_health():
	today = getdate()
	cutoff = add_days(today, -30)
	ytd_start = today.replace(month=1, day=1)

	orgs = frappe.get_all(
		"CRM Organization",
		fields=[
			"name",
			"organization_name",
			"last_order",
			"erpnext_customer",
			"account_owner",
			"declining_order_value",
			"ordering_below_average",
		],
	)

	dormant = []
	for o in orgs:
		if o.last_order and getdate(o.last_order) < cutoff:
			dormant.append(
				{
					"organization": o.name,
					"organization_name": o.organization_name,
					"last_order": o.last_order,
					"days": (today - getdate(o.last_order)).days,
				}
			)
	dormant.sort(key=lambda r: r["days"], reverse=True)

	at_risk_orgs = [o for o in orgs if o.declining_order_value or o.ordering_below_average]

	# This-quarter vs last-quarter order counts for the at-risk accounts.
	q_month = ((today.month - 1) // 3) * 3 + 1
	this_q_start = today.replace(month=q_month, day=1)
	last_q_start = getdate(add_months(this_q_start, -3))
	last_q_end = add_days(this_q_start, -1)
	risk_customers = [o.erpnext_customer for o in at_risk_orgs if o.erpnext_customer]
	this_q = _so_count_by_customer(risk_customers, this_q_start, today)
	last_q = _so_count_by_customer(risk_customers, last_q_start, last_q_end)
	accounts_at_risk = [
		{
			"organization": o.name,
			"organization_name": o.organization_name,
			"owner": o.account_owner,
			"last_qtr": last_q.get(o.erpnext_customer, 0),
			"this_qtr": this_q.get(o.erpnext_customer, 0),
		}
		for o in at_risk_orgs
	]

	# YTD revenue by customer → attribute to organizations.
	cust_to_org = {o.erpnext_customer: o for o in orgs if o.erpnext_customer}
	ytd_total = _so_sum(ytd_start, today)

	top_accounts = []
	repeat_value = 0
	if frappe.db.exists("DocType", "Sales Order") and cust_to_org:
		rows = frappe.get_all(
			"Sales Order",
			filters={
				"docstatus": 1,
				"customer": ["in", list(cust_to_org)],
				"transaction_date": ["between", [ytd_start, today]],
			},
			fields=["customer", "sum(base_grand_total) as value", "count(name) as orders"],
			group_by="customer",
		)
		for r in rows:
			org = cust_to_org.get(r.customer)
			if r.orders and r.orders > 1:
				repeat_value += flt(r.value)
			top_accounts.append(
				{
					"organization": org.name if org else r.customer,
					"organization_name": org.organization_name if org else r.customer,
					"value": flt(r.value),
				}
			)
		top_accounts.sort(key=lambda r: r["value"], reverse=True)
		top_accounts = top_accounts[:10]

	repeat_pct = round(repeat_value / ytd_total * 100) if ytd_total else 0

	return {
		"dormant_count": len(dormant),
		"dormant": dormant[:10],
		"at_risk_count": len(at_risk_orgs),
		"accounts_at_risk": accounts_at_risk[:10],
		"repeat_pct": repeat_pct,
		"ytd_revenue": ytd_total,
		"top_accounts": top_accounts,
	}


def _waiting_time():
	"""Proxy for stage waiting time: average days since a deal was last touched,
	grouped by stage. Uses the deal's modified timestamp (no activity log needed)."""
	statuses = _open_statuses()
	deals = frappe.get_all(
		"CRM Deal",
		filters={"status": ["in", statuses]} if statuses else {},
		fields=["status", "modified"],
	)
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


def _performance():
	"""Trial conversion, technical response time and marketing contribution — all
	from real CRM Deal fields. NPS is intentionally absent: no NPS data source exists."""
	trials = frappe.get_all(
		"CRM Deal",
		filters={"trial_outcome": ["in", ["Successful", "Partial", "Unsuccessful"]]},
		fields=["trial_outcome"],
	)
	successful = sum(1 for t in trials if t.trial_outcome == "Successful")
	trial_conversion = {
		"total": len(trials),
		"successful": successful,
		"rate": round(successful / len(trials) * 100) if trials else 0,
	}

	resp = frappe.db.get_value(
		"CRM Deal",
		{"first_response_time": [">", 0]},
		["avg(first_response_time) as avg", "count(name) as n"],
		as_dict=True,
	)

	return {
		"trial_conversion": trial_conversion,
		"tech_response_seconds": flt(resp.avg) if resp else 0,
		"tech_response_count": (resp.n if resp else 0) or 0,
	}


def _overdue_payments():
	if not frappe.db.exists("DocType", "Sales Invoice"):
		return {"amount": 0, "count": 0, "accounts": []}
	today = getdate()
	rows = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"due_date": ["<", today],
		},
		fields=["customer", "outstanding_amount", "due_date"],
	)
	by_cust = {}
	for r in rows:
		acc = by_cust.setdefault(
			r.customer, {"customer": r.customer, "amount": 0, "days": 0}
		)
		acc["amount"] += flt(r.outstanding_amount)
		acc["days"] = max(acc["days"], (today - getdate(r.due_date)).days)
	accounts = sorted(by_cust.values(), key=lambda a: a["amount"], reverse=True)
	return {
		"amount": sum(a["amount"] for a in accounts),
		"count": len(accounts),
		"accounts": accounts[:10],
	}


@frappe.whitelist()
def get_ceo_dashboard(period: str = "month") -> dict:
	"""CEO dashboard metrics for the given period (month / quarter / ytd), computed
	live from CRM Deals, CRM Organizations and ERPNext Sales Orders / Invoices."""
	if period not in ("month", "quarter", "ytd"):
		period = "month"
	return {
		"period": period,
		"pipeline": _pipeline(period),
		"account_health": _account_health(),
		"waiting_time": _waiting_time(),
		"performance": _performance(),
		"overdue_payments": _overdue_payments(),
	}
