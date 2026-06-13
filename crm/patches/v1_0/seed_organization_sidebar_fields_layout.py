import json

import frappe

# Organization detail left-side panel, matching the Precious Alloys prototype
# (crm_react/app/org.jsx OrgRecordPanel): Details, Account, Health & Credit.
SECTIONS = [
	{
		"label": "Details",
		"name": "details_section",
		"fields": [
			"organization_name",
			"website",
			"territory",
			"industry",
			"no_of_employees",
			"address",
		],
	},
	{
		"label": "Account",
		"name": "account_section",
		"fields": [
			"gstin",
			"account_type",
			"account_owner",
			"sales_manager",
			"region",
		],
	},
	{
		"label": "Health & Credit",
		"name": "health_credit_section",
		"fields": [
			"credit_terms",
			"last_order",
			"health_score",
			"repeat_revenue",
		],
	},
]


def execute():
	layout = build_layout()

	name = frappe.db.exists("CRM Fields Layout", {"dt": "CRM Organization", "type": "Side Panel"})
	if name:
		doc = frappe.get_doc("CRM Fields Layout", name)
	else:
		doc = frappe.new_doc("CRM Fields Layout")
		doc.dt = "CRM Organization"
		doc.type = "Side Panel"

	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)


def build_layout():
	sections = []
	for s in SECTIONS:
		sections.append(
			{
				"label": s["label"],
				"name": s["name"],
				"opened": True,
				"showEditButton": True,
				"columns": [{"name": s["name"] + "_column", "fields": s["fields"]}],
			}
		)
	return sections
