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
