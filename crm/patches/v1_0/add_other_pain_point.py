import frappe


def execute():
	categories = ["Alloys", "Plating", "Machines"]

	if frappe.db.exists("CRM Pain Point", "Other"):
		doc = frappe.get_doc("CRM Pain Point", "Other")
	else:
		doc = frappe.get_doc(
			{
				"doctype": "CRM Pain Point",
				"pain_point": "Other",
				"pain_type": "Technical",
			}
		)

	existing = {row.product_category for row in doc.product_categories}
	for category in categories:
		if category not in existing:
			doc.append("product_categories", {"product_category": category})

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
