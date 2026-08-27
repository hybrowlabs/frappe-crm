import frappe

OLD_STATUS = "Request for Info"
NEW_STATUS = "Request for New Info"


def execute():
	"""Rename the `Request for Info` deal stage to `Request for New Info`.

	The stage was created under the shorter label; the pipeline wording settled on
	"Request for New Info", so sites that ran `readd_request_for_info_status` before
	the rename still carry the old name. `CRM Deal Status` is the link target for
	`CRM Deal.status`, so a plain rename carries the deals across with it.
	"""
	if not frappe.db.exists("CRM Deal Status", OLD_STATUS):
		return

	if frappe.db.exists("CRM Deal Status", NEW_STATUS):
		# Both exist: move the deals over and drop the stale row.
		frappe.db.set_value(
			"CRM Deal", {"status": OLD_STATUS}, "status", NEW_STATUS, update_modified=False
		)
		frappe.delete_doc("CRM Deal Status", OLD_STATUS, ignore_permissions=True, force=True)
	else:
		frappe.rename_doc("CRM Deal Status", OLD_STATUS, NEW_STATUS, force=True, show_alert=False)
		frappe.db.set_value("CRM Deal Status", NEW_STATUS, "deal_status", NEW_STATUS)
		frappe.db.set_value("CRM Deal Status", NEW_STATUS, "label", NEW_STATUS)

	frappe.db.commit()
