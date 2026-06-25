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


def update_previous_order_items(doc, method=None):
	"""On Sales Order submit, record/increment ordered item quantities on the
	linked CRM Organization (matched via the order's ERPNext Customer)."""
	if not doc.customer:
		return

	organization = frappe.db.get_value(
		"CRM Organization", {"erpnext_customer": doc.customer}, "name"
	)
	if not organization:
		return

	org = frappe.get_doc("CRM Organization", organization)
	existing = {row.item_code: row for row in org.previous_order_items}

	for item in doc.items:
		if not item.item_code or not item.qty:
			continue
		if item.item_code in existing:
			existing[item.item_code].quantity += item.qty
		else:
			org.append(
				"previous_order_items",
				{"item_code": item.item_code, "quantity": item.qty},
			)

	org.save(ignore_permissions=True)


def reduce_previous_order_items(doc, method=None):
	"""On Sales Order cancel, subtract the order's quantities back out of the
	linked CRM Organization's recorded items (dropping rows that hit zero)."""
	if not doc.customer:
		return

	organization = frappe.db.get_value(
		"CRM Organization", {"erpnext_customer": doc.customer}, "name"
	)
	if not organization:
		return

	org = frappe.get_doc("CRM Organization", organization)
	existing = {row.item_code: row for row in org.previous_order_items}

	for item in doc.items:
		if not item.item_code or not item.qty:
			continue
		row = existing.get(item.item_code)
		if not row:
			continue
		row.quantity -= item.qty
		if row.quantity <= 0:
			org.previous_order_items.remove(row)

	org.save(ignore_permissions=True)
