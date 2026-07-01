import frappe


@frappe.whitelist()
def get_previous_order_items(deal):
	"""Item codes previously ordered by the deal's organization, for prefilling
	a new Quotation (one row per item, quantity left for the user to fill)."""
	organization = frappe.db.get_value("CRM Deal", deal, "organization")
	if not organization:
		return []

	return frappe.get_all(
		"CRM Previous Order Items",
		filters={"parent": organization, "parenttype": "CRM Organization"},
		pluck="item_code",
	)


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
	"""Aggregate item_code -> total quantity across all submitted Sales Orders of
	the given ERPNext customer. Used to (re)build a CRM Organization's previously
	ordered items. Returns {} if there's no customer or ERPNext/Sales Order isn't
	available."""
	if not customer or not frappe.db.exists("DocType", "Sales Order"):
		return {}

	orders = frappe.get_all("Sales Order", filters={"customer": customer, "docstatus": 1}, pluck="name")
	if not orders:
		return {}

	rows = frappe.get_all(
		"Sales Order Item",
		filters={"parent": ["in", orders], "parenttype": "Sales Order"},
		fields=["item_code", "qty"],
	)
	totals = {}
	for r in rows:
		if not r.item_code or not r.qty:
			continue
		totals[r.item_code] = totals.get(r.item_code, 0) + r.qty
	return totals


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
		row.quantity = totals.get(row.item_code, 0)
		existing.add(row.item_code)
	for item_code, quantity in totals.items():
		if item_code not in existing:
			org.append("previous_order_items", {"item_code": item_code, "quantity": quantity})

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
			org.append("previous_order_items", {"item_code": item.item_code, "quantity": 0})
			existing.add(item.item_code)
			added = True
	if added:
		org.save(ignore_permissions=True)
