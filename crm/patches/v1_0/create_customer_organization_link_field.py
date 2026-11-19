import frappe


def execute():
	if not frappe.db.get_single_value("ERPNext CRM Settings", "enabled"):
		return

	frappe.get_single("ERPNext CRM Settings").create_custom_fields_in_frappe_crm()
