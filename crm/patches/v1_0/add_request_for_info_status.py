import frappe

# The new stage sits directly after Qualification (position 2), so every status from
# position 3 onwards shifts down by one.
NEW_STATUS = "Request for Info"
NEW_POSITION = 3


def execute():
	"""Add the `Request for Info` deal stage between Qualified and Tech Assignment.

	When the tech team asks the salesperson for more details, the deal used to be pushed
	back to Qualification with a hidden `sent_back_by_tech_team` flag — invisible in the
	pipeline. It now parks in its own stage until the salesperson answers.
	"""
	if not frappe.db.exists("CRM Deal Status", NEW_STATUS):
		# Shift downwards first (highest position first) so no two rows ever collide on
		# an intermediate position while the update runs.
		existing = frappe.get_all(
			"CRM Deal Status",
			filters={"position": [">=", NEW_POSITION]},
			fields=["name", "position"],
			order_by="position desc",
		)
		for status in existing:
			frappe.db.set_value("CRM Deal Status", status.name, "position", status.position + 1)

		frappe.get_doc(
			{
				"doctype": "CRM Deal Status",
				"deal_status": NEW_STATUS,
				"label": NEW_STATUS,
				"position": NEW_POSITION,
				# Ongoing, not On Hold: the dashboards build their pipeline from
				# `type in ("Open", "Ongoing")`, and these deals are still live.
				"type": "Ongoing",
				"probability": 10,
				"color": "amber",
				"active": 1,
			}
		).insert(ignore_permissions=True)

	# Deals already parked in Qualification by the old flow belong in the new stage.
	stuck = frappe.get_all(
		"CRM Deal",
		filters={"status": "Qualification", "sent_back_by_tech_team": 1},
		pluck="name",
	)
	for deal in stuck:
		frappe.db.set_value("CRM Deal", deal, "status", NEW_STATUS, update_modified=False)

	frappe.db.commit()
