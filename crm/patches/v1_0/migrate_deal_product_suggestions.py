import frappe
from frappe.utils import flt


def execute():
	if not frappe.db.exists("DocType", "CRM Product Suggestion"):
		return
	if not frappe.db.has_column("CRM Deal", "recommended_item_code"):
		return

	rows = frappe.db.sql(
		"""
		select name, recommended_item_code, trial_quantity
		from `tabCRM Deal`
		where coalesce(recommended_item_code, '') != ''
		""",
		as_dict=True,
	)

	for row in rows:
		try:
			if not frappe.db.exists("Item", row.recommended_item_code):
				continue

			if frappe.db.exists(
				"CRM Product Suggestion",
				{"parent": row.name, "parenttype": "CRM Deal", "parentfield": "product_suggestions"},
			):
				continue

			doc = frappe.get_doc("CRM Deal", row.name)
			doc.append(
				"product_suggestions",
				{
					"item": row.recommended_item_code,
					"quantity": flt(row.trial_quantity),
				},
			)
			doc.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				title="Deal Product Suggestion Migration Skipped",
				message=frappe.get_traceback(),
			)
