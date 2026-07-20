import frappe


def execute():
	"""Mark all existing lead & deal statuses as active.

	The `active` check was added with default 1, but that only applies to new
	documents, existing rows get 0.
	"""
	for doctype in ("CRM Lead Status", "CRM Deal Status"):
		table = frappe.qb.DocType(doctype)
		frappe.qb.update(table).set(table.active, 1).run()

	frappe.db.commit()
