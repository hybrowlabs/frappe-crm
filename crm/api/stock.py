import frappe
from frappe import _
from frappe.query_builder.functions import Sum

from crm.api.quotation import _session_sales_person, can_see_all_quotations
from crm.fcrm.doctype.crm_custom_settings.crm_custom_settings import get_branch_stock_warehouses

# CRM "Available Stock" page: item-wise stock of a branch, added up over the
# child warehouses CRM Custom Settings -> Stock Warehouses sets for it.


def _allowed_branches():
	"""Branches the session user may view: every configured branch for
	Administrator / System Manager, otherwise the user's Sales Person branches."""
	if can_see_all_quotations():
		return frappe.get_all(
			"CRM Branch Stock Warehouse",
			filters={"parent": "CRM Custom Settings", "parentfield": "branch_stock_warehouses"},
			pluck="branch",
			order_by="idx asc",
		)
	sales_person = _session_sales_person()
	if not sales_person:
		return []
	branches = frappe.get_all(
		"Sales Person Branch",
		filters={"parenttype": "Sales Person", "parent": sales_person, "parentfield": "custom_branches"},
		pluck="branch",
		order_by="idx asc",
	)
	# A branch can be on several rows (one per currency).
	return list(dict.fromkeys(branches))


@frappe.whitelist()
def get_stock_branches():
	"""Branches for the page's Branch dropdown."""
	return _allowed_branches()


@frappe.whitelist()
def get_available_stock(branch: str):
	"""Items with stock above zero in the branch's warehouses, with the total
	Actual Qty across them."""
	if branch not in _allowed_branches():
		frappe.throw(_("Branch {0} is not set on your Sales Person.").format(branch), frappe.PermissionError)

	warehouses = get_branch_stock_warehouses(branch)
	if not warehouses:
		return {"warehouses": [], "items": []}

	bin = frappe.qb.DocType("Bin")
	item = frappe.qb.DocType("Item")
	total = Sum(bin.actual_qty)
	items = (
		frappe.qb.from_(bin)
		.join(item)
		.on(item.name == bin.item_code)
		.select(bin.item_code, item.item_name, item.stock_uom, total.as_("qty"))
		.where(bin.warehouse.isin(warehouses))
		.groupby(bin.item_code, item.item_name, item.stock_uom)
		.having(total > 0)
		.orderby(bin.item_code)
		.run(as_dict=True)
	)
	return {"warehouses": warehouses, "items": items}
