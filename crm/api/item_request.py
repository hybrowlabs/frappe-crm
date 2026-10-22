import frappe
from frappe import _
from frappe.utils import escape_html, get_url

from crm.api.quotation import _check_branch_currency, _check_customer
from crm.fcrm.doctype.crm_custom_settings.crm_custom_settings import get_email_recipients

# CRM "Item Request" page: a sales person asks for stock items to be added to a
# customer's Item Discounts (Customer -> custom_item_discounts) so they can be
# quoted. The request is only an email to CRM Custom Settings -> Email
# Recipients; nothing is changed on the customer.


def _quotable_item_codes(customer, branch):
	"""Items the customer can already be quoted in this branch: Item Discounts
	rows for the branch or with the branch left blank (same rule as quotations)."""
	rows = frappe.get_all(
		"Customer Item Discount",
		filters={"parenttype": "Customer", "parent": customer, "parentfield": "custom_item_discounts"},
		fields=["item_code", "branch"],
	)
	return {row.item_code for row in rows if row.item_code and (not row.branch or row.branch == branch)}


def _requestable_items(customer, branch, currency):
	"""Enabled stock items the customer cannot be quoted yet. Service
	(non-inventory) items are left out."""
	_check_customer(customer)
	_check_branch_currency(customer, branch, currency)
	quotable = _quotable_item_codes(customer, branch)
	items = frappe.get_all(
		"Item",
		filters={"disabled": 0, "is_stock_item": 1, "is_sales_item": 1, "has_variants": 0},
		fields=["name as item_code", "item_name", "item_group", "stock_uom"],
		order_by="name asc",
	)
	return [item for item in items if item.item_code not in quotable]


@frappe.whitelist()
def get_request_items(customer: str, branch: str, currency: str):
	"""Items for the page's list."""
	return _requestable_items(customer, branch, currency)


@frappe.whitelist(methods=["POST"])
def send_item_request(customer: str, branch: str, currency: str, items):
	"""Email the selected items to the Email Recipients in CRM Custom Settings."""
	codes = list(dict.fromkeys(frappe.parse_json(items) or []))
	if not codes:
		frappe.throw(_("Select at least one item."))

	recipients = get_email_recipients()
	if not recipients:
		frappe.throw(
			_("No Email Recipients are set in CRM Custom Settings. Ask your admin to add them."),
			title=_("No Recipients"),
		)

	available = {item.item_code: item for item in _requestable_items(customer, branch, currency)}
	missing = [code for code in codes if code not in available]
	if missing:
		frappe.throw(
			_("These items cannot be requested for this customer: {0}").format(", ".join(missing)),
			title=_("Invalid Items"),
		)

	customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
	requested_by = frappe.utils.get_fullname(frappe.session.user)
	frappe.sendmail(
		recipients=recipients,
		subject=_("Item request for {0}").format(customer_name),
		content=_request_email(
			requested_by, customer, customer_name, branch, currency, [available[c] for c in codes]
		),
		reference_doctype="Customer",
		reference_name=customer,
	)
	return {"recipients": len(recipients)}


def _request_email(requested_by, customer, customer_name, branch, currency, items):
	"""HTML body: who asked, the branch / currency / customer, and the item table.

	Laid out with tables only (no margins, divs or <p> spacing), because Gmail,
	Outlook and phone mail apps drop or change those. Tables are 100% wide up to
	600px so they fit a phone screen."""
	font = "font-family:Arial,Helvetica,sans-serif;"
	cell = f"{font}padding:8px 12px;border-bottom:1px solid #e8eaed;font-size:14px;line-height:20px;color:#1f272e;"
	head = f"{font}padding:8px 12px;border-bottom:1px solid #e8eaed;font-size:12px;line-height:16px;font-weight:bold;color:#6b7280;text-align:left;"
	details = "".join(
		f"""<tr><td width="140" style="{cell}color:#6b7280;">{label}</td>
			<td style="{cell}font-weight:bold;">{escape_html(value)}</td></tr>"""
		for label, value in (
			(_("Requested By"), requested_by),
			(_("Branch"), branch),
			(_("Currency (Billing)"), currency),
			(_("Customer"), f"{customer_name} ({customer})"),
		)
	)
	rows = "".join(
		f"""<tr><td width="24" style="{cell}color:#6b7280;">{i}</td>
			<td style="{cell}font-weight:bold;">{escape_html(item.item_code)}</td>
			<td style="{cell}">{escape_html(item.item_name or "")}</td>
			<td style="{cell}">{escape_html(item.item_group or "")}</td></tr>"""
		for i, item in enumerate(items, start=1)
	)
	customer_url = get_url(f"/app/customer/{customer}")
	box = 'width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #e8eaed;border-collapse:collapse;"'
	# An empty row of fixed height: the one gap every mail client keeps.
	gap = '<tr><td height="{0}" style="height:{0}px;font-size:0;line-height:0;">&nbsp;</td></tr>'
	return f"""
	<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">
		<tr><td style="{font}font-size:14px;line-height:20px;color:#1f272e;">
			{_("Please add these items to the customer's Item Discounts so they can be quoted.")}
		</td></tr>
		{gap.format(16)}
		<tr><td><table role="presentation" {box}>{details}</table></td></tr>
		{gap.format(20)}
		<tr><td><table {box}>
			<tr bgcolor="#f4f5f6"><th align="left" style="{head}">#</th>
				<th align="left" style="{head}">{_("Item Code")}</th>
				<th align="left" style="{head}">{_("Item Name")}</th>
				<th align="left" style="{head}">{_("Item Group")}</th></tr>
			{rows}
		</table></td></tr>
		{gap.format(24)}
		<tr><td>
			<!-- The colour sits on the cell, so Outlook (which ignores padding on links) still draws the button. -->
			<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
				<td bgcolor="#1f272e" style="border-radius:8px;">
					<a href="{customer_url}" target="_blank" style="{font}display:inline-block;padding:10px 20px;font-size:14px;line-height:20px;color:#ffffff;text-decoration:none;border-radius:8px;">{_("Open the Customer")} &rarr;</a>
				</td>
			</tr></table>
		</td></tr>
	</table>
	"""
