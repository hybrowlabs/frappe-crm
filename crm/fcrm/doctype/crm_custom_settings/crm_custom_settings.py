# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CRMCustomSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.fcrm.doctype.crm_branch_warehouse.crm_branch_warehouse import CRMBranchWarehouse
		from crm.fcrm.doctype.fcrm_holiday_list.fcrm_holiday_list import FCRMHolidayList
		from crm.fcrm.doctype.fcrm_timing_setting.fcrm_timing_setting import FCRMTimingSetting
		from frappe.types import DF

		branch_warehouses: DF.Table[CRMBranchWarehouse]
		friday: DF.Check
		holiday_list: DF.Link | None
		holiday_list_table: DF.Table[FCRMHolidayList]
		monday: DF.Check
		saturday: DF.Check
		sunday: DF.Check
		thursday: DF.Check
		time_setting_branch_wise: DF.Table[FCRMTimingSetting]
		tuesday: DF.Check
		wednesday: DF.Check
	# end: auto-generated types
	def validate(self):
		seen = set()
		for row in self.branch_warehouses:
			if row.branch in seen:
				frappe.throw(_("Row #{0}: Branch {1} is listed more than once.").format(row.idx, row.branch))
			seen.add(row.branch)
			if frappe.db.get_value("Warehouse", row.warehouse, "is_group"):
				frappe.throw(
					_("Row #{0}: {1} is a group warehouse; pick a warehouse that holds stock.").format(
						row.idx, row.warehouse
					)
				)

		if self.holiday_list and (self.is_new() or self.has_value_changed("holiday_list")):
			self.set("holiday_list_table", [])
			for holiday_date in get_holiday_list_dates(self.holiday_list):
				self.append("holiday_list_table", {"date": holiday_date})


@frappe.whitelist()
def get_holiday_list_dates(holiday_list):
	"""Return the dates configured in a Holiday List for the settings form."""
	if not holiday_list:
		return []

	frappe.has_permission("Holiday List", "read", holiday_list, throw=True)
	return frappe.get_all(
		"Holiday",
		filters={
			"parent": holiday_list,
			"parenttype": "Holiday List",
			"parentfield": "holidays",
		},
		pluck="holiday_date",
		order_by="holiday_date asc",
	)

def get_branch_warehouse(branch):
	"""The warehouse set for this branch, or None."""
	return frappe.db.get_value(
		"CRM Branch Warehouse",
		{"parent": "CRM Custom Settings", "parentfield": "branch_warehouses", "branch": branch},
		"warehouse",
	)


def is_holiday(date):
	"""True when the date is in the holiday list configured in CRM Custom Settings."""
	return bool(
		date
		and frappe.db.exists(
			"FCRM Holiday List",
			{
				"parent": "CRM Custom Settings",
				"parentfield": "holiday_list_table",
				"date": getdate(date),
			},
		)
	)
