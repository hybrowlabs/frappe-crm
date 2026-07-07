import frappe


def execute():
	categories = ["Alloys", "Plating", "Machines"]
	# "Other" is the catch-all — map it to every sub-category so it always
	# appears regardless of the sub-category selected in the requirement modal.
	sub_categories = [
		row.name
		for row in frappe.get_all("CRM Product Sub Category", fields=["name"])
	]

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

	existing_sub = {row.product_sub_category for row in doc.product_sub_categories}
	for sub_category in sub_categories:
		if sub_category not in existing_sub:
			doc.append("product_sub_categories", {"product_sub_category": sub_category})

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
