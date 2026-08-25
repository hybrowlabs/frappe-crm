import frappe

# The new stage sits directly after Tech Assignment (position 3), so every status from
# position 4 onwards shifts down by one.
NEW_STATUS = "New Product Development"
NEW_POSITION = 4


def execute():
	"""Add the `New Product Development` deal stage between Tech Assignment and Tech Evaluation.

	When no existing product fits an Alloys enquiry, the tech team proposes a new alloy
	instead of forcing a recommendation or killing the deal as Not Suitable. The deal parks
	in this stage — assigned to the salesperson and their manager — until the Sales Manager
	approves it onward to Tech Evaluation or declines it.
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
				"probability": 22,
				"color": "violet",
				"active": 1,
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()
