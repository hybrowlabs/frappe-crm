# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.api.exchange_rate import get_exchange_rate


class CRMOrganization(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.Link | None
		annual_revenue: DF.Currency
		currency: DF.Link | None
		exchange_rate: DF.Float
		gstin: DF.Data | None
		industry: DF.Link | None
		no_of_employees: DF.Literal["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
		organization_logo: DF.AttachImage | None
		organization_name: DF.Data | None
		territory: DF.Link | None
		website: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.update_exchange_rate()
		self.refetch_previous_order_items()
		self.update_last_order()

	def update_last_order(self):
		"""Store the date of the linked customer's most recent submitted Sales Order,
		so the org list can filter dormancy live from a single stored date."""
		customer = self.get("erpnext_customer")
		if not customer or not frappe.db.exists("DocType", "Sales Order"):
			return
		self.last_order = frappe.db.get_value(
			"Sales Order",
			{"customer": customer, "docstatus": 1},
			"transaction_date",
			order_by="transaction_date desc",
		)

	def refetch_previous_order_items(self):
		"""When the linked ERPNext customer changes, rebuild the previously-ordered
		items from that customer's submitted Sales Orders (cleared if unlinked)."""
		if not self.has_value_changed("erpnext_customer"):
			return

		from crm.api.sales_order import get_ordered_items_for_customer

		totals = get_ordered_items_for_customer(self.get("erpnext_customer"))
		self.set("previous_order_items", [])
		for item_code, quantity in totals.items():
			self.append("previous_order_items", {"item_code": item_code, "quantity": quantity})

	def update_exchange_rate(self):
		if self.has_value_changed("currency") or not self.exchange_rate:
			system_currency = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
			exchange_rate = 1
			if self.currency and self.currency != system_currency:
				exchange_rate = get_exchange_rate(self.currency, system_currency)

			self.db_set("exchange_rate", exchange_rate)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Organization",
				"type": "Data",
				"key": "organization_name",
				"width": "16rem",
			},
			{
				"label": "Website",
				"type": "Data",
				"key": "website",
				"width": "14rem",
			},
			{
				"label": "Industry",
				"type": "Link",
				"key": "industry",
				"options": "CRM Industry",
				"width": "14rem",
			},
			{
				"label": "Annual Revenue",
				"type": "Currency",
				"key": "annual_revenue",
				"width": "14rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"organization_name",
			"organization_logo",
			"website",
			"industry",
			"currency",
			"annual_revenue",
			"modified",
		]
		return {"columns": columns, "rows": rows}


def update_repeat_business_signals():
	"""Nightly: recompute the two aggregate order-signal checkboxes for every linked
	organization, and refresh last_order. The two date-based signals (no order 20-29
	days, dormant 30+ days) are derived live from last_order at list-filter time.

	- ordering_below_average: this month's order count < its trailing 3-month average.
	- declining_order_value: average order value this quarter < last quarter.
	"""
	from frappe.utils import add_months, get_first_day, getdate

	if not frappe.db.exists("DocType", "Sales Order"):
		return

	orgs = frappe.get_all(
		"CRM Organization",
		filters={"erpnext_customer": ["is", "set"]},
		fields=["name", "erpnext_customer"],
	)
	if not orgs:
		return

	customers = list({o.erpnext_customer for o in orgs})

	today = getdate()
	month_start = get_first_day(today)
	prev3_start = get_first_day(add_months(month_start, -3))
	quarter_start = get_first_day(add_months(month_start, -((today.month - 1) % 3)))
	last_quarter_start = get_first_day(add_months(quarter_start, -3))
	window_start = min(prev3_start, last_quarter_start)

	orders = frappe.get_all(
		"Sales Order",
		filters={
			"docstatus": 1,
			"customer": ["in", customers],
			"transaction_date": [">=", window_start],
		},
		fields=["customer", "transaction_date", "base_grand_total"],
	)
	by_customer = {}
	for o in orders:
		by_customer.setdefault(o.customer, []).append(o)

	last_orders = frappe.get_all(
		"Sales Order",
		filters={"docstatus": 1, "customer": ["in", customers]},
		fields=["customer", "MAX(transaction_date) as last_order"],
		group_by="customer",
	)
	last_map = {r.customer: r.last_order for r in last_orders}

	for org in orgs:
		rows = by_customer.get(org.erpnext_customer, [])
		current_count = sum(1 for r in rows if getdate(r.transaction_date) >= month_start)
		prev3_count = sum(1 for r in rows if prev3_start <= getdate(r.transaction_date) < month_start)
		below = 1 if current_count < (prev3_count / 3) else 0

		this_q = [r for r in rows if getdate(r.transaction_date) >= quarter_start]
		last_q = [r for r in rows if last_quarter_start <= getdate(r.transaction_date) < quarter_start]
		this_avg = sum((r.base_grand_total or 0) for r in this_q) / len(this_q) if this_q else 0
		last_avg = sum((r.base_grand_total or 0) for r in last_q) / len(last_q) if last_q else 0
		declining = 1 if (last_q and this_avg < last_avg) else 0

		frappe.db.set_value(
			"CRM Organization",
			org.name,
			{
				"ordering_below_average": below,
				"declining_order_value": declining,
				"last_order": last_map.get(org.erpnext_customer),
			},
			update_modified=False,
		)
	frappe.db.commit()


def sync_customers_to_crm_orgs():
	"""Daily: create a CRM Organization for every ERPNext Customer not already
	linked to one, keeping the customer connected via erpnext_customer."""
	linked = set(
		frappe.get_all(
			"CRM Organization",
			filters={"erpnext_customer": ["is", "set"]},
			pluck="erpnext_customer",
		)
	)
	for customer in frappe.get_all("Customer", fields=["name", "customer_name", "territory"]):
		if customer.name in linked:
			continue
		try:
			org = frappe.new_doc("CRM Organization")
			org.organization_name = customer.customer_name or customer.name
			org.erpnext_customer = customer.name
			if customer.territory:
				org.territory = customer.territory
			org.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Customer sync to CRM Org failed: {customer.name}")
