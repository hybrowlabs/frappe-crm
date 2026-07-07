import frappe
from frappe.utils import add_days, add_months, flt, getdate

# Repeat Business dashboard — 80% of revenue is repeat, so this view is entirely
# account/order-centric. "Order records" = submitted ERPNext Sales Orders, joined
# to CRM Organizations through `erpnext_customer`. Every number is computed live;
# metrics whose source is absent (e.g. Service tickets) are omitted, never faked.

RB_CATEGORIES = ("Alloys", "Plating", "Machines")

# Lead sources treated as marketing-originated (mirrors ceo_dashboard.MARKETING_SOURCES).
MARKETING_SOURCES = ("Campaign", "Advertisement", "Website", "Exhibition", "Digital Marketing", "Events")


def _has_sales_order():
	return frappe.db.exists("DocType", "Sales Order")


def _won_statuses():
	return [s.name for s in frappe.get_all("CRM Deal Status", filters={"type": "Won"}, fields=["name"])]


def _order_stats(customers):
	"""Per-customer order counts / revenue across the windows the dashboard needs,
	computed from a single two-year Sales Order scan. Empty dict when SO is absent."""
	if not customers or not _has_sales_order():
		return {}
	today = getdate()
	scan_start = getdate(add_months(today.replace(day=1), -24))
	rows = frappe.get_all(
		"Sales Order",
		filters={
			"docstatus": 1,
			"customer": ["in", customers],
			"transaction_date": [">=", scan_start],
		},
		fields=["customer", "transaction_date", "base_grand_total"],
	)

	month_start = today.replace(day=1)
	last_month_start = getdate(add_months(month_start, -1))
	last_month_end = add_days(month_start, -1)
	q_month = ((today.month - 1) // 3) * 3 + 1
	q_start = today.replace(month=q_month, day=1)
	last_q_start = getdate(add_months(q_start, -3))
	last_q_end = add_days(q_start, -1)
	year_start = today.replace(month=1, day=1)
	last_year_start = getdate(add_months(year_start, -12))
	last_year_end = add_days(year_start, -1)
	rolling_3mo_start = getdate(add_months(month_start, -3))

	stats = {}
	for r in rows:
		d = getdate(r.transaction_date)
		amt = flt(r.base_grand_total)
		s = stats.setdefault(
			r.customer,
			{
				"this_month": 0, "last_month": 0, "this_qtr": 0, "ytd_orders": 0,
				"rev_ytd": 0.0, "rev_last_year": 0.0,
				"aov_q_sum": 0.0, "aov_q_n": 0, "aov_lastq_sum": 0.0, "aov_lastq_n": 0,
				"orders_3mo": 0,
			},
		)
		if d >= month_start:
			s["this_month"] += 1
		if last_month_start <= d <= last_month_end:
			s["last_month"] += 1
		if d >= q_start:
			s["this_qtr"] += 1
			s["aov_q_sum"] += amt
			s["aov_q_n"] += 1
		if last_q_start <= d <= last_q_end:
			s["aov_lastq_sum"] += amt
			s["aov_lastq_n"] += 1
		if d >= year_start:
			s["ytd_orders"] += 1
			s["rev_ytd"] += amt
		if last_year_start <= d <= last_year_end:
			s["rev_last_year"] += amt
		if d >= rolling_3mo_start:
			s["orders_3mo"] += 1
	return stats


def _categories_by_org():
	"""Product categories each organization has actually bought — distinct
	product_category across that org's Won deals."""
	won = _won_statuses()
	if not won:
		return {}
	deals = frappe.get_all(
		"CRM Deal",
		filters={"status": ["in", won], "product_category": ["is", "set"]},
		fields=["organization", "product_category"],
	)
	out = {}
	for d in deals:
		if d.organization:
			out.setdefault(d.organization, set()).add(d.product_category)
	return out


def _marketing_orgs():
	"""Organizations whose originating deal/lead came from a marketing source."""
	orgs = set()
	for d in frappe.get_all(
		"CRM Deal",
		filters={"source": ["in", MARKETING_SOURCES], "organization": ["is", "set"]},
		fields=["organization"],
	):
		if d.organization:
			orgs.add(d.organization)
	return orgs


def _status(row, days):
	# An account with no order history at all (no orders in any window and no
	# last-order date) has nothing to judge — mark it "No Data", not Healthy.
	has_history = row["ytd_orders"] or row["this_month"] or row["last_month"] or row["this_qtr"]
	if days is None and not has_history:
		return "No Data"
	if days is not None and days > 30:
		return "Dormant"
	if row["this_month"] < row["avg3mo"] or (row["aov_q"] and row["aov_q"] < row["aov_lastq"]):
		return "Declining"
	return "Healthy"


def _accounts():
	today = getdate()
	orgs = frappe.get_all(
		"CRM Organization",
		fields=[
			"name", "organization_name", "account_owner", "erpnext_customer",
			"last_order", "ordering_below_average", "declining_order_value", "modified",
		],
	)
	cust_ids = [o.erpnext_customer for o in orgs if o.erpnext_customer]
	stats = _order_stats(cust_ids)
	cats = _categories_by_org()
	mkt_orgs = _marketing_orgs()

	accounts = []
	for o in orgs:
		st = stats.get(o.erpnext_customer, {})
		days = (today - getdate(o.last_order)).days if o.last_order else None
		orders_3mo = st.get("orders_3mo", 0)
		aov_q = st.get("aov_q_sum", 0) / st["aov_q_n"] if st.get("aov_q_n") else 0
		aov_lastq = st.get("aov_lastq_sum", 0) / st["aov_lastq_n"] if st.get("aov_lastq_n") else 0
		row = {
			"organization": o.name,
			"organization_name": o.organization_name or o.name,
			"ae": o.account_owner,
			"this_month": st.get("this_month", 0),
			"last_month": st.get("last_month", 0),
			"this_qtr": st.get("this_qtr", 0),
			"ytd_orders": st.get("ytd_orders", 0),
			"rev_ytd": st.get("rev_ytd", 0.0),
			"rev_last_year": st.get("rev_last_year", 0.0),
			"avg3mo": round(orders_3mo / 3, 1),
			"aov_q": aov_q,
			"aov_lastq": aov_lastq,
			"last_order": o.last_order,
			"days": days,
			"last_interaction_days": (today - getdate(o.modified)).days,
			"cats": sorted(cats.get(o.name, [])),
			"below_avg_signal": bool(o.ordering_below_average),
			"declining_signal": bool(o.declining_order_value),
			"is_marketing": o.name in mkt_orgs,
		}
		accounts.append(row)
	return accounts


@frappe.whitelist()
def get_repeat_business_dashboard() -> dict:
	"""Repeat Business dashboard — order-frequency, early-warning, dormancy,
	revenue-trend, cross-sell and marketing-repeat views over CRM Organizations
	and their ERPNext Sales Orders. No mock data."""
	has_orders = _has_sales_order()
	accounts = _accounts()

	# ---- order frequency ----
	order_3plus = [a for a in accounts if a["this_month"] >= 3]
	active_freq = [a for a in accounts if a["ytd_orders"] or a["this_month"]]
	avg_freq = round(sum(a["this_month"] for a in accounts) / len(accounts), 1) if accounts else 0
	dormant_30 = [a for a in accounts if a["days"] is not None and a["days"] > 30]
	dormant_60 = [a for a in accounts if a["days"] is not None and a["days"] > 60]
	winback_90 = [a for a in accounts if a["days"] is not None and a["days"] >= 90]

	freq_rows = []
	for a in accounts:
		status = _status(a, a["days"])
		freq_rows.append({**a, "status": status})
	healthy = [a for a in freq_rows if a["status"] == "Healthy"]

	# ---- early warning ----
	below_avg = [a for a in accounts if (a["this_month"] < a["avg3mo"]) or a["below_avg_signal"]]
	declining_value = [a for a in accounts if (a["aov_q"] and a["aov_q"] < a["aov_lastq"]) or a["declining_signal"]]
	no_order_2029 = [a for a in accounts if a["days"] is not None and 20 <= a["days"] <= 29]

	# ---- revenue trend ----
	rev_sorted = sorted([a for a in accounts if a["rev_ytd"] or a["rev_last_year"]], key=lambda a: a["rev_ytd"], reverse=True)
	top_by_freq = sorted([a for a in accounts if a["ytd_orders"]], key=lambda a: a["ytd_orders"], reverse=True)
	total_rev = sum(a["rev_ytd"] for a in accounts)
	top10_rev = sum(a["rev_ytd"] for a in rev_sorted[:10])
	conc_pct = round(top10_rev / total_rev * 100) if total_rev else 0

	# ---- cross-sell ----
	one_cat = [a for a in accounts if len(a["cats"]) == 1]
	gap_rows = [a for a in accounts if a["cats"]]

	# ---- marketing repeat ----
	mkt_repeat = sorted(
		[a for a in accounts if a["is_marketing"] and a["ytd_orders"] >= 2],
		key=lambda a: a["rev_ytd"],
		reverse=True,
	)

	def trim(rows, n=25):
		return rows[:n]

	return {
		"has_orders": has_orders,
		"total_accounts": len(accounts),
		"order_frequency": {
			"order_3plus_count": len(order_3plus),
			"avg_freq": avg_freq,
			"healthy_count": len(healthy),
			"dormant_30_count": len(dormant_30),
			"rows": trim(sorted(freq_rows, key=lambda a: a["this_month"], reverse=True), 40),
		},
		"early_warning": {
			"below_avg_count": len(below_avg),
			"declining_value_count": len(declining_value),
			"no_order_2029_count": len(no_order_2029),
			"below_avg": trim(sorted(below_avg, key=lambda a: a["avg3mo"] - a["this_month"], reverse=True)),
			"declining_value": trim(sorted(declining_value, key=lambda a: a["aov_lastq"] - a["aov_q"], reverse=True)),
		},
		"dormant": {
			"d30_count": len(dormant_30),
			"d60_count": len(dormant_60),
			"winback_count": len(winback_90),
			"rows": trim(sorted(dormant_30, key=lambda a: a["days"], reverse=True), 40),
			"winback": trim(sorted(winback_90, key=lambda a: a["days"], reverse=True)),
		},
		"revenue_trend": {
			"rows": trim(rev_sorted, 40),
			"top_by_freq": top_by_freq[:20],
			"concentration": {
				"top_n": 10,
				"top_pct": conc_pct,
				"top_value": top10_rev,
				"rest_value": total_rev - top10_rev,
				"total_value": total_rev,
			},
		},
		"cross_sell": {
			"one_cat_count": len(one_cat),
			"one_cat": trim(one_cat),
			"categories": list(RB_CATEGORIES),
			"gap_rows": trim(gap_rows, 40),
			"order_3plus_count": len(order_3plus),
		},
		"marketing_repeat": trim(mkt_repeat),
	}
