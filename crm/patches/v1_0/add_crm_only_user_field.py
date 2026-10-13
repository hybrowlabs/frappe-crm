import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# preferred anchors, top to bottom: the field is placed under the first one
# that exists. "Is Alumni Employee" lives only on UAT/Live, so it's found by label.
FALLBACK_ANCHORS = ("custom_disable_employee_self_service", "disable_mobile_access", "enabled")


def execute():
	create_custom_fields(
		{
			"User": [
				{
					"fieldname": "crm_only",
					"fieldtype": "Check",
					"label": "CRM Only",
					"insert_after": get_anchor(),
					"default": "0",
					"description": "When ticked, this user can only use the CRM app and cannot open ERPNext. "
					"After login, the user goes straight to CRM.",
				}
			]
		},
		ignore_validate=True,
	)


def get_anchor():
	meta = frappe.get_meta("User")
	alumni = next((df.fieldname for df in meta.fields if df.label == "Is Alumni Employee"), None)
	if alumni:
		return alumni

	return next((f for f in FALLBACK_ANCHORS if meta.has_field(f)), "enabled")
