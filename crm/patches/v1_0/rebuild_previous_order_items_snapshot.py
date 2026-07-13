import frappe

from crm.api.sales_order import rebuild_previous_order_items


def execute():
	customers = frappe.get_all(
		"CRM Organization",
		filters={"erpnext_customer": ["is", "set"]},
		pluck="erpnext_customer",
	)
	for customer in sorted(set(customers)):
		rebuild_previous_order_items(customer)
