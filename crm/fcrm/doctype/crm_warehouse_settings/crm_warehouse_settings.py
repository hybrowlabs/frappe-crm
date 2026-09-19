# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMWarehouseSettings(Document):
	def validate(self):
		seen = set()
		for row in self.branch_warehouses:
			if row.branch in seen:
				frappe.throw(_("Row #{0}: Branch {1} is listed more than once.").format(row.idx, row.branch))
			seen.add(row.branch)
			if frappe.db.get_value("Warehouse", row.warehouse, "is_group"):
				frappe.throw(
					_("Row #{0}: {1} is a group warehouse; pick a warehouse that holds stock.").format(
						row.idx, row.warehouse
					)
				)


def get_branch_warehouse(branch):
	"""The warehouse set for this branch, or None."""
	return frappe.db.get_value(
		"CRM Branch Warehouse",
		{"parent": "CRM Warehouse Settings", "parentfield": "branch_warehouses", "branch": branch},
		"warehouse",
	)
