import frappe
from frappe import _
from frappe.utils import get_time, getdate, now_datetime

from crm.fcrm.doctype.crm_custom_settings.crm_custom_settings import (
	WEEKDAYS,
	get_branch_warehouse,
	get_print_format,
	is_holiday,
	is_working_day,
)

HOLIDAY_BLOCKED = "{0} cannot be created on holiday for branch {1}."
DAY_BLOCKED = "{0} for branch {1} cannot be created on {2}."
METAL_RATE_PREFIX = "Metal rate for"
METAL_RATE_RISEN = "Metal rate has risen since this quotation was made. Please revise the quotation."
TIME_BLOCKED = "{0} for branch {1} can only be created during: {2}."


def _block_outside_window(doc, fieldname, label):
	"""Refuse the document outside the window CRM Custom Settings allows for it:
	holiday, then weekday, then the branch's from/to time. Only Time Setting rows
	ticked for this document (`fieldname`) count, so a Quotation window does not
	let a Sales Order through and the other way round."""
	# A Quotation keeps its branch in custom_branch; a Sales Order in branch.
	branch = doc.get("custom_branch") or doc.get("branch") or _sales_person_branch()
	if is_holiday(doc.transaction_date, branch):
		frappe.throw(_(HOLIDAY_BLOCKED).format(label, branch or _("(none)")), title=_("Holiday"))

	settings = frappe.get_cached_doc("CRM Custom Settings")
	date = getdate(doc.transaction_date)
	if not is_working_day(date, branch):
		frappe.throw(
			_(DAY_BLOCKED).format(label, branch or _("(none)"), _(WEEKDAYS[date.weekday()])),
			title=_("Day Not Allowed"),
		)

	windows = [r for r in settings.time_setting_branch_wise if r.branch == branch and r.get(fieldname)]
	if not windows:
		return

	now = now_datetime().time()
	if any(get_time(r.from_time) <= now <= get_time(r.to_time) for r in windows):
		return

	frappe.throw(
		_(TIME_BLOCKED).format(label, branch, ", ".join(f"{r.from_time} - {r.to_time}" for r in windows)),
		title=_("Outside Working Hours"),
	)


def block_holiday_creation(doc):
	"""Called by create_quotation only, not as a doc hook, so quotations raised
	from the ERPNext desk, the API or data import are not limited."""
	_block_outside_window(doc, "quotation", _("Quotation"))


def _sales_person_branch():
	"""First branch of the session user's Sales Person, when the quotation has none."""
	sales_person = _session_sales_person()
	if sales_person:
		return frappe.db.get_value(
			"Sales Person Branch",
			{"parenttype": "Sales Person", "parent": sales_person, "parentfield": "custom_branches"},
			"branch",
			order_by="idx asc",
		)

# CRM list/detail views over ERPNext's Quotation. Normal users only see the
# quotations they created; Administrator and System Managers see all of them.


def can_see_all_quotations(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def quotation_owner_filter():
	"""Extra list filter that limits Quotation to the session user's own records."""
	return {} if can_see_all_quotations() else {"owner": frappe.session.user}


# ERPNext's list colours per status (erpnext/selling/doctype/quotation/quotation_list.js).
STATUS_COLORS = {
	"Open": "orange",
	"Partially Ordered": "yellow",
	"Ordered": "green",
	"Lost": "gray",
	"Expired": "gray",
}

WORKFLOW_STYLE_COLORS = {
	"Success": "green",
	"Warning": "orange",
	"Danger": "red",
	"Primary": "blue",
	"Inverse": "black",
	"Info": "light-blue",
}


def get_active_workflow():
	"""The active Quotation workflow, if it overrides the status indicator."""
	workflow = frappe.get_all(
		"Workflow",
		filters={"document_type": "Quotation", "is_active": 1},
		fields=["name", "workflow_state_field", "override_status"],
		limit=1,
	)
	if workflow and not workflow[0].override_status:
		return workflow[0]


def get_indicator(doc, workflow=None):
	"""The status label and colour ERPNext's list shows, following
	frappe.get_indicator: workflow state, then Draft/Cancelled by docstatus,
	then the status field."""
	if workflow and doc.get(workflow.workflow_state_field):
		state = doc.get(workflow.workflow_state_field)
		style = frappe.db.get_value("Workflow State", state, "style")
		return {"label": state, "color": WORKFLOW_STYLE_COLORS.get(style, "gray")}
	if doc.get("docstatus") == 0:
		return {"label": "Draft", "color": "red"}
	if doc.get("docstatus") == 2:
		return {"label": "Cancelled", "color": "red"}
	return {"label": doc.get("status"), "color": STATUS_COLORS.get(doc.get("status"), "gray")}


def get_workflow_states(workflow):
	return frappe.get_all(
		"Workflow Document State", filters={"parent": workflow.name}, pluck="state", order_by="idx"
	)


def get_status_options(workflow=None):
	"""Statuses the CRM shows (and filters by), in ERPNext's terms."""
	options = ["Draft", *STATUS_COLORS, "Cancelled"]
	if workflow:
		options = list(dict.fromkeys([*get_workflow_states(workflow), *options]))
	return options


def status_filter(value, workflow=None):
	"""Filters matching a displayed status, the inverse of get_indicator()."""
	if workflow and value in get_workflow_states(workflow):
		return {workflow.workflow_state_field: value}
	if value == "Draft":
		return {"docstatus": 0}
	if value == "Cancelled":
		return {"docstatus": 2}
	return {"status": value, "docstatus": 1}


def translate_status_filter(filters):
	"""Rewrites an equality filter on status (quick filter or Filter button) so
	it matches the status ERPNext displays, e.g. Draft = not yet submitted."""
	value = filters.get("status")
	if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] == "=":
		value = value[1]
	if not value or not isinstance(value, str):
		return
	del filters["status"]
	filters.update(status_filter(value, get_active_workflow()))


class QuotationList:
	"""Stands in for a list controller: Quotation is ERPNext's doctype, so it
	has no CRM default_list_data of its own."""

	@staticmethod
	def default_list_data():
		columns = [
			{"label": "Quotation No", "type": "Data", "key": "name", "width": "12rem"},
			# customer_name is hidden in ERPNext, so the column is party_name and
			# the CRM list shows customer_name in it.
			{"label": "Customer", "type": "Dynamic Link", "key": "party_name", "width": "16rem"},
			{"label": "Date", "type": "Date", "key": "transaction_date", "width": "9rem"},
			{"label": "Valid Till", "type": "Date", "key": "valid_till", "width": "9rem"},
			{"label": "Amount", "type": "Currency", "key": "grand_total", "width": "10rem"},
			{"label": "Status", "type": "Select", "key": "status", "width": "11rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]
		rows = [
			"name",
			"customer_name",
			"party_name",
			"transaction_date",
			"valid_till",
			"grand_total",
			"currency",
			"status",
			"modified",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def parse_list_data(data):
		"""Adds the ERPNext status indicator to each row. docstatus and the
		workflow state are looked up here so they work with any column set."""
		names = [row.get("name") for row in data if row.get("name")]
		if not names:
			return data
		workflow = get_active_workflow()
		fields = ["name", "docstatus", "status"]
		if workflow:
			fields.append(workflow.workflow_state_field)
		docs = {
			d.name: d
			for d in frappe.get_all("Quotation", filters={"name": ["in", names]}, fields=fields)
		}
		for row in data:
			doc = docs.get(row.get("name"))
			if doc:
				row["_indicator"] = get_indicator(doc, workflow)
		return data


# Default quick filters: the list's own columns. customer_name is hidden in
# ERPNext's meta, so its label is set here rather than taken from the field.
QUICK_FILTERS = [
	("name", "Quotation No"),
	("customer_name", "Customer"),
	("status", None),
	("transaction_date", None),
	("valid_till", None),
]


def get_quick_filter_fields():
	meta = frappe.get_meta("Quotation")
	fields = []
	for fieldname, label in QUICK_FILTERS:
		if fieldname == "name":
			fields.append(frappe._dict(label=label, fieldname="name", fieldtype="Data"))
			continue
		field = meta.get_field(fieldname)
		if field:
			options = field.options
			if fieldname == "status":
				options = "\n".join(get_status_options(get_active_workflow()))
			fields.append(
				frappe._dict(
					label=label or field.label,
					fieldname=fieldname,
					fieldtype=field.fieldtype,
					options=options,
				)
			)
	return fields


def get_list_controller(doctype):
	"""get_controller(), except Quotation and Sales Order get CRM list defaults."""
	from frappe.model.document import get_controller

	if doctype == "Quotation":
		return QuotationList
	if doctype == "Sales Order":
		from crm.api.sales_order_list import SalesOrderList

		return SalesOrderList
	return get_controller(doctype)


@frappe.whitelist()
def get_quotation(name: str):
	"""Read-only view of one quotation for the CRM quotation page."""
	doc = frappe.get_doc("Quotation", name)
	doc.check_permission("read")
	if not can_see_all_quotations() and doc.owner != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return {
		"name": doc.name,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"indicator": get_indicator(doc, get_active_workflow()),
		"customer_name": doc.customer_name,
		"party_name": doc.party_name,
		"billing_address": _address_text(doc.customer_address),
		"quotation_to": doc.quotation_to,
		"transaction_date": doc.transaction_date,
		"valid_till": doc.valid_till,
		"company": doc.company,
		"branch": doc.get("custom_branch"),
		"order_type": doc.order_type,
		"payment_terms_template": doc.get("payment_terms_template"),
		"currency": doc.currency,
		"deal": doc.get("custom_deal"),
		"sale_by": doc.get("custom_sale_by"),
		"owner": doc.owner,
		"owner_name": frappe.utils.get_fullname(doc.owner),
		# Any draft or submitted Sales Order made from this quotation, with the
		# state the CRM Sales Orders list shows for it.
		"sales_orders": _sales_orders_for(name),
		"sales_order_states": _sales_order_states(name),
		"creation": doc.creation,
		"items": [
			{
				"item_code": i.item_code,
				"item_name": i.item_name,
				"description": frappe.utils.strip_html(i.description or "").strip(),
				"gst_hsn_code": i.get("gst_hsn_code") or "",
				"gst_rate": _line_gst_rate(i),
				"custom_no_of_packs": i.get("custom_no_of_packs"),
				"custom_base_qty": i.get("custom_base_qty"),
				"qty": i.qty,
				"uom": i.uom,
				"rate": i.rate,
				"amount": i.amount,
			}
			for i in doc.items
		],
		"taxes": [
			{"description": t.description, "rate": t.rate, "tax_amount": t.tax_amount}
			for t in doc.get("taxes") or []
		],
		"net_total": doc.net_total,
		"total_taxes_and_charges": doc.total_taxes_and_charges,
		"discount_amount": doc.discount_amount,
		"grand_total": doc.grand_total,
		"rounded_total": doc.rounded_total,
		# The print format this quotation's branch sets in CRM Custom Settings;
		# None means the screen prints with the doctype's own default.
		"print_format": get_print_format(doc.get("custom_branch"), "quotation_print_format"),
	}


def _address_text(name):
	"""An address as the new-quotation screen shows it: street lines, then
	city / state / pincode, country and GSTIN, one per line."""
	if not name:
		return ""
	a = frappe.db.get_value(
		"Address",
		name,
		["address_line1", "address_line2", "city", "state", "pincode", "country", "gstin"],
		as_dict=True,
	)
	if not a:
		return ""
	lines = [
		a.address_line1,
		a.address_line2,
		", ".join(filter(None, [a.city, a.state, a.pincode])),
		a.country,
		a.gstin and f"GSTIN: {a.gstin}",
	]
	return "\n".join(filter(None, lines))


def _line_gst_rate(item):
	"""GST % on a saved quotation line: IGST, or CGST + SGST within the state;
	None when the line has no Item Tax Template, as on the new-quotation screen."""
	from frappe.utils import flt

	if not item.get("item_tax_template"):
		return None
	return flt(item.get("igst_rate")) or flt(item.get("cgst_rate")) + flt(item.get("sgst_rate"))


def _is_expired(doc):
	"""Expired by status, or past Valid Till before ERPNext's nightly job marks it."""
	from frappe.utils import getdate, nowdate

	return doc.status == "Expired" or bool(doc.valid_till and getdate(doc.valid_till) < getdate(nowdate()))


def _session_sales_person():
	"""The session user's enabled Sales Person, if any."""
	from crm.api.sales_manager import sales_person_from_user

	sales_person = sales_person_from_user(frappe.session.user)
	if sales_person and frappe.db.get_value("Sales Person", sales_person, "enabled"):
		return sales_person


@frappe.whitelist()
def get_currency_symbol(currency: str):
	"""The symbol on the ERPNext Currency record (blank when none is set), so the
	quotation and sales order screens show amounts the way the Currency master does."""
	return frappe.get_cached_value("Currency", currency, "symbol") or ""


@frappe.whitelist()
def get_quotation_defaults():
	"""Sales Person for "Sale By" and its Branch & Currency rows for a new quotation."""
	sales_person = _session_sales_person()
	branches = []
	if sales_person:
		branches = frappe.get_all(
			"Sales Person Branch",
			filters={"parenttype": "Sales Person", "parent": sales_person, "parentfield": "custom_branches"},
			fields=["branch", "currency"],
			order_by="idx asc",
		)
	# The company ERPNext puts on a new Quotation (the CRM sets none), for the
	# company address / contact pickers.
	company = frappe.new_doc("Quotation").company
	return {"sales_person": sales_person, "branches": branches, "company": company}


@frappe.whitelist()
def get_quotation_window(branch: str):
	"""The branch's Quotation time windows and whether now is inside one, so the
	screen can say so before the user fills the form. Same rows the before_insert
	gate uses; no rows means no time limit."""
	settings = frappe.get_cached_doc("CRM Custom Settings")
	windows = [r for r in settings.time_setting_branch_wise if r.branch == branch and r.quotation]
	if not windows:
		return {"open": True, "windows": []}
	now = now_datetime().time()
	return {
		"open": any(get_time(r.from_time) <= now <= get_time(r.to_time) for r in windows),
		"windows": [f"{r.from_time} - {r.to_time}" for r in windows],
	}


# Every line of a CRM quotation and its sales order takes the warehouse set for
# the salesperson's branch in CRM Warehouse Settings; the Item's own warehouse
# is not used.
NO_WAREHOUSE = "No warehouse is set for branch {0} in CRM Warehouse Settings."


def _check_customer(customer):
	"""Only customers with the user's Sales Person on their Sales Team;
	Administrator and System Managers may use any customer."""
	if can_see_all_quotations():
		return
	sales_person = _session_sales_person()
	if not sales_person or not frappe.db.exists(
		"Sales Team", {"parenttype": "Customer", "parent": customer, "sales_person": sales_person}
	):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _is_gst_free_customer(customer):
	"""SEZ and Overseas customers are charged no GST; India Compliance refuses a
	quotation that carries GST for them."""
	return frappe.db.get_value("Customer", customer, "gst_category") in ("SEZ", "Overseas")


def _entitled_items(customer, branch):
	"""{item_code: {item_code, stock_uom, slabs}} for the rows on the customer's
	Item Discounts table for this branch or with the branch left blank. Same
	rule as the Customer Portal's item list."""
	rows = frappe.get_all(
		"Customer Item Discount",
		filters={"parenttype": "Customer", "parent": customer, "parentfield": "custom_item_discounts"},
		fields=["item_code", "branch", "from_qty", "to_qty", "item_discount"],
		order_by="item_code asc, from_qty asc, idx asc",
	)
	rows = [row for row in rows if row.item_code and (not row.branch or row.branch == branch)]
	codes = list(dict.fromkeys(row.item_code for row in rows))
	if not codes:
		return {}
	uoms = dict(
		frappe.get_all(
			"Item",
			filters={"name": ["in", codes], "disabled": 0, "is_sales_item": 1},
			fields=["name", "stock_uom"],
			as_list=True,
		)
	)
	return {
		code: {
			"item_code": code,
			"stock_uom": uoms[code],
			"slabs": [
				{"from_qty": row.from_qty, "to_qty": row.to_qty, "discount": row.item_discount}
				for row in rows
				if row.item_code == code
			],
		}
		for code in codes
		if code in uoms
	}


@frappe.whitelist()
def get_customer_items(customer: str, branch: str | None = None):
	"""The items this customer can be quoted in this branch, with their
	discount slabs (qty ranges) so the screen can check the qty first."""
	_check_customer(customer)
	return list(_entitled_items(customer, branch).values())


@frappe.whitelist()
def get_item_details(customer: str, item_code: str):
	"""Item fields the new-quotation screen shows read-only, plus the pack rule it
	uses for Qty. GST rate is the one the quotation will get on save (same Item Tax
	Template as apply_quotation_taxes picks)."""
	from frappe.utils import strip_html
	from papl_business_logic.papl_business_logic.api.quotation_tax import (
		_template_rate,
		item_tax_template,
		resolve_tax_category,
	)

	_check_customer(customer)
	item = frappe.get_cached_doc("Item", item_code)
	company = frappe.new_doc("Quotation").company
	tax_category = None if _is_gst_free_customer(customer) else resolve_tax_category(customer)
	template = (
		item_tax_template(item_code, company, tax_category, frappe.utils.nowdate()) if tax_category else None
	)
	return {
		"item_name": item.item_name,
		"stock_uom": item.stock_uom,
		"description": strip_html(item.description or "").strip(),
		"gst_hsn_code": item.get("gst_hsn_code") or "",
		"gst_rate": _template_rate(template) if template else None,
		"custom_sell_only_as_a_multiple_of_base_qty": item.get("custom_sell_only_as_a_multiple_of_base_qty"),
		"custom_base_qty": item.get("custom_base_qty"),
	}


@frappe.whitelist()
def get_customer_addresses(customer: str):
	"""The customer's own billing and shipping addresses, so the screen can pick
	the only one by itself and ask when there are several."""
	_check_customer(customer)
	names = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Address",
			"link_doctype": "Customer",
			"link_name": customer,
		},
		pluck="parent",
	)
	if not names:
		return {"billing": [], "shipping": []}
	rows = frappe.get_all(
		"Address",
		filters={"name": ["in", names], "disabled": 0},
		fields=["name", "address_type", "is_primary_address", "is_shipping_address"],
		order_by="is_primary_address desc, name asc",
	)
	billing = [r.name for r in rows if r.address_type == "Billing"]
	shipping = [r.name for r in rows if r.address_type == "Shipping" or r.is_shipping_address]
	# A customer that types none of them still has to be quotable: fall back to
	# every address it has, the same list the picker shows.
	names = [r.name for r in rows]
	return {"billing": billing or names, "shipping": shipping or names}


# Pricing-core status -> (call succeeded, rate set). Same map as the Customer
# Portal: an item with no Sales BOM rate is
# not an error, it just has no number to show.
PRICE_STATUS = {
	"success": (True, True),
	"non_stock": (True, False),
	"inactive_bom": (True, False),
	"raw_material": (True, False),
}


def _check_branch_currency(customer, branch, currency):
	"""The Work Location / Currency pair must be a row on the user's Sales
	Person, and the customer must have that Work Location in its Branch Details
	and that Currency as its Billing Currency."""
	sales_person = _session_sales_person()
	if not (
		branch
		and currency
		and sales_person
		and frappe.db.exists(
			"Sales Person Branch",
			{
				"parenttype": "Sales Person",
				"parent": sales_person,
				"parentfield": "custom_branches",
				"branch": branch,
				"currency": currency,
			},
		)
	):
		frappe.throw(
			_("Work Location {0} with Currency {1} is not set on your Sales Person.").format(branch, currency),
			frappe.PermissionError,
		)
	if frappe.db.get_value("Customer", customer, "default_currency") != currency or not frappe.db.exists(
		"Branch CT",
		{"parenttype": "Customer", "parent": customer, "parentfield": "custom_branch_details", "branch": branch},
	):
		frappe.throw(
			_("Customer {0} is not set up for Work Location {1} with Currency {2}.").format(
				customer, branch, currency
			),
			frappe.PermissionError,
		)


@frappe.whitelist()
def get_customer_branch_options(customer: str):
	"""The user's Work Location / Currency rows this customer can be quoted in,
	for a quotation opened with the customer already picked."""
	_check_customer(customer)
	sales_person = _session_sales_person()
	currency = frappe.db.get_value("Customer", customer, "default_currency")
	if not (sales_person and currency):
		return []
	branches = frappe.get_all(
		"Branch CT",
		filters={"parenttype": "Customer", "parent": customer, "parentfield": "custom_branch_details"},
		pluck="branch",
	)
	return frappe.get_all(
		"Sales Person Branch",
		filters={
			"parenttype": "Sales Person",
			"parent": sales_person,
			"parentfield": "custom_branches",
			"branch": ["in", branches or ["__none__"]],
			"currency": currency,
		},
		fields=["branch", "currency"],
		order_by="idx asc",
	)


def _price_line(item_code, qty, customer, branch, currency, allowed):
	"""One line priced by PAPL's Sales BOM pricing, as {ok, priced, reason, message, rate, amount}."""
	from frappe.utils import flt, strip_html
	from papl_business_logic.papl_business_logic.custom.quotation import _validate_and_price_item

	line = {"item_code": item_code, "qty": qty, "ok": False, "priced": False, "reason": "error", "message": ""}
	if item_code not in allowed:
		return dict(line, reason="not_entitled", message=_("Item {0} is not set up for this customer.").format(item_code))

	try:
		result = _validate_and_price_item(
			item_code=item_code, branch=branch, customer=customer, qty=qty, currency=currency
		)
	except Exception as exc:
		frappe.log_error(title="CRM quotation pricing failed", message=frappe.get_traceback())
		return dict(line, message=strip_html(str(exc)))

	status = result.get("status") or "error"
	ok, priced = PRICE_STATUS.get(status, (False, False))
	line.update(ok=ok, priced=priced, reason=status, message=strip_html(result.get("message") or ""))
	if priced:
		rate = flt((result.get("rate_info") or {}).get("rate"))
		line.update(rate=rate, amount=flt(rate * qty))
	return line


@frappe.whitelist()
def get_items_price(customer: str, branch: str, currency: str, items):
	"""Rates for the lines on a new quotation, priced the way the quotation will
	be on save. Each line is reported on its own so one bad line does not hide
	the rest."""
	from frappe.utils import flt

	_check_customer(customer)
	_check_branch_currency(customer, branch, currency)
	allowed = set(_entitled_items(customer, branch))

	rows = frappe.parse_json(items) if isinstance(items, str) else (items or [])
	lines = []
	# Pricing messages are returned per line, not popped up.
	frappe.flags.mute_messages = True
	try:
		for row in rows:
			item_code = (row or {}).get("item_code")
			if item_code:
				lines.append(
					_price_line(item_code, flt(row.get("qty")) or 1, customer, branch, currency, allowed)
				)
	finally:
		frappe.flags.mute_messages = False
	return {"currency": currency, "items": lines}


def _refusal(doc, default_reason, message):
	"""(reason, message) for a refused quotation. A line PAPL's validate priced
	under its Sales BOM's Min Sale Price (the rate and minimum it set on the row
	before refusing) is reported by item only: the CRM does not show the rate or
	the minimum."""
	from frappe.utils import flt

	below = [
		row.item_code
		for row in doc.items
		if flt(row.get("custom_min_sale_price")) > 0 and flt(row.rate) < flt(row.custom_min_sale_price)
	]
	if below:
		return "below_min_price", _("Price for item {0} is below the minimum allowed price.").format(
			", ".join(below)
		)
	return default_reason, message


def _linked_to(doctype, name, link_doctype, link_name):
	"""Whether an Address / Contact belongs to that Customer or Company."""
	return frappe.db.exists(
		"Dynamic Link",
		{"parenttype": doctype, "parent": name, "link_doctype": link_doctype, "link_name": link_name},
	)


@frappe.whitelist()
def create_quotation(
	customer: str,
	branch: str,
	currency: str,
	items,
	addresses=None,
	deal: str | None = None,
):
	"""Create and submit a quotation from the CRM, the way the Customer Portal
	does: no rate is sent, PAPL's validate prices every line from the Sales BOM,
	GST is chosen by the portal's tax rules, and a line left at rate 0 refuses
	the whole quotation. Runs as the logged-in user; approval is skipped like the
	portal's. The Sales Order is not raised here: the quotation page's Create
	Sales Order button calls create_sales_order when the user asks for it.

	Returns {ok, reason, message, name}."""
	from papl_business_logic.papl_business_logic.api.quotation_tax import apply_quotation_taxes
	from frappe.contacts.doctype.address.address import get_default_address
	from frappe.utils import cint, flt, nowdate, strip_html

	def refuse(reason, message):
		return {"ok": False, "reason": reason, "message": message}

	_check_customer(customer)
	_check_branch_currency(customer, branch, currency)
	sales_person = _session_sales_person()
	entitled = _entitled_items(customer, branch)
	warehouse = get_branch_warehouse(branch)
	if not warehouse:
		return refuse("no_warehouse", _(NO_WAREHOUSE).format(branch))

	rows = frappe.parse_json(items) if isinstance(items, str) else (items or [])
	rows = [row for row in rows if (row or {}).get("item_code")]
	if not rows:
		return refuse("missing_fields", _("Please add at least one item."))

	doc = frappe.new_doc("Quotation")
	doc.update(
		{
			"quotation_to": "Customer",
			"party_name": customer,
			"custom_branch": branch,
			"currency": currency,
			"custom_sale_by": sales_person,
			"transaction_date": nowdate(),
			"valid_till": nowdate(),
			"order_type": "Sales",
			"custom_created_from_crm": 1,
			# papl_business_logic "Created Via" (Backend / CRM / Customer Portal).
			"custom_created_via": "CRM",
		}
	)
	# Opened from a deal: link the quotation back to it.
	if deal:
		frappe.get_doc("CRM Deal", deal).check_permission("read")
		doc.custom_deal = deal

	# The company is whatever ERPNext puts on a new Quotation; the CRM sets none.
	company = doc.company
	if not company:
		return refuse("no_company", _("ERPNext set no company on the new quotation."))

	# Address tab: only the customer's / company's own addresses.
	addresses = frappe.parse_json(addresses) if isinstance(addresses, str) else (addresses or {})
	own = {
		"customer_address": ("Address", "Customer", customer),
		"shipping_address_name": ("Address", "Customer", customer),
		"company_address": ("Address", "Company", company),
	}
	for field, (doctype, link_doctype, link_name) in own.items():
		value = addresses.get(field)
		if not value:
			continue
		if not _linked_to(doctype, value, link_doctype, link_name):
			return refuse("not_found", _("{0} {1} does not belong to {2}.").format(doctype, value, link_name))
		doc.set(field, value)

	for row in rows:
		item_code = row["item_code"]
		if item_code not in entitled:
			return refuse("not_entitled", _("Item {0} is not set up for this customer.").format(item_code))

		# Pack items: qty is always packs x base qty, never taken from the screen.
		base_qty, in_packs = frappe.db.get_value(
			"Item", item_code, ["custom_base_qty", "custom_sell_only_as_a_multiple_of_base_qty"]
		)
		if cint(in_packs) and flt(base_qty) > 0:
			packs = cint(row.get("no_of_packs"))
			qty = flt(base_qty) * packs
		else:
			packs, base_qty = 0, 0
			qty = flt(row.get("qty"))
		if qty <= 0:
			return refuse("invalid_qty", _("Quantity for item {0} must be more than zero.").format(item_code))

		doc.append(
			"items",
			{
				"item_code": item_code,
				"qty": qty,
				"uom": entitled[item_code]["stock_uom"],
				"custom_no_of_packs": packs,
				"custom_base_qty": base_qty,
				"warehouse": warehouse,
			},
		)

	# Billing address before taxes: India Compliance re-derives place of supply
	# (and replaces the taxes) when it is blank at validate.
	if not doc.customer_address:
		doc.customer_address = get_default_address("Customer", customer)

	try:
		if not _is_gst_free_customer(customer):
			apply_quotation_taxes(doc)
	except Exception:
		frappe.log_error(title="CRM quotation taxes failed", message=frappe.get_traceback())
		return refuse("tax_failed", _("Taxes could not be worked out for this quotation."))

	try:
		block_holiday_creation(doc)
		doc.insert()
	except frappe.PermissionError:
		raise
	except Exception as exc:
		# Rolled back first, or the Error Log row goes with it; the traceback is
		# still the one from this except block.
		frappe.db.rollback()
		frappe.log_error(title="CRM quotation insert failed", message=frappe.get_traceback(with_context=True))
		return refuse(*_refusal(doc, "validation_failed", strip_html(str(exc))))

	# The rate is only known after PAPL's validate has priced the lines.
	unpriced = [row.item_code for row in doc.items if flt(row.rate) <= 0]
	if unpriced:
		frappe.db.rollback()
		return refuse(
			"unpriceable_items",
			_("No price could be found for {0}. Please remove it and try again.").format(", ".join(unpriced)),
		)

	try:
		doc.custom_approval_status = "Approved"
		doc.custom_workflow_state = "Not Required"
		doc.submit()
	except frappe.PermissionError:
		raise
	except Exception as exc:
		# Rolled back first, or the Error Log row goes with it.
		quotation_name = doc.name
		frappe.db.rollback()
		frappe.log_error(
			title="CRM quotation submit failed",
			message=frappe.get_traceback(with_context=True),
			reference_doctype="Quotation",
			reference_name=quotation_name,
		)
		return refuse(*_refusal(doc, "failed", strip_html(str(exc))))

	return {"ok": True, "reason": "submitted", "message": "", "name": doc.name}


@frappe.whitelist()
def create_sales_order(quotation: str):
	"""Create and submit the Sales Order for a submitted CRM quotation, when the
	user presses Create Sales Order on the quotation page. Only a submitted
	quotation can be ordered, and only while no live Sales Order already stands
	against it, so a second press is refused instead of raising a second order.

	Returns {ok, reason, message, sales_order}."""
	from frappe.utils import cint, strip_html

	doc = frappe.get_doc("Quotation", quotation)
	doc.check_permission("read")

	if cint(doc.docstatus) != 1:
		return {
			"ok": False,
			"reason": "not_orderable",
			"message": _("Only a submitted quotation can be turned into a Sales Order."),
		}

	if _is_expired(doc):
		return {
			"ok": False,
			"reason": "expired",
			"message": _("This quotation has expired, so a Sales Order can't be created."),
		}

	existing = _sales_orders_for(doc.name)
	if existing:
		return {
			"ok": False,
			"reason": "already_ordered",
			"message": _("Sales Order {0} has already been raised against this quotation.").format(
				existing[0]
			),
			"sales_order": existing[0],
		}

	try:
		order = _make_sales_order(doc)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		# Rolled back first, or the Error Log row goes with it; the quotation
		# itself stays submitted and can be ordered again later.
		frappe.db.rollback()
		frappe.log_error(
			title="CRM quotation Sales Order failed",
			message=frappe.get_traceback(with_context=True),
			reference_doctype="Quotation",
			reference_name=doc.name,
		)
		return {"ok": False, "reason": "failed", "message": strip_html(str(exc))}

	if order.docstatus == 0:
		return {
			"ok": True,
			"reason": "pending_approval",
			"message": _("Sales Order {0} is waiting for credit approval.").format(order.name),
			"sales_order": order.name,
		}
	return {"ok": True, "reason": "ordered", "message": "", "sales_order": order.name}


def _sales_order_states(quotation):
	"""{sales order: indicator} for the orders made from this quotation."""
	from crm.api.sales_order_list import get_indicator as sales_order_indicator

	names = _sales_orders_for(quotation)
	if not names:
		return {}
	return {
		d.name: sales_order_indicator(d)
		for d in frappe.get_all(
			"Sales Order",
			filters={"name": ["in", names]},
			fields=["name", "docstatus", "status", "per_delivered", "custom_credit_approval_status"],
		)
	}


def _sales_orders_for(quotation):
	"""Draft or submitted Sales Orders made from this quotation."""
	return sorted(
		set(
			frappe.get_all(
				"Sales Order Item",
				filters={"prevdoc_docname": quotation, "docstatus": ["<", 2]},
				pluck="parent",
			)
		)
	)


def _make_sales_order(quotation):
	"""Create and submit the Sales Order for a just-submitted CRM quotation, the
	way the Customer Portal does: PAPL's metal-rate check, then PAPL's own mapper (it
	refuses an expired quotation) so the order copies the quoted lines, rates,
	taxes and payment schedule; delivery is today + 7 days. Raises on any error
	so the caller can roll the quotation back with it.

	Saved, then submitted, as the desk does (so ERPNext sets the order status).
	An order over PAPL's floating limit is saved as a Pending draft and not
	submitted; the Credit Approval Dashboard submits it when it is approved."""
	from frappe.utils import add_days, nowdate
	from papl_business_logic.papl_business_logic.custom.quotation import (
		make_sales_order,
		validate_metal_rate_before_so,
	)

	warehouse = get_branch_warehouse(quotation.custom_branch)
	if not warehouse:
		frappe.throw(_(NO_WAREHOUSE).format(quotation.custom_branch))

	# Same gate as the desk's Create > Sales Order button: no order once the
	# metal rate has risen past the tolerance it was quoted at.
	try:
		validate_metal_rate_before_so(quotation.name)
	except frappe.ValidationError as exc:
		# PAPL's message carries the new metal rate; the CRM only asks for a revision.
		if not str(exc).startswith(METAL_RATE_PREFIX):
			raise
		frappe.clear_messages()
		frappe.throw(_(METAL_RATE_RISEN), title=_("Metal Rate Exceeded"))

	delivery_date = add_days(nowdate(), 7)
	order = make_sales_order(quotation.name)
	order.delivery_date = delivery_date
	# papl_business_logic "Created Via"; the CRM Sales Orders list reads this.
	order.custom_created_via = "CRM"
	order.custom_crm_quotation = quotation.name
	# Sale By is required on the order.
	if order.meta.has_field("custom_sale_by") and not order.get("custom_sale_by"):
		order.custom_sale_by = quotation.get("custom_sale_by") or _session_sales_person()
	for row in order.items:
		row.delivery_date = delivery_date
		# Always the branch's warehouse from CRM Warehouse Settings, not the item's.
		row.warehouse = warehouse
	# CRM Custom Settings window, checked here and not as a doc hook so orders
	# raised from the ERPNext desk are not limited.
	_block_outside_window(order, "sales_order", _("Sales Order"))
	# PAPL's floating-limit popup (HTML with a chart) is not for the CRM; the
	# result below says what happened.
	frappe.flags.mute_messages = True
	try:
		order.insert()
		# Over the floating limit: PAPL has marked the draft Pending, which puts it
		# on the Credit Approval Dashboard; approving it there submits it. Left as
		# a draft, as the desk does, instead of submitting into PAPL's refusal.
		if order.get("custom_credit_approval_status") == "Pending":
			return order
		order.submit()
	finally:
		frappe.flags.mute_messages = False
	return order
