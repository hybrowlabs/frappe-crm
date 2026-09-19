import frappe
from frappe import _
from frappe.utils import flt

from crm.api.quotation import can_see_all_quotations

# CRM list/detail views over ERPNext's Sales Order, limited to orders created
# in the CRM (papl_business_logic "Created Via" = CRM). Normal users see only the
# orders they created; Administrator and System Managers see all of them.

# The order states the Customer Portal shows (customer_experiance/papl_api.py,
# _order_state), plus ERPNext's own Draft / Cancelled / Closed / On Hold.
STATE_COLORS = {
	"Draft": "red",
	"Confirmed": "blue",
	"Dispatched": "orange",
	"Delivered": "green",
	"On Hold": "yellow",
	"Closed": "gray",
	"Cancelled": "red",
}


def get_state(doc):
	"""Draft, Confirmed, Dispatched (part delivered), Delivered, or ERPNext's
	Cancelled / Closed / On Hold."""
	if doc.get("docstatus") == 0:
		return "Draft"
	if doc.get("docstatus") == 2:
		return "Cancelled"
	if doc.get("status") in ("Closed", "On Hold"):
		return doc.get("status")
	if doc.get("status") == "Completed" or flt(doc.get("per_delivered")) >= 100:
		return "Delivered"
	if flt(doc.get("per_delivered")) > 0:
		return "Dispatched"
	return "Confirmed"


def get_indicator(doc):
	state = get_state(doc)
	return {"label": state, "color": STATE_COLORS.get(state, "gray")}


def state_filter(value):
	"""Filters matching a state from get_state()."""
	if value == "Draft":
		return {"docstatus": 0}
	if value == "Cancelled":
		return {"docstatus": 2}
	if value in ("Closed", "On Hold"):
		return {"docstatus": 1, "status": value}
	open_statuses = ["not in", ["Closed", "On Hold"]]
	if value == "Delivered":
		return {"docstatus": 1, "status": open_statuses, "per_delivered": [">=", 100]}
	if value == "Dispatched":
		return {"docstatus": 1, "status": open_statuses, "per_delivered": ["between", [0.000001, 99.999999]]}
	return {"docstatus": 1, "status": ["not in", ["Closed", "On Hold", "Completed"]], "per_delivered": 0}


def translate_status_filter(filters):
	"""Rewrites an equality filter on status (quick filter or Filter button) to
	the order state shown in the CRM."""
	value = filters.get("status")
	if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] == "=":
		value = value[1]
	if not value or not isinstance(value, str) or value not in STATE_COLORS:
		return
	del filters["status"]
	filters.update(state_filter(value))


def sales_order_filter():
	"""Only CRM-created orders, and only the session user's own unless they may see all."""
	filters = {"custom_created_via": "CRM"}
	if not can_see_all_quotations():
		filters["owner"] = frappe.session.user
	return filters


class SalesOrderList:
	"""Stands in for a list controller: Sales Order is ERPNext's doctype, so it
	has no CRM default_list_data of its own."""

	@staticmethod
	def default_list_data():
		columns = [
			{"label": "Sales Order No", "type": "Data", "key": "name", "width": "12rem"},
			# The column is customer; the CRM list shows customer_name in it.
			{"label": "Customer", "type": "Link", "key": "customer", "width": "15rem"},
			{"label": "Quotation", "type": "Link", "key": "custom_crm_quotation", "width": "11rem"},
			{"label": "Date", "type": "Date", "key": "transaction_date", "width": "8rem"},
			{"label": "Delivery Date", "type": "Date", "key": "delivery_date", "width": "8rem"},
			{"label": "Amount", "type": "Currency", "key": "grand_total", "width": "9rem"},
			{"label": "Status", "type": "Select", "key": "status", "width": "9rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]
		rows = [
			"name",
			"customer",
			"customer_name",
			"custom_crm_quotation",
			"transaction_date",
			"delivery_date",
			"grand_total",
			"currency",
			"status",
			"modified",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def parse_list_data(data):
		"""Adds the order state to each row, whatever columns were chosen."""
		names = [row.get("name") for row in data if row.get("name")]
		if not names:
			return data
		docs = {
			d.name: d
			for d in frappe.get_all(
				"Sales Order",
				filters={"name": ["in", names]},
				fields=["name", "docstatus", "status", "per_delivered"],
			)
		}
		for row in data:
			doc = docs.get(row.get("name"))
			if doc:
				row["_indicator"] = get_indicator(doc)
		return data


QUICK_FILTERS = [
	("name", "Sales Order No"),
	("customer_name", "Customer"),
	("custom_crm_quotation", "Quotation"),
	("status", None),
	("delivery_date", None),
]


def get_quick_filter_fields():
	meta = frappe.get_meta("Sales Order")
	fields = []
	for fieldname, label in QUICK_FILTERS:
		if fieldname == "name":
			fields.append(frappe._dict(label=label, fieldname="name", fieldtype="Data"))
			continue
		field = meta.get_field(fieldname)
		if field:
			options = "\n".join(STATE_COLORS) if fieldname == "status" else field.options
			fields.append(
				frappe._dict(
					label=label or field.label,
					fieldname=fieldname,
					fieldtype=field.fieldtype,
					options=options,
				)
			)
	return fields


@frappe.whitelist()
def get_sales_order(name: str):
	"""Read-only view of one CRM sales order for the CRM sales order page."""
	doc = frappe.get_doc("Sales Order", name)
	doc.check_permission("read")
	if not can_see_all_quotations() and doc.owner != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	quotation = doc.get("custom_crm_quotation") or next(
		(row.prevdoc_docname for row in doc.items if row.prevdoc_docname), None
	)
	return {
		"name": doc.name,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"indicator": get_indicator(doc),
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"quotation": quotation,
		"transaction_date": doc.transaction_date,
		"delivery_date": doc.delivery_date,
		"company": doc.company,
		"branch": doc.get("branch"),
		"currency": doc.currency,
		"sale_by": doc.get("custom_sale_by"),
		"per_delivered": flt(doc.per_delivered),
		"per_billed": flt(doc.per_billed),
		"items": [
			{
				"item_code": i.item_code,
				"item_name": i.item_name,
				"qty": i.qty,
				"delivered_qty": i.delivered_qty,
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
