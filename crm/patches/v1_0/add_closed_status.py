import frappe

# Terminal stage, so it goes at the very end — nothing needs renumbering.
NEW_STATUS = "Closed"


def execute():
	"""Add the `Closed` deal stage after Lost.

	A deal whose new-product proposal the Sales Manager declines is closed rather than
	lost: it never reached a commercial decision, so counting it as a lost deal would
	overstate losses. It is typed `Lost` all the same, which keeps it out of the open
	pipeline in the dashboard queries and lets a deal move here from any stage without
	tripping the intermediate stage gates.
	"""
	if frappe.db.exists("CRM Deal Status", NEW_STATUS):
		return

	last = frappe.db.sql("select max(position) from `tabCRM Deal Status`")[0][0] or 0

	frappe.get_doc(
		{
			"doctype": "CRM Deal Status",
			"deal_status": NEW_STATUS,
			"label": NEW_STATUS,
			"position": last + 1,
			"type": "Lost",
			"probability": 0,
			"color": "gray",
			"active": 1,
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
