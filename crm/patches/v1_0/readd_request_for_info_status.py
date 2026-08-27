import frappe

# The stage sits directly after Qualified (position 2), so every status from position 3
# onwards shifts down by one.
NEW_STATUS = "Request for New Info"
NEW_POSITION = 3


def execute():
	"""Bring back the `Request for New Info` deal stage between Qualified and Tech Assignment.

	A deal the tech team sends back for more details used to drop into Qualification with
	only the hidden `sent_back_by_tech_team` flag to mark it — invisible in the pipeline.
	It parks in its own stage again, while the answer is still collected inside the
	Qualified stage form (the header CTA stays "Continue Trial").
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

	# Deals parked in Qualification by the flag-only flow belong in the stage.
	stuck = frappe.get_all(
		"CRM Deal",
		filters={"status": "Qualification", "sent_back_by_tech_team": 1},
		pluck="name",
	)
	for deal in stuck:
		frappe.db.set_value("CRM Deal", deal, "status", NEW_STATUS, update_modified=False)

	frappe.db.commit()
