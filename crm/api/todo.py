import frappe
from frappe import _

from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def after_insert(doc, method):
	if doc.reference_type in ["CRM Lead", "CRM Deal"] and doc.reference_name and doc.allocated_to:
		fieldname = "lead_owner" if doc.reference_type == "CRM Lead" else "deal_owner"
		owner = frappe.db.get_value(doc.reference_type, doc.reference_name, fieldname)
		if not owner:
			frappe.db.set_value(
				doc.reference_type, doc.reference_name, fieldname, doc.allocated_to, update_modified=False
			)

	if (
		doc.reference_type in ["CRM Lead", "CRM Deal", "CRM Task"]
		and doc.reference_name
		and doc.allocated_to
		and not frappe.flags.get("skip_assignment_notification")
	):
		notify_assigned_user(doc)


def on_update(doc, method):
	if (
		doc.has_value_changed("status")
		and doc.status == "Cancelled"
		and doc.reference_type in ["CRM Lead", "CRM Deal", "CRM Task"]
		and doc.reference_name
		and doc.allocated_to
	):
		notify_assigned_user(doc, is_cancelled=True)


def notify_assigned_user(doc, is_cancelled=False):
	_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
	owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
	notification_text = get_notification_text(owner, doc, _doc, is_cancelled)

	message = (
		_("Your assignment on {0} {1} has been removed by {2}").format(
			doc.reference_type, doc.reference_name, owner
		)
		if is_cancelled
		else _("{0} assigned a {1} {2} to you").format(owner, doc.reference_type, doc.reference_name)
	)

	redirect_to_doctype, redirect_to_name = get_redirect_to_doc(doc)

	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": doc.allocated_to,
			"notification_type": "Assignment",
			"message": message,
			"notification_text": notification_text,
			"reference_doctype": doc.reference_type,
			"reference_docname": doc.reference_name,
			"redirect_to_doctype": redirect_to_doctype,
			"redirect_to_docname": redirect_to_name,
		}
	)

	# Email the assignee when a lead is assigned to them (auto-by-territory, manual,
	# or import), so the assignment isn't missed outside the CRM. Never let an email
	# failure block the assignment / lead creation.
	if not is_cancelled and doc.reference_type == "CRM Lead":
		try:
			send_lead_assignment_email(doc.allocated_to, _doc, owner)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Lead assignment email failed")


def send_lead_assignment_email(recipient_user, lead, assigned_by):
	"""Send the assignee a branded email that a lead was assigned to them. Skips
	self-assignment (no point emailing yourself)."""
	if not recipient_user or recipient_user == frappe.session.user:
		return
	recipient = frappe.db.get_value("User", recipient_user, "email") or recipient_user
	if not recipient:
		return

	lead_url = frappe.utils.get_url(f"/crm/leads/{lead.name}")
	assigned_by = frappe.utils.escape_html(assigned_by or "")
	lead_title = frappe.utils.escape_html(lead.get("lead_name") or lead.name)

	content = f"""
	<div style="background:#f4f5f6;padding:32px 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
		<table role="presentation" align="center" cellpadding="0" cellspacing="0" width="480" style="max-width:480px;width:100%;background:#ffffff;border-radius:12px;border:1px solid #e8eaed;">
			<tr><td style="padding:32px 32px 28px 32px;text-align:center;">
				<h1 style="font-size:20px;line-height:1.35;color:#1f272e;margin:0 0 10px 0;">{_('A new lead has been assigned to you')}</h1>
				<p style="font-size:15px;color:#6b7280;margin:0 0 24px 0;">{_('{0} assigned the lead {1} to you.').format(assigned_by, f'<span style="color:#1f272e;font-weight:600;">{lead_title}</span>')}</p>
				<a href="{lead_url}" style="display:inline-block;background:#1f272e;color:#ffffff;text-decoration:none;font-size:14px;font-weight:500;padding:11px 24px;border-radius:8px;">{_('Open the Lead')} &rarr;</a>
			</td></tr>
		</table>
	</div>
	"""

	frappe.sendmail(
		recipients=[recipient],
		subject=_("A lead has been assigned to you: {0}").format(lead.get("lead_name") or lead.name),
		content=content,
		reference_doctype="CRM Lead",
		reference_name=lead.name,
	)


def get_notification_text(owner, doc, reference_doc, is_cancelled=False):
	name = doc.reference_name
	doctype = doc.reference_type

	if doctype.startswith("CRM "):
		doctype = doctype[4:].lower()

	if doctype in ["lead", "deal"]:
		name = (
			reference_doc.lead_name or name
			if doctype == "lead"
			else reference_doc.organization or reference_doc.lead_name or name
		)

		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{ _('Your assignment on {0} {1} has been removed by {2}').format(
                        doctype,
                        f'<span class="font-medium text-ink-gray-9">{ name }</span>',
                        f'<span class="font-medium text-ink-gray-9">{ owner }</span>'
                    ) }</span>
                </div>
            """

		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{ owner }</span>
                <span>{ _('assigned a {0} {1} to you').format(
                    doctype,
                    f'<span class="font-medium text-ink-gray-9">{ name }</span>'
                ) }</span>
            </div>
        """

	if doctype == "task":
		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{ _('Your assignment on task {0} has been removed by {1}').format(
                        f'<span class="font-medium text-ink-gray-9">{ reference_doc.title }</span>',
                        f'<span class="font-medium text-ink-gray-9">{ owner }</span>'
                    ) }</span>
                </div>
            """
		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{ owner }</span>
                <span>{ _('assigned a new task {0} to you').format(
                    f'<span class="font-medium text-ink-gray-9">{ reference_doc.title }</span>'
                ) }</span>
            </div>
        """


def get_redirect_to_doc(doc):
	if doc.reference_type == "CRM Task":
		reference_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
		return reference_doc.reference_doctype, reference_doc.reference_docname

	return doc.reference_type, doc.reference_name
