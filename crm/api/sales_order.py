import frappe
from frappe.utils import add_days, flt, getdate


@frappe.whitelist()
def get_previous_order_items(deal):
	"""Item codes to prefill a new Quotation created from this deal: the technical
	team's recommended item (from the Tech Assignment stage) first, then any items the
	deal's organization previously ordered. One row per item, quantity left blank."""
	item_codes = []

	recommended = frappe.db.get_value("CRM Deal", deal, "recommended_item_code")
	if recommended:
		item_codes.append(recommended)

	organization = frappe.db.get_value("CRM Deal", deal, "organization")
	if organization:
		previous = frappe.get_all(
			"CRM Previous Order Items",
			filters={"parent": organization, "parenttype": "CRM Organization"},
			pluck="item_code",
		)
		for code in previous:
			if code and code not in item_codes:
				item_codes.append(code)

	return item_codes


@frappe.whitelist()
def get_previous_order_items_for_customer(customer):
	"""Item codes previously ordered by the CRM Organization linked to this
	ERPNext customer — for prefilling a repeat-order Quotation that has no deal."""
	organization = frappe.db.get_value("CRM Organization", {"erpnext_customer": customer}, "name")
	if not organization:
		return []

	return frappe.get_all(
		"CRM Previous Order Items",
		filters={"parent": organization, "parenttype": "CRM Organization"},
		pluck="item_code",
	)


def get_ordered_items_for_customer(customer):
	"""Build the stored ordered-item snapshot from submitted Sales Orders."""
	if not customer or not frappe.db.exists("DocType", "Sales Order"):
		return {}

	orders = frappe.get_all(
		"Sales Order",
		filters={"customer": customer, "docstatus": 1},
		fields=["name", "transaction_date"],
	)
	if not orders:
		return {}

	date_map = {order.name: order.transaction_date for order in orders}
	rows = frappe.get_all(
		"Sales Order Item",
		filters={"parent": ["in", list(date_map)], "parenttype": "Sales Order"},
		fields=["item_code", "item_name", "qty", "stock_uom", "base_amount", "parent"],
	)
	today = getdate()
	month_ago = add_days(today, -30)
	quarter_ago = add_days(today, -90)
	totals = {}
	for r in rows:
		if not r.item_code or not r.qty:
			continue
		row = totals.setdefault(
			r.item_code,
			{
				"item_code": r.item_code,
				"item_name": r.item_name or r.item_code,
				"uom": r.stock_uom,
				"quantity": 0,
				"monthly_volume": 0,
				"quarterly_volume": 0,
				"total_purchase": 0,
				"last_purchase": None,
			},
		)
		qty = flt(r.qty)
		row["quantity"] += qty
		row["total_purchase"] += flt(r.base_amount)
		d = getdate(date_map.get(r.parent)) if date_map.get(r.parent) else None
		if d:
			if row["last_purchase"] is None or d > row["last_purchase"]:
				row["last_purchase"] = d
			if d >= month_ago:
				row["monthly_volume"] += qty
			if d >= quarter_ago:
				row["quarterly_volume"] += qty
	return totals


def get_item_snapshot_defaults(item_code):
	if not item_code:
		return {}
	item = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True) or {}
	return {
		"item_code": item_code,
		"item_name": item.get("item_name") or item_code,
		"uom": item.get("stock_uom"),
		"quantity": 0,
		"monthly_volume": 0,
		"quarterly_volume": 0,
		"total_purchase": 0,
		"last_purchase": None,
	}


def rebuild_previous_order_items(customer):
	"""Rebuild the linked CRM Organization's previously-ordered items from the
	authoritative aggregate of the customer's submitted Sales Orders, rather than
	incrementally adding/removing. Keeps the data correct regardless of edits,
	amendments, or out-of-order submit/cancel."""
	if not customer:
		return

	organization = frappe.db.get_value("CRM Organization", {"erpnext_customer": customer}, "name")
	if not organization:
		return

	totals = get_ordered_items_for_customer(customer)
	org = frappe.get_doc("CRM Organization", organization)
	# Update quantities from the Sales Order aggregate but never drop an item that's
	# already listed — items no longer in any Sales Order are kept with quantity 0.
	existing = set()
	for row in org.previous_order_items:
		total = totals.get(row.item_code) or get_item_snapshot_defaults(row.item_code)
		row.item_name = total.get("item_name")
		row.uom = total.get("uom")
		row.quantity = total.get("quantity", 0)
		row.monthly_volume = total.get("monthly_volume", 0)
		row.quarterly_volume = total.get("quarterly_volume", 0)
		row.total_purchase = total.get("total_purchase", 0)
		row.last_purchase = total.get("last_purchase")
		existing.add(row.item_code)
	for item_code, total in totals.items():
		if item_code not in existing:
			org.append("previous_order_items", total)

	org.save(ignore_permissions=True)


def update_previous_order_items(doc, method=None):
	"""On Sales Order submit, recompute the linked CRM Organization's previously
	ordered items from all of the customer's submitted Sales Orders."""
	rebuild_previous_order_items(doc.customer)


def reduce_previous_order_items(doc, method=None):
	"""On Sales Order cancel, recompute the linked CRM Organization's previously
	ordered items from the customer's remaining submitted Sales Orders."""
	rebuild_previous_order_items(doc.customer)


def add_quotation_items_to_previous_order_items(doc, method=None):
	"""On Quotation create, add its items to the linked CRM Organization's previously
	ordered items with quantity 0 if not already present. Quantities stay driven by
	Sales Orders; this only grows the item catalogue."""
	organization = None
	if doc.quotation_to == "Customer" and doc.party_name:
		organization = frappe.db.get_value(
			"CRM Organization", {"erpnext_customer": doc.party_name}, "name"
		)
	elif doc.get("custom_deal"):
		organization = frappe.db.get_value("CRM Deal", doc.custom_deal, "organization")
	if not organization:
		return

	org = frappe.get_doc("CRM Organization", organization)
	existing = {row.item_code for row in org.previous_order_items}
	added = False
	for item in doc.items:
		if item.item_code and item.item_code not in existing:
			org.append("previous_order_items", get_item_snapshot_defaults(item.item_code))
			existing.add(item.item_code)
			added = True
	if added:
		org.save(ignore_permissions=True)
