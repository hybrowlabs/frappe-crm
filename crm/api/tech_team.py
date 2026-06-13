import frappe
import frappe.share
from frappe import _
from frappe.utils import nowdate

from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def assign_to_user(doctype, name, user, description):
	"""Assign a document to a user. The default desk Notification Log and CRM
	assignment notification fire as usual, in addition to our own notification."""
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
		first_name, full_name = frappe.db.get_value(
			"User", r.team_member, ["first_name", "full_name"]
		) or (r.team_member, r.team_member)
		options.append(
			{
				"value": r.name,
				"label": f"{r.product_category} — {first_name}",
				"full_name": full_name or r.team_member,
			}
		)
	return options


@frappe.whitelist()
def assign_tech_team(deal: str, tech_team: str, notes: str | None = None):
	"""Assign the deal to the member of the given CRM Tech Team entry and notify
	them via the standard CRM (in-app) notification, including any assignment notes."""
	member = frappe.db.get_value("CRM Tech Team", tech_team, "team_member")
	if not member:
		frappe.throw(_("No Tech Team member configured for {0}").format(tech_team))

	assign_to_user(
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

	send_assignment_email(deal, member, owner, notes)

	return member


def send_assignment_email(deal, member, assigned_by, notes=None):
	"""Email the assigned tech member so the assignment isn't missed when they're
	not actively in the CRM."""
	recipient = frappe.db.get_value("User", member, "email") or member
	if not recipient or member == frappe.session.user:
		return

	deal_url = frappe.utils.get_url(f"/crm/deals/{deal}")
	assigned_by = frappe.utils.escape_html(assigned_by)

	note_block = ""
	if notes:
		note_block = f"""
			<tr><td style="padding-top:16px;">
				<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#8d96a5;margin-bottom:4px;">{_('Assignment Note')}</div>
				<div style="font-size:14px;color:#1f272e;background:#f4f5f6;border-radius:8px;padding:12px 14px;">{frappe.utils.escape_html(notes)}</div>
			</td></tr>
		"""

	content = f"""
	<div style="background:#f4f5f6;padding:24px 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
		<table role="presentation" align="center" cellpadding="0" cellspacing="0" width="520" style="max-width:520px;width:100%;background:#ffffff;border-radius:12px;border:1px solid #e8eaed;">
			<tr><td style="padding:28px 28px 0 28px;">
				<div style="display:inline-block;font-size:12px;font-weight:600;color:#2490ef;background:#eef6ff;border-radius:20px;padding:5px 12px;">{_('Technical Evaluation')}</div>
				<h1 style="font-size:20px;line-height:1.35;color:#1f272e;margin:16px 0 6px 0;">{_('A deal has been assigned to you')}</h1>
				<p style="font-size:14px;color:#6b7280;margin:0;">{_('{0} assigned you to handle the technical evaluation for this deal.').format(assigned_by)}</p>
			</td></tr>
			<tr><td style="padding:20px 28px 0 28px;">
				<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e8eaed;border-radius:8px;">
					<tr><td style="padding:14px 16px;">
						<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#8d96a5;margin-bottom:4px;">{_('Deal')}</div>
						<div style="font-size:15px;font-weight:600;color:#1f272e;">{deal}</div>
					</td></tr>
				</table>
			</td></tr>
			<tr><td style="padding:0 28px;"><table role="presentation" cellpadding="0" cellspacing="0" width="100%">{note_block}</table></td></tr>
			<tr><td style="padding:24px 28px 28px 28px;">
				<a href="{deal_url}" style="display:inline-block;background:#1f272e;color:#ffffff;text-decoration:none;font-size:14px;font-weight:500;padding:11px 22px;border-radius:8px;">{_('Open the Deal')} &rarr;</a>
			</td></tr>
		</table>
		<p style="text-align:center;font-size:12px;color:#9aa4b2;margin:18px 0 0 0;">{_('Sent from your CRM')}</p>
	</div>
	"""

	frappe.sendmail(
		recipients=[recipient],
		subject=_("Deal {0} assigned to you for technical evaluation").format(deal),
		content=content,
		reference_doctype="CRM Deal",
		reference_name=deal,
	)
