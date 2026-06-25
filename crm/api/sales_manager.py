import random

import frappe
from frappe import _

from crm.api.tech_team import assign_to_user
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def _user_from_email(email):
	"""Return the CRM User matching an email (User name is usually the email, but
	fall back to the email field), or None."""
	if not email:
		return None
	if frappe.db.exists("User", email):
		return email
	return frappe.db.get_value("User", {"email": email}, "name")


def get_territory_sales_manager(territory):
	"""Resolve the CRM User acting as sales manager for a territory, via the ERPNext
	Territory's territory_manager (a Sales Person). Prefers the Sales Person's
	custom_email_id (added by another app); otherwise the linked Employee's user.
	Raises if neither resolves to a User."""
	if not territory:
		frappe.throw(_("Deal has no territory to resolve a sales manager from."))

	sales_person = frappe.db.get_value("Territory", territory, "territory_manager")
	if not sales_person:
		frappe.throw(_("No Territory Manager set on territory {0}.").format(territory))

	if frappe.db.has_column("Sales Person", "custom_email_id"):
		user = _user_from_email(
			frappe.db.get_value("Sales Person", sales_person, "custom_email_id")
		)
		if user:
			return user

	employee = frappe.db.get_value("Sales Person", sales_person, "employee")
	if employee:
		user = frappe.db.get_value("Employee", employee, "user_id")
		if user and frappe.db.exists("User", user):
			return user

	frappe.throw(
		_("Could not resolve a CRM user for the Territory Manager ({0}) of territory {1}.").format(
			sales_person, territory
		)
	)


def get_territory_users(territory):
	"""All CRM users reachable from a territory's manager (Sales Person): via the
	Sales Person's custom_email_id and via its linked Employee's user. Deduped;
	returns [] (no error) when the territory, manager, or users can't be resolved."""
	if not territory:
		return []

	sales_person = frappe.db.get_value("Territory", territory, "territory_manager")
	if not sales_person:
		return []

	users = []
	if frappe.db.has_column("Sales Person", "custom_email_id"):
		user = _user_from_email(
			frappe.db.get_value("Sales Person", sales_person, "custom_email_id")
		)
		if user:
			users.append(user)

	employee = frappe.db.get_value("Sales Person", sales_person, "employee")
	if employee:
		user = frappe.db.get_value("Employee", employee, "user_id")
		if user and frappe.db.exists("User", user):
			users.append(user)

	return list(dict.fromkeys(users))


def auto_assign_by_territory(doc, method=None):
	"""On insert, if a Lead/Deal has no assignee yet, assign it to a user resolved
	from its territory's manager (random pick if several). Territory is mandatory,
	but if it's somehow missing or resolves to no user, assignment is skipped."""
	already_assigned = frappe.get_all(
		"ToDo",
		filters={"reference_type": doc.doctype, "reference_name": doc.name, "status": "Open"},
		limit=1,
	)
	if already_assigned:
		return

	users = get_territory_users(doc.get("territory"))
	if not users:
		return

	assign_to_user(doc.doctype, doc.name, random.choice(users), _("Auto-assigned by territory"))


def _user_from_sales_person(sales_person):
	"""Forward-map a Sales Person to a CRM User (custom_email_id then employee.user_id)."""
	if not sales_person:
		return None
	if frappe.db.has_column("Sales Person", "custom_email_id"):
		user = _user_from_email(
			frappe.db.get_value("Sales Person", sales_person, "custom_email_id")
		)
		if user:
			return user
	employee = frappe.db.get_value("Sales Person", sales_person, "employee")
	if employee:
		user = frappe.db.get_value("Employee", employee, "user_id")
		if user and frappe.db.exists("User", user):
			return user
	return None


def _sales_person_from_user(user):
	"""Reverse-map a CRM User to its Sales Person record (via custom_email_id or
	the linked Employee's user_id)."""
	if not user:
		return None
	email = frappe.db.get_value("User", user, "email") or user
	if frappe.db.has_column("Sales Person", "custom_email_id"):
		sales_person = frappe.db.get_value("Sales Person", {"custom_email_id": email})
		if sales_person:
			return sales_person
	employee = frappe.db.get_value("Employee", {"user_id": user})
	if employee:
		sales_person = frappe.db.get_value("Sales Person", {"employee": employee})
		if sales_person:
			return sales_person
	return None


def _deal_sales_person_user(doc):
	"""The deal's sales person = the earliest open ToDo assignee that isn't the tech
	member. (At insert the territory sales person is assigned first, so the earliest
	non-tech assignee is the sales person.)"""
	tech_user = doc.get("assigned_tech_member")
	todos = frappe.get_all(
		"ToDo",
		filters={"reference_type": "CRM Deal", "reference_name": doc.name, "status": "Open"},
		fields=["allocated_to"],
		order_by="creation asc",
	)
	for t in todos:
		if t.allocated_to and t.allocated_to != tech_user:
			return t.allocated_to
	return None


def notify_roles_on_status_change(doc, method=None):
	"""On a deal status change, notify the other two of the trio — tech member,
	sales person (current assignee), and the sales person's immediate parent
	(sales manager) — whenever one of them made the change. Roles that aren't set
	(e.g. no tech member assigned) are simply skipped."""
	if not doc.has_value_changed("status"):
		return

	tech_user = doc.get("assigned_tech_member") or None
	sales_user = _deal_sales_person_user(doc)
	manager_user = None
	if sales_user:
		sales_person = _sales_person_from_user(sales_user)
		if sales_person:
			parent = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")
			manager_user = _user_from_sales_person(parent)

	# Notify the trio about the change. If the editor is one of them they're skipped
	# (so the other two are notified); if the editor is outside the trio, all three
	# are notified.
	trio = list(dict.fromkeys(u for u in (tech_user, sales_user, manager_user) if u))
	editor = frappe.session.user
	owner_name = frappe.get_cached_value("User", editor, "full_name") or editor
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ owner_name }</span>
			<span>{ _('changed the deal status to') }</span>
			<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(doc.status or '') }</span>
		</div>
	"""
	for user in trio:
		if user == editor:
			continue
		notify_user(
			{
				"owner": editor,
				"assigned_to": user,
				"notification_type": "Mention",
				"message": _("Deal {0} status changed to {1}").format(doc.name, doc.status),
				"notification_text": notification_text,
				"reference_doctype": "CRM Deal",
				"reference_docname": doc.name,
				"redirect_to_doctype": "CRM Deal",
				"redirect_to_docname": doc.name,
			}
		)
		send_status_change_email(doc, user, owner_name)


def send_status_change_email(doc, recipient_user, changed_by):
	"""Email a deal stakeholder that its status changed, so the update isn't missed
	when they're not actively in the CRM."""
	recipient = frappe.db.get_value("User", recipient_user, "email") or recipient_user
	if not recipient or recipient_user == frappe.session.user:
		return

	deal_url = frappe.utils.get_url(f"/crm/deals/{doc.name}")
	changed_by = frappe.utils.escape_html(changed_by)
	status = frappe.utils.escape_html(doc.status or "")

	content = f"""
	<div style="background:#f4f5f6;padding:24px 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
		<table role="presentation" align="center" cellpadding="0" cellspacing="0" width="520" style="max-width:520px;width:100%;background:#ffffff;border-radius:12px;border:1px solid #e8eaed;">
			<tr><td style="padding:28px 28px 0 28px;">
				<div style="display:inline-block;font-size:12px;font-weight:600;color:#2490ef;background:#eef6ff;border-radius:20px;padding:5px 12px;">{_('Status Update')}</div>
				<h1 style="font-size:20px;line-height:1.35;color:#1f272e;margin:16px 0 6px 0;">{_('A deal you are involved in changed status')}</h1>
				<p style="font-size:14px;color:#6b7280;margin:0;">{_('{0} updated the status of this deal.').format(changed_by)}</p>
			</td></tr>
			<tr><td style="padding:20px 28px 0 28px;">
				<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e8eaed;border-radius:8px;">
					<tr><td style="padding:14px 16px;border-bottom:1px solid #e8eaed;">
						<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#8d96a5;margin-bottom:4px;">{_('Deal')}</div>
						<div style="font-size:15px;font-weight:600;color:#1f272e;">{frappe.utils.escape_html(doc.name)}</div>
					</td></tr>
					<tr><td style="padding:14px 16px;">
						<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#8d96a5;margin-bottom:4px;">{_('New Status')}</div>
						<div style="font-size:15px;font-weight:600;color:#1f272e;">{status}</div>
					</td></tr>
				</table>
			</td></tr>
			<tr><td style="padding:24px 28px 28px 28px;">
				<a href="{deal_url}" style="display:inline-block;background:#1f272e;color:#ffffff;text-decoration:none;font-size:14px;font-weight:500;padding:11px 22px;border-radius:8px;">{_('Open the Deal')} &rarr;</a>
			</td></tr>
		</table>
		<p style="text-align:center;font-size:12px;color:#9aa4b2;margin:18px 0 0 0;">{_('Sent from your CRM')}</p>
	</div>
	"""

	frappe.sendmail(
		recipients=[recipient],
		subject=_("Deal {0} status changed to {1}").format(doc.name, doc.status),
		content=content,
		reference_doctype="CRM Deal",
		reference_name=doc.name,
	)


def notify_sales_manager_on_approval(doc, method=None):
	"""When a deal is newly sent for sales-manager approval, resolve the territory's
	sales manager (Territory Manager) and assign + notify them."""
	if not (doc.sales_manager_approval_required and not doc.sales_manager_approved):
		return
	if not doc.has_value_changed("sales_manager_approval_required"):
		return

	manager = get_territory_sales_manager(doc.territory)

	assign_to_user(
		"CRM Deal",
		doc.name,
		manager,
		_("Sales manager approval requested for this deal"),
	)

	owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ owner }</span>
			<span>{ _('requested your approval on this deal') }</span>
		</div>
	"""
	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": manager,
			"notification_type": "Assignment",
			"message": _("Approval requested for deal {0}").format(doc.name),
			"notification_text": notification_text,
			"reference_doctype": "CRM Deal",
			"reference_docname": doc.name,
			"redirect_to_doctype": "CRM Deal",
			"redirect_to_docname": doc.name,
		}
	)

	send_approval_request_email(doc, manager, owner or frappe.session.user)


def send_approval_request_email(doc, manager_user, requested_by):
	"""Email the sales manager that their approval is required on a deal (e.g. after a
	partially successful trial), so the request isn't missed when they're not in the CRM."""
	recipient = frappe.db.get_value("User", manager_user, "email") or manager_user
	if not recipient or manager_user == frappe.session.user:
		return

	deal_url = frappe.utils.get_url(f"/crm/deals/{doc.name}")
	requested_by = frappe.utils.escape_html(requested_by)

	content = f"""
	<div style="background:#f4f5f6;padding:24px 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
		<table role="presentation" align="center" cellpadding="0" cellspacing="0" width="520" style="max-width:520px;width:100%;background:#ffffff;border-radius:12px;border:1px solid #e8eaed;">
			<tr><td style="padding:28px 28px 0 28px;">
				<div style="display:inline-block;font-size:12px;font-weight:600;color:#b54708;background:#fef0c7;border-radius:20px;padding:5px 12px;">{_('Approval Required')}</div>
				<h1 style="font-size:20px;line-height:1.35;color:#1f272e;margin:16px 0 6px 0;">{_('Your approval is required on a deal')}</h1>
				<p style="font-size:14px;color:#6b7280;margin:0;">{_('{0} has requested your approval to proceed with this deal.').format(requested_by)}</p>
			</td></tr>
			<tr><td style="padding:20px 28px 0 28px;">
				<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e8eaed;border-radius:8px;">
					<tr><td style="padding:14px 16px;">
						<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#8d96a5;margin-bottom:4px;">{_('Deal')}</div>
						<div style="font-size:15px;font-weight:600;color:#1f272e;">{frappe.utils.escape_html(doc.name)}</div>
					</td></tr>
				</table>
			</td></tr>
			<tr><td style="padding:24px 28px 28px 28px;">
				<a href="{deal_url}" style="display:inline-block;background:#1f272e;color:#ffffff;text-decoration:none;font-size:14px;font-weight:500;padding:11px 22px;border-radius:8px;">{_('Review &amp; Approve')} &rarr;</a>
			</td></tr>
		</table>
		<p style="text-align:center;font-size:12px;color:#9aa4b2;margin:18px 0 0 0;">{_('Sent from your CRM')}</p>
	</div>
	"""

	frappe.sendmail(
		recipients=[recipient],
		subject=_("Approval required for deal {0}").format(doc.name),
		content=content,
		reference_doctype="CRM Deal",
		reference_name=doc.name,
	)
