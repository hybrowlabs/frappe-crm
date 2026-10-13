import frappe
from frappe import _

# Item -> Branches (custom_branches) decides which branches show the item on
# the CRM's Available Stock page.


def validate(doc, method=None):
	"""Every branch on the item must have Stock Warehouses set in CRM Custom
	Settings, and appear only once."""
	rows = doc.get("custom_branches") or []
	if not rows:
		return

	allowed = set(
		frappe.get_all(
			"CRM Branch Stock Warehouse",
			filters={"parent": "CRM Custom Settings", "parentfield": "branch_stock_warehouses"},
			pluck="branch",
		)
	)
	seen = set()
	for row in rows:
		if row.branch in seen:
			frappe.throw(
				_("Branches Row #{0}: Branch {1} is listed more than once.").format(row.idx, row.branch),
				title=_("Duplicate Branch"),
			)
		seen.add(row.branch)
		if row.branch not in allowed:
			frappe.throw(
				_(
					"Branches Row #{0}: Branch {1} has no Stock Warehouses set in CRM Custom Settings."
				).format(row.idx, row.branch),
				title=_("Branch Not Set Up"),
			)
