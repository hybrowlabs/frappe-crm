import frappe
import frappe.share
from frappe import _
from frappe.utils import nowdate

from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def quiet_assign(doctype, name, user, description):
	"""Assign a document to a user without firing the default desk Notification Log
	or the default CRM assignment notification — we send our own instead."""
	exists = frappe.get_all(
		"ToDo",
		filters={
			"reference_type": doctype,
			"reference_name": str(name),
			"allocated_to": user,
			"status": "Open",
		},
		limit=1,
	)
	if exists:
		return

	frappe.flags.skip_assignment_notification = True
	try:
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": user,
				"reference_type": doctype,
				"reference_name": str(name),
				"description": description,
				"status": "Open",
				"date": nowdate(),
				"assigned_by": frappe.session.user,
			}
		).insert(ignore_permissions=True)
	finally:
		frappe.flags.skip_assignment_notification = False

	# give the assignee access to the document
	doc = frappe.get_doc(doctype, name)
	if not frappe.has_permission(doc=doc, user=user):
		frappe.share.add(doctype, str(name), user)


@frappe.whitelist()
def get_tech_teams():
	"""Tech Team options for selection — value is the record name, label reads
	as 'Product Category — Member First Name' (as in the prototype)."""
	rows = frappe.get_all(
		"CRM Tech Team",
		fields=["name", "product_category", "team_member"],
		order_by="product_category asc",
	)
	options = []
	for r in rows:
		first_name = frappe.db.get_value("User", r.team_member, "first_name") or r.team_member
		options.append({"value": r.name, "label": f"{r.product_category} — {first_name}"})
	return options


@frappe.whitelist()
def assign_tech_team(deal: str, tech_team: str, notes: str | None = None):
	"""Assign the deal to the member of the given CRM Tech Team entry and notify
	them via the standard CRM (in-app) notification, including any assignment notes."""
	member = frappe.db.get_value("CRM Tech Team", tech_team, "team_member")
	if not member:
		frappe.throw(_("No Tech Team member configured for {0}").format(tech_team))

	quiet_assign(
		"CRM Deal",
		deal,
		member,
		notes or _("Trial initiated — assigned for technical evaluation"),
	)

	owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
	note_section = ""
	if notes:
		note_section = f"""
				<span>{ _('with note:') }</span>
				<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(notes) }</span>
		"""
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ owner }</span>
			<span>{ _('assigned this deal for technical evaluation') }</span>
			{ note_section }
		</div>
	"""
	message = (
		_("Assigned for technical evaluation with note: {0}").format(notes)
		if notes
		else _("Assigned for technical evaluation")
	)
	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": member,
			"notification_type": "Assignment",
			"message": message,
			"notification_text": notification_text,
			"reference_doctype": "CRM Deal",
			"reference_docname": deal,
			"redirect_to_doctype": "CRM Deal",
			"redirect_to_docname": deal,
		}
	)

	return member
