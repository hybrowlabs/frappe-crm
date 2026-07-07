import json

import frappe


def execute():
	# GST in, employee count out for the Organization list quick filters.
	name = frappe.db.exists("CRM Global Settings", {"dt": "CRM Organization"})
	if name:
		frappe.db.set_value(
			"CRM Global Settings",
			name,
			"json",
			json.dumps(["organization_name", "gstin", "territory", "industry"]),
		)
