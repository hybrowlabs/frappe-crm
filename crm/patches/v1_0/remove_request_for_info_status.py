import frappe

# The stage sat between Qualification (2) and Tech Assignment (4), so every status from
# position 4 onwards shifts back up by one once it goes.
OLD_STATUS = "Request for Info"
OLD_POSITION = 3


def execute():
	"""Drop the `Request for Info` deal stage.

	The tech team's request for more details no longer parks the deal in a stage of its
	own with a stage form of its own — the deal drops back to Qualification carrying the
	`sent_back_by_tech_team` flag, and the salesperson answers the questions inside the
	Qualified stage form before assigning the tech team again.
	"""
	if not frappe.db.exists("CRM Deal Status", OLD_STATUS):
		return

	# Deals parked in the stage belong back in Qualification, still flagged as waiting
	# on an answer so the Qualified stage form asks for one.
	parked = frappe.get_all("CRM Deal", filters={"status": OLD_STATUS}, pluck="name")
	for deal in parked:
		frappe.db.set_value(
			"CRM Deal",
			deal,
			{"status": "Qualification", "sent_back_by_tech_team": 1},
			update_modified=False,
		)

	frappe.delete_doc("CRM Deal Status", OLD_STATUS, ignore_permissions=True, force=True)

	# Close the gap left in the pipeline order (lowest position first, so no two rows
	# ever collide on an intermediate position while the update runs).
	following = frappe.get_all(
		"CRM Deal Status",
		filters={"position": [">", OLD_POSITION]},
		fields=["name", "position"],
		order_by="position asc",
	)
	for status in following:
		frappe.db.set_value("CRM Deal Status", status.name, "position", status.position - 1)

	frappe.db.commit()
