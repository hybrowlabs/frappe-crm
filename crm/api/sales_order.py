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
	org.set("previous_order_items", [])
	for item_code, quantity in totals.items():
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
