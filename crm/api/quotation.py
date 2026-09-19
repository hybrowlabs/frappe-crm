import frappe
from frappe import _

from crm.fcrm.doctype.crm_warehouse_settings.crm_warehouse_settings import get_branch_warehouse

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
		"quotation_to": doc.quotation_to,
		"transaction_date": doc.transaction_date,
		"valid_till": doc.valid_till,
		"company": doc.company,
		"order_type": doc.order_type,
		"currency": doc.currency,
		"deal": doc.get("custom_deal"),
		"sale_by": doc.get("custom_sale_by"),
		"owner": doc.owner,
		"owner_name": frappe.utils.get_fullname(doc.owner),
		# Any draft or submitted Sales Order made from this quotation.
		"sales_orders": _sales_orders_for(name),
		"creation": doc.creation,
		"items": [
			{
				"item_code": i.item_code,
				"item_name": i.item_name,
				"description": i.description,
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
	}


def _session_sales_person():
	"""The session user's enabled Sales Person, if any."""
	from crm.api.sales_manager import sales_person_from_user

	sales_person = sales_person_from_user(frappe.session.user)
	if sales_person and frappe.db.get_value("Sales Person", sales_person, "enabled"):
		return sales_person


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


# Pricing-core status -> (call succeeded, rate set). Same map as the Customer
# Portal: an item with no Sales BOM rate is
# not an error, it just has no number to show.
PRICE_STATUS = {
	"success": (True, True),
	"non_stock": (True, False),
	"inactive_bom": (True, False),
	"raw_material": (True, False),
}


def _branch_currency(branch):
	"""The currency on the user's Sales Person row for this branch; the branch
	must be one of the user's own."""
	sales_person = _session_sales_person()
	currency = sales_person and frappe.db.get_value(
		"Sales Person Branch",
		{"parenttype": "Sales Person", "parent": sales_person, "parentfield": "custom_branches", "branch": branch},
		"currency",
	)
	if not currency:
		frappe.throw(_("Branch {0} is not set on your Sales Person.").format(branch), frappe.PermissionError)
	return currency


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
def get_items_price(customer: str, branch: str, items):
	"""Rates for the lines on a new quotation, priced the way the quotation will
	be on save. Each line is reported on its own so one bad line does not hide
	the rest."""
	from frappe.utils import flt

	_check_customer(customer)
	currency = _branch_currency(branch)
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
	items,
	addresses=None,
	deal: str | None = None,
):
	"""Create and submit a quotation from the CRM, then create and submit its
	Sales Order, the way the Customer Portal does:
	no rate is sent, PAPL's validate prices every line from the Sales BOM, GST
	is chosen by the portal's tax rules, and a line left at rate 0 refuses the
	whole quotation. Runs as the logged-in user; approval is skipped like the
	portal's. All or nothing: if the quotation or its Sales Order fails, neither
	is kept and the error is returned.

	Returns {ok, reason, message, name, sales_order}."""
	from papl_business_logic.papl_business_logic.api.quotation_tax import apply_quotation_taxes
	from frappe.contacts.doctype.address.address import get_default_address
	from frappe.utils import cint, flt, nowdate, strip_html

	def refuse(reason, message):
		return {"ok": False, "reason": reason, "message": message}

	_check_customer(customer)
	currency = _branch_currency(branch)
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
		apply_quotation_taxes(doc)
	except Exception:
		frappe.log_error(title="CRM quotation taxes failed", message=frappe.get_traceback())
		return refuse("tax_failed", _("Taxes could not be worked out for this quotation."))

	try:
		doc.insert()
	except frappe.PermissionError:
		raise
	except Exception as exc:
		frappe.db.rollback()
		return refuse("validation_failed", strip_html(str(exc)))

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
		order = _make_sales_order(doc)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		# All or nothing: a quotation is only kept together with its Sales Order.
		frappe.db.rollback()
		return refuse("failed", strip_html(str(exc)))

	return {"ok": True, "reason": "ordered", "message": "", "name": doc.name, "sales_order": order.name}


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
	PAPL's credit-limit hold only commits on its own when the hold status changed
	since the save, which cannot happen within this one request, so a hold just
	raises and is rolled back with everything else."""
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
	validate_metal_rate_before_so(quotation.name)

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
	order.insert()
	order.submit()
	return order
