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
def get_tech_teams(territory=None, product_category=None):
	"""Tech Team options for selection — value is the record name, label is the
	member's full name. Optionally scoped to a deal's territory and product
	category."""
	filters = {"active": 1}
	if territory:
		filters["territory"] = territory
	if product_category:
		filters["product_category"] = product_category
	rows = frappe.get_all(
		"CRM Tech Team",
		filters=filters,
		fields=["name", "product_category", "team_member"],
		order_by="product_category asc",
	)
	options = []
	for r in rows:
		enabled, full_name = frappe.db.get_value(
			"User", r.team_member, ["enabled", "full_name"]
		) or (0, None)
		# auto-skip entries whose linked user has been disabled — the User
		# record is the live source of truth, so no sync hook is needed.
		if not enabled:
			continue
		options.append(
			{
				"value": r.name,
				"label": full_name or r.team_member,
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


def _render_deal_email(badge, heading, subtext, rows_html, deal_url, cta_label):
	"""Shared branded shell for the tech-response stakeholder emails."""
	return f"""
	<div style="background:#f4f5f6;padding:24px 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
		<table role="presentation" align="center" cellpadding="0" cellspacing="0" width="520" style="max-width:520px;width:100%;background:#ffffff;border-radius:12px;border:1px solid #e8eaed;">
			<tr><td style="padding:28px 28px 0 28px;">
				<div style="display:inline-block;font-size:12px;font-weight:600;color:#2490ef;background:#eef6ff;border-radius:20px;padding:5px 12px;">{badge}</div>
				<h1 style="font-size:20px;line-height:1.35;color:#1f272e;margin:16px 0 6px 0;">{heading}</h1>
				<p style="font-size:14px;color:#6b7280;margin:0;">{subtext}</p>
			</td></tr>
			<tr><td style="padding:20px 28px 0 28px;">
				<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e8eaed;border-radius:8px;">{rows_html}</table>
			</td></tr>
			<tr><td style="padding:24px 28px 28px 28px;">
				<a href="{deal_url}" style="display:inline-block;background:#1f272e;color:#ffffff;text-decoration:none;font-size:14px;font-weight:500;padding:11px 22px;border-radius:8px;">{cta_label} &rarr;</a>
			</td></tr>
		</table>
		<p style="text-align:center;font-size:12px;color:#9aa4b2;margin:18px 0 0 0;">{_('Sent from your CRM')}</p>
	</div>
	"""


def _email_row(label, value, border=True):
	edge = "border-bottom:1px solid #e8eaed;" if border else ""
	return f"""
		<tr><td style="padding:14px 16px;{edge}">
			<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#8d96a5;margin-bottom:4px;">{label}</div>
			<div style="font-size:15px;color:#1f272e;">{value}</div>
		</td></tr>
	"""


def _log_info_round(doc, action_label, text):
	"""Keep the Q&A rounds readable on the deal timeline. The fields only ever hold the
	latest round, so every question and every answer is also posted as a comment."""
	who = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user
	body = frappe.utils.escape_html(text).replace("\n", "<br>")
	doc.add_comment(
		"Comment",
		f"<b>{frappe.utils.escape_html(who)}</b> {action_label}:<br>{body}",
	)


@frappe.whitelist()
def request_more_info(deal: str, questions: str):
	"""Tech team asks the salesperson for more info before recommending a product.
	The questions are saved on the deal and emailed to the salesperson; the deal parks in
	the Request for New Info stage with `sent_back_by_tech_team` set, so the waiting-time clock
	pauses on Tech and the deal leaves the technical pending queue until the salesperson
	answers the questions inside the Qualified stage form."""
	if not questions or not questions.strip():
		frappe.throw(_("Please enter the questions for the salesperson."))

	doc = frappe.get_doc("CRM Deal", deal)
	doc.info_questions = questions
	# The previous round's answer belongs to the previous question — start clean.
	doc.info_answers = None
	doc.technical_response = "Request More Info"
	doc.sent_back_by_tech_team = 1
	doc.status = "Request for New Info"
	doc.save(ignore_permissions=True)

	_log_info_round(doc, _("asked the salesperson"), questions)

	from crm.api.sales_manager import _deal_sales_person_user

	sales_user = _deal_sales_person_user(doc)
	if not sales_user:
		return None

	asked_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(asked_by) }</span>
			<span>{ _('has questions before recommending a product on this deal') }</span>
		</div>
	"""
	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": sales_user,
			"notification_type": "Mention",
			"message": _("Tech team requested more info on deal {0}").format(deal),
			"notification_text": notification_text,
			"reference_doctype": "CRM Deal",
			"reference_docname": deal,
			"redirect_to_doctype": "CRM Deal",
			"redirect_to_docname": deal,
		}
	)

	recipient = frappe.db.get_value("User", sales_user, "email") or sales_user
	if recipient and sales_user != frappe.session.user:
		rows = _email_row(_("Deal"), frappe.utils.escape_html(deal)) + _email_row(
			_("Questions"),
			frappe.utils.escape_html(questions).replace("\n", "<br>"),
			border=False,
		)
		frappe.sendmail(
			recipients=[recipient],
			subject=_("Tech team needs more info on deal {0}").format(deal),
			content=_render_deal_email(
				_("More Info Requested"),
				_("The tech team has questions for you"),
				_("{0} needs a few details before recommending a product for this deal.").format(
					frappe.utils.escape_html(asked_by)
				),
				rows,
				frappe.utils.get_url(f"/crm/deals/{deal}"),
				_("Open the Deal"),
			),
			reference_doctype="CRM Deal",
			reference_name=deal,
		)

	return sales_user


# The Qualified stage form's own fields. The answer round saves the whole form
# server-side, so only these may come along for the ride.
QUALIFICATION_FIELDS = {
	"opportunity_type",
	"decision_maker_involved",
	"decision_timeline",
	"current_monthly_volume",
	"expected_monthly_volume",
	"expected_monthly_volume_uom",
	"deal_value",
	"current_monthly_spend",
	"expected_monthly_revenue",
	"business_impact",
	"business_priority",
	"impact_notes",
	"forecast_category",
	"trial_required",
	"assign_to_tech_team",
	"technical_person",
	"assigned_tech_member",
	"evaluation_start",
	"assignment_notes",
	"dc_performance_metal_loss",
	"dc_performance_colour",
	"dc_price_competitive",
	"dc_delivery_lead_time",
}


@frappe.whitelist()
def answer_info_request(deal: str, answer: str, values: dict | str | None = None):
	"""Salesperson answers the tech team's questions from the Qualified stage form.

	The deal waits in the Request for New Info stage, but the answer is collected in the
	Qualified stage form rather than in a stage form of its own — the header CTA on that
	stage reads "Continue Trial" and reopens this form.

	The whole round is saved here rather than by the browser: the answer, the stage
	form's own fields and the move back to Tech Assignment land in one server-side save,
	so a deal the tech team touched while the form was open can't fail on a timestamp
	mismatch. The tech member is then notified and emailed the answer.
	"""
	if not answer or not answer.strip():
		frappe.throw(_("Please enter your answer for the technical team."))

	doc = frappe.get_doc("CRM Deal", deal)
	if not doc.sent_back_by_tech_team:
		frappe.throw(_("This deal is not waiting on an answer from Sales."))

	if values:
		if isinstance(values, str):
			values = frappe.parse_json(values)
		doc.update({k: v for k, v in values.items() if k in QUALIFICATION_FIELDS})

	doc.info_answers = answer
	doc.sent_back_by_tech_team = 0
	doc.status = "Tech Assignment"
	doc.save(ignore_permissions=True)

	_log_info_round(doc, _("answered the technical team"), answer)

	tech_user = doc.assigned_tech_member
	if not tech_user and doc.technical_person:
		tech_user = frappe.db.get_value("CRM Tech Team", doc.technical_person, "team_member")
	if not tech_user:
		return None

	answered_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(answered_by) }</span>
			<span>{ _('answered your questions on this deal') }</span>
		</div>
	"""
	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": tech_user,
			"notification_type": "Mention",
			"message": _("Salesperson answered your questions on deal {0}").format(deal),
			"notification_text": notification_text,
			"reference_doctype": "CRM Deal",
			"reference_docname": deal,
			"redirect_to_doctype": "CRM Deal",
			"redirect_to_docname": deal,
		}
	)

	recipient = frappe.db.get_value("User", tech_user, "email") or tech_user
	if recipient and tech_user != frappe.session.user:
		rows = _email_row(_("Deal"), frappe.utils.escape_html(deal))
		if doc.info_questions:
			rows += _email_row(
				_("You asked"),
				frappe.utils.escape_html(doc.info_questions).replace("\n", "<br>"),
			)
		rows += _email_row(
			_("Answer"),
			frappe.utils.escape_html(answer).replace("\n", "<br>"),
			border=False,
		)
		frappe.sendmail(
			recipients=[recipient],
			subject=_("Salesperson answered your questions on deal {0}").format(deal),
			content=_render_deal_email(
				_("Answer Received"),
				_("The salesperson has answered you"),
				_("{0} replied with the details you asked for. The deal is back in Tech Assignment.").format(
					frappe.utils.escape_html(answered_by)
				),
				rows,
				frappe.utils.get_url(f"/crm/deals/{deal}"),
				_("Open the Deal"),
			),
			reference_doctype="CRM Deal",
			reference_name=deal,
		)

	return tech_user


@frappe.whitelist()
def flag_not_suitable(deal: str, reason: str, notes: str | None = None):
	"""Tech team marks the recommendation Not Suitable. Flags the deal for the sales
	manager (the assigned salesperson's parent in the Sales Person tree) and emails
	them. The deal stays in the Tech Assignment stage until the manager reviews it."""
	if not reason:
		frappe.throw(_("Please select a reason."))

	doc = frappe.get_doc("CRM Deal", deal)
	doc.not_suitable = 1
	doc.technical_response = "Not Suitable"
	doc.not_suitable_reason = reason
	doc.not_suitable_notes = notes or ""
	doc.save(ignore_permissions=True)

	from crm.api.sales_manager import (
		_deal_sales_person_user,
		_user_from_sales_person,
		sales_person_from_user,
	)

	manager_user = None
	sales_user = _deal_sales_person_user(doc)
	if sales_user:
		sales_person = sales_person_from_user(sales_user)
		if sales_person:
			parent = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")
			manager_user = _user_from_sales_person(parent)

	if not manager_user:
		return None

	flagged_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(flagged_by) }</span>
			<span>{ _('marked this deal Not Suitable — needs your review') }</span>
		</div>
	"""
	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": manager_user,
			"notification_type": "Mention",
			"message": _("Deal {0} marked Not Suitable — review required").format(deal),
			"notification_text": notification_text,
			"reference_doctype": "CRM Deal",
			"reference_docname": deal,
			"redirect_to_doctype": "CRM Deal",
			"redirect_to_docname": deal,
		}
	)

	recipient = frappe.db.get_value("User", manager_user, "email") or manager_user
	if recipient and manager_user != frappe.session.user:
		rows = _email_row(_("Deal"), frappe.utils.escape_html(deal))
		rows += _email_row(_("Reason"), frappe.utils.escape_html(reason), border=bool(notes))
		if notes:
			rows += _email_row(
				_("Comments"), frappe.utils.escape_html(notes).replace("\n", "<br>"), border=False
			)
		frappe.sendmail(
			recipients=[recipient],
			subject=_("Deal {0} marked Not Suitable — your review needed").format(deal),
			content=_render_deal_email(
				_("Escalation"),
				_("A deal needs your review"),
				_("{0} marked the technical recommendation Not Suitable and escalated it to you.").format(
					frappe.utils.escape_html(flagged_by)
				),
				rows,
				frappe.utils.get_url(f"/crm/deals/{deal}"),
				_("Review the Deal"),
			),
			reference_doctype="CRM Deal",
			reference_name=deal,
		)

	return manager_user


@frappe.whitelist()
def resolve_escalation(deal: str, action: str, notes: str | None = None):
	"""Sales manager resolves a Not-Suitable escalation. 'redirect' clears the flag and
	sends the deal back to Req. Discussion for re-qualification; 'lost' closes it."""
	doc = frappe.get_doc("CRM Deal", deal)
	if not doc.not_suitable:
		frappe.throw(_("This deal is not under escalation review."))

	if action == "redirect":
		doc.not_suitable = 0
		doc.status = "Req. Discussion"
	elif action == "lost":
		doc.not_suitable = 0
		doc.status = "Lost"
	else:
		frappe.throw(_("Unknown escalation action: {0}").format(action))

	if notes:
		doc.add_comment("Comment", frappe.utils.escape_html(notes))
	doc.save(ignore_permissions=True)

	return doc.status


def _npd_stakeholders(doc):
	"""The salesperson on the deal and their immediate manager — the two people an NPD
	proposal is handed to. Either may be missing (no sales person set, or no parent in
	the Sales Person tree); callers simply skip whoever isn't resolvable."""
	from crm.api.sales_manager import (
		_deal_sales_person_user,
		_user_from_sales_person,
		sales_person_from_user,
	)

	sales_user = _deal_sales_person_user(doc)
	manager_user = None
	if sales_user:
		sales_person = sales_person_from_user(sales_user)
		if sales_person:
			parent = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")
			manager_user = _user_from_sales_person(parent)

	# dict.fromkeys keeps order and drops the duplicate when the salesperson is their
	# own manager.
	return list(dict.fromkeys(u for u in (sales_user, manager_user) if u))


def _npd_figures(doc):
	"""The lab figures as email rows. Every field is optional, so only what the tech
	team actually filled in is shown."""
	rows = ""
	if doc.npd_composition:
		rows += _email_row(_("Composition (%)"), doc.npd_composition)
	if doc.npd_hardness:
		rows += _email_row(_("Hardness"), doc.npd_hardness)
	if doc.npd_xrf:
		rows += _email_row(_("XRF (%)"), doc.npd_xrf)
	if doc.npd_icp:
		rows += _email_row(_("ICP"), doc.npd_icp)
	return rows


@frappe.whitelist()
def request_npd(
	deal: str,
	composition: float | None = None,
	hardness: int | None = None,
	xrf: float | None = None,
	icp: int | None = None,
):
	"""Tech team proposes developing a new alloy instead of recommending an existing item.

	Every figure is optional — the proposal can be sent with as much or as little lab data
	as the tech team has. The deal moves to the New Product Development stage and is
	assigned to both the salesperson and their manager, but only the manager can answer it.
	"""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.technical_response = "New Product Development"
	doc.npd_composition = composition or 0
	doc.npd_hardness = hardness or 0
	# XRF and ICP only apply alongside a composition — mirrors the form hiding them.
	doc.npd_xrf = (xrf or 0) if composition else 0
	doc.npd_icp = (icp or 0) if composition else 0
	# A resubmission starts a clean round: the previous answer belonged to the previous
	# proposal.
	doc.npd_decision = None
	doc.npd_remarks = None
	doc.npd_declined = 0
	doc.npd_pending = 1
	doc.status = "New Product Development"
	doc.save(ignore_permissions=True)

	summary = ", ".join(
		f"{label}: {value}"
		for label, value in (
			(_("Composition (%)"), doc.npd_composition),
			(_("Hardness"), doc.npd_hardness),
			(_("XRF (%)"), doc.npd_xrf),
			(_("ICP"), doc.npd_icp),
		)
		if value
	)
	_log_info_round(doc, _("proposed a new product development"), summary or _("No figures recorded"))

	stakeholders = _npd_stakeholders(doc)
	if not stakeholders:
		return None

	proposed_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(proposed_by) }</span>
			<span>{ _('proposed a new product development on this deal') }</span>
		</div>
	"""
	rows = _email_row(_("Deal"), frappe.utils.escape_html(deal)) + _npd_figures(doc)

	for user in stakeholders:
		assign_to_user(
			"CRM Deal",
			deal,
			user,
			_("New product development proposed — awaiting the Sales Manager's decision"),
		)
		notify_user(
			{
				"owner": frappe.session.user,
				"assigned_to": user,
				"notification_type": "Mention",
				"message": _("New product development proposed on deal {0}").format(deal),
				"notification_text": notification_text,
				"reference_doctype": "CRM Deal",
				"reference_docname": deal,
				"redirect_to_doctype": "CRM Deal",
				"redirect_to_docname": deal,
			}
		)

		recipient = frappe.db.get_value("User", user, "email") or user
		if not recipient or user == frappe.session.user:
			continue
		frappe.sendmail(
			recipients=[recipient],
			subject=_("New product development proposed on deal {0}").format(deal),
			content=_render_deal_email(
				_("New Product Development"),
				_("A new product has been proposed"),
				_("{0} could not match an existing product and proposed developing a new one.").format(
					frappe.utils.escape_html(proposed_by)
				),
				rows,
				frappe.utils.get_url(f"/crm/deals/{deal}"),
				_("Open the Deal"),
			),
			reference_doctype="CRM Deal",
			reference_name=deal,
		)

	return stakeholders


@frappe.whitelist()
def respond_npd(deal: str, decision: str, remarks: str | None = None):
	"""Sales Manager answers an NPD proposal.

	'Yes' sends the deal on to Tech Evaluation. 'No' closes the deal — it moves to the
	terminal `Closed` stage with the manager's remarks on record. Closed rather than
	Lost: the deal never reached a commercial decision, so counting it as a lost deal
	would overstate losses.
	"""
	if decision not in ("Yes", "No"):
		frappe.throw(_("Please select Yes or No."))

	doc = frappe.get_doc("CRM Deal", deal)
	if not doc.npd_pending:
		frappe.throw(_("This deal is not awaiting a new product development decision."))

	doc.npd_decision = decision
	doc.npd_remarks = remarks or ""
	doc.npd_pending = 0
	if decision == "Yes":
		doc.status = "Demo/Making"
	else:
		doc.npd_declined = 1
		doc.status = "Closed"
	doc.save(ignore_permissions=True)

	_log_info_round(
		doc,
		_("approved the new product development")
		if decision == "Yes"
		else _("declined the new product development"),
		remarks or _("No remarks"),
	)

	tech_user = doc.assigned_tech_member
	if not tech_user and doc.technical_person:
		tech_user = frappe.db.get_value("CRM Tech Team", doc.technical_person, "team_member")
	if not tech_user:
		return doc.status

	answered_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user
	verb = _("approved") if decision == "Yes" else _("declined")
	notification_text = f"""
		<div class="mb-2 leading-5 text-ink-gray-5">
			<span class="font-medium text-ink-gray-9">{ frappe.utils.escape_html(answered_by) }</span>
			<span>{ _('{0} your new product development proposal').format(verb) }</span>
		</div>
	"""
	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": tech_user,
			"notification_type": "Mention",
			"message": _("New product development {0} on deal {1}").format(verb, deal),
			"notification_text": notification_text,
			"reference_doctype": "CRM Deal",
			"reference_docname": deal,
			"redirect_to_doctype": "CRM Deal",
			"redirect_to_docname": deal,
		}
	)

	recipient = frappe.db.get_value("User", tech_user, "email") or tech_user
	if recipient and tech_user != frappe.session.user:
		rows = _email_row(_("Deal"), frappe.utils.escape_html(deal))
		rows += _email_row(_("Decision"), decision, border=bool(remarks))
		if remarks:
			rows += _email_row(
				_("Remarks"), frappe.utils.escape_html(remarks).replace("\n", "<br>"), border=False
			)
		frappe.sendmail(
			recipients=[recipient],
			subject=_("New product development {0} on deal {1}").format(verb, deal),
			content=_render_deal_email(
				_("New Product Development"),
				_("Your proposal was {0}").format(verb),
				_("{0} reviewed the new product you proposed for this deal.").format(
					frappe.utils.escape_html(answered_by)
				),
				rows,
				frappe.utils.get_url(f"/crm/deals/{deal}"),
				_("Open the Deal"),
			),
			reference_doctype="CRM Deal",
			reference_name=deal,
		)

	return doc.status
