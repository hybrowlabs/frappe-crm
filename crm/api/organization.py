import frappe
from frappe.utils import add_days, flt, getdate


def get_customer(organization):
	return frappe.db.get_value("CRM Organization", organization, "erpnext_customer")


def get_order_items(customer):
	"""Every submitted Sales Order Item for the customer, each tagged with its order date."""
	if not customer or not frappe.db.exists("DocType", "Sales Order"):
		return []

	orders = frappe.get_all(
		"Sales Order",
		filters={"customer": customer, "docstatus": 1},
		fields=["name", "transaction_date"],
	)
	if not orders:
		return []

	date_map = {o.name: o.transaction_date for o in orders}
	items = frappe.get_all(
		"Sales Order Item",
		filters={"parent": ["in", list(date_map)], "parenttype": "Sales Order"},
		fields=["item_code", "item_name", "qty", "stock_uom", "base_amount", "item_group", "parent"],
	)
	for it in items:
		it["date"] = date_map.get(it.parent)
	return items


@frappe.whitelist()
def get_ordered_items(organization: str) -> dict:
	"""Stored ordered-item snapshot for the Organization tab."""
	rows = frappe.get_all(
		"CRM Previous Order Items",
		filters={"parent": organization, "parenttype": "CRM Organization"},
		fields=[
			"item_code",
			"item_name",
			"uom",
			"monthly_volume",
			"quarterly_volume",
			"last_purchase",
			"total_purchase",
			"quantity",
		],
		order_by="total_purchase desc, item_code asc",
	)

	items = [
		{
			"item_code": row.item_code,
			"item_name": row.item_name or row.item_code,
			"uom": row.uom,
			"monthly_vol": flt(row.monthly_volume),
			"quarterly_vol": flt(row.quarterly_volume),
			"last_purchase": row.last_purchase,
			"total_purchase": flt(row.total_purchase),
			"total_qty": flt(row.quantity),
		}
		for row in rows
	]
	return {
		"items": items,
		"total_purchase": sum(row["total_purchase"] for row in items),
		"count": len(items),
	}


CATEGORY_ROOT = "Stock"


def get_category_resolver():
	"""Map any item group to the top-level category it sits under.

	Categories are the groups directly below CATEGORY_ROOT (Plating, Machine,
	Alloy). Item Group is a nested set, so a leaf belongs to the category whose
	lft..rgt range contains it — which keeps the mapping live: re-parent a group
	in ERPNext and past orders re-categorise with it, at any tree depth.
	"""
	if not frappe.db.exists("DocType", "Item Group"):
		return lambda item_group: item_group or "Uncategorized"

	categories = frappe.get_all(
		"Item Group",
		filters={"is_group": 1, "parent_item_group": CATEGORY_ROOT},
		fields=["name", "lft", "rgt"],
		order_by="lft",
	)
	if not categories:
		return lambda item_group: item_group or "Uncategorized"

	lft_by_group = {
		g.name: g.lft for g in frappe.get_all("Item Group", fields=["name", "lft"])
	}

	def to_category(item_group):
		lft = lft_by_group.get(item_group)
		if lft is None:
			return "Uncategorized"
		for c in categories:
			if c.lft <= lft <= c.rgt:
				return c.name
		return "Uncategorized"

	return to_category


def get_payment_status(customer):
	"""Unpaid invoice balance for the customer, split into overdue and total outstanding.

	Overdue is the part of the outstanding whose due date has already passed, so it
	is always a subset of outstanding — never a separate bucket to add on top.
	"""
	empty = {"outstanding": 0, "overdue": 0, "overdue_count": 0, "max_overdue_days": 0}
	if not customer or not frappe.db.exists("DocType", "Sales Invoice"):
		return empty

	rows = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["outstanding_amount", "due_date"],
	)
	if not rows:
		return empty

	today = getdate()
	outstanding = overdue = overdue_count = max_days = 0
	for r in rows:
		amount = flt(r.outstanding_amount)
		outstanding += amount
		if r.due_date and getdate(r.due_date) < today:
			overdue += amount
			overdue_count += 1
			max_days = max(max_days, (today - getdate(r.due_date)).days)

	return {
		"outstanding": outstanding,
		"overdue": overdue,
		"overdue_count": overdue_count,
		"max_overdue_days": max_days,
	}


@frappe.whitelist()
def get_analytics(organization: str) -> dict:
	"""KPI tiles, 12-week trade volume, top items and spend-by-category for the Analytics tab."""
	customer = get_customer(organization)
	items = get_order_items(customer)
	payments = get_payment_status(customer)
	org = (
		frappe.db.get_value(
			"CRM Organization",
			organization,
			["repeat_revenue", "health_score", "last_order", "credit_terms"],
			as_dict=True,
		)
		or {}
	)
	today = getdate()

	total_purchases = sum(flt(it.base_amount) for it in items)
	total_qty = sum(flt(it.qty) for it in items)

	uom_qty = {}
	for it in items:
		uom_qty[it.stock_uom] = uom_qty.get(it.stock_uom, 0) + flt(it.qty)
	uom = max(uom_qty, key=uom_qty.get) if uom_qty else ""

	# Volume bucketed by week index back from today; W1 (oldest) .. W12 (newest).
	weeks = [0] * 12
	for it in items:
		if not it.date:
			continue
		wk = (today - getdate(it.date)).days // 7
		if 0 <= wk < 12:
			weeks[wk] += flt(it.qty)
	vol_12w = sum(weeks)
	this_week, last_week = weeks[0], weeks[1]
	wow = ((this_week - last_week) / last_week * 100) if last_week else 0

	item_val = {}
	for it in items:
		key = it.item_name or it.item_code
		entry = item_val.setdefault(key, {"item": key, "value": 0, "qty": 0, "uom": it.stock_uom})
		entry["value"] += flt(it.base_amount)
		entry["qty"] += flt(it.qty)
	top_items = sorted(item_val.values(), key=lambda r: r["value"], reverse=True)[:5]

	to_category = get_category_resolver()
	cat_val = {}
	for it in items:
		cat = to_category(it.item_group)
		cat_val[cat] = cat_val.get(cat, 0) + flt(it.base_amount)
	spend_by_category = [
		{
			"category": cat,
			"value": val,
			"pct": round(val / total_purchases * 100) if total_purchases else 0,
		}
		for cat, val in sorted(cat_val.items(), key=lambda kv: kv[1], reverse=True)
	]

	return {
		"kpis": {
			"total_purchases": total_purchases,
			"total_qty": total_qty,
			"uom": uom,
			"avg_weekly": vol_12w / 12 if vol_12w else 0,
			"wow": round(wow),
			"repeat_revenue": flt(org.get("repeat_revenue")),
			"health_score": flt(org.get("health_score")),
			"outstanding": payments["outstanding"],
			"overdue": payments["overdue"],
			"overdue_count": payments["overdue_count"],
			"max_overdue_days": payments["max_overdue_days"],
		},
		"weekly_volume": list(reversed(weeks)),
		"top_items": top_items,
		"spend_by_category": spend_by_category,
		"last_order": org.get("last_order"),
		"credit_terms": org.get("credit_terms"),
	}
