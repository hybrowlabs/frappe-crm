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
	"""Per-item purchase aggregates plus quote-created catalogue rows.

	Submitted Sales Orders are authoritative for quantity/value. CRM Previous
	Order Items keeps quote-created items visible at quantity 0 until an order is
	submitted for them.
	"""
	previous_items = frappe.get_all(
		"CRM Previous Order Items",
		filters={"parent": organization, "parenttype": "CRM Organization"},
		fields=["item_code", "quantity"],
	)
	items = get_order_items(get_customer(organization))
	today = getdate()
	month_ago = add_days(today, -30)
	quarter_ago = add_days(today, -90)

	agg = {}
	for previous in previous_items:
		if not previous.item_code:
			continue
		item = frappe.db.get_value(
			"Item",
			previous.item_code,
			["item_name", "stock_uom"],
			as_dict=True,
		) or {}
		agg[previous.item_code] = {
			"item_code": previous.item_code,
			"item_name": item.get("item_name") or previous.item_code,
			"uom": item.get("stock_uom"),
			"monthly_vol": 0,
			"quarterly_vol": 0,
			"total_qty": 0,
			"total_purchase": 0,
			"last_purchase": None,
		}

	for it in items:
		row = agg.setdefault(
			it.item_code,
			{
				"item_code": it.item_code,
				"item_name": it.item_name or it.item_code,
				"uom": it.stock_uom,
				"monthly_vol": 0,
				"quarterly_vol": 0,
				"total_qty": 0,
				"total_purchase": 0,
				"last_purchase": None,
			},
		)
		qty = flt(it.qty)
		row["total_qty"] += qty
		row["total_purchase"] += flt(it.base_amount)
		d = getdate(it.date) if it.date else None
		if d:
			if row["last_purchase"] is None or d > row["last_purchase"]:
				row["last_purchase"] = d
			if d >= month_ago:
				row["monthly_vol"] += qty
			if d >= quarter_ago:
				row["quarterly_vol"] += qty

	rows = sorted(agg.values(), key=lambda r: r["total_purchase"], reverse=True)
	return {
		"items": rows,
		"total_purchase": sum(r["total_purchase"] for r in rows),
		"count": len(rows),
	}


@frappe.whitelist()
def get_analytics(organization: str) -> dict:
	"""KPI tiles, 12-week trade volume, top items and spend-by-category for the Analytics tab."""
	items = get_order_items(get_customer(organization))
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

	cat_val = {}
	for it in items:
		cat = it.item_group or "Uncategorized"
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
		},
		"weekly_volume": list(reversed(weeks)),
		"top_items": top_items,
		"spend_by_category": spend_by_category,
		"last_order": org.get("last_order"),
		"credit_terms": org.get("credit_terms"),
	}
