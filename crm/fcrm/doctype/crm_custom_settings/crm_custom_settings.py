# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

BRANCH_FIELDS = {"MIDC": "midc", "FTWZ": "ftwz", "SEEPZ": "seepz"}

WEEKDAYS = (
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
)


class CRMCustomSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.fcrm.doctype.crm_branch_warehouse.crm_branch_warehouse import CRMBranchWarehouse
		from crm.fcrm.doctype.crm_week_days.crm_week_days import CRMWeekDays
		from crm.fcrm.doctype.fcrm_holiday_list.fcrm_holiday_list import FCRMHolidayList
		from crm.fcrm.doctype.fcrm_timing_setting.fcrm_timing_setting import FCRMTimingSetting
		from frappe.types import DF

		branch_warehouses: DF.Table[CRMBranchWarehouse]
		holiday_list: DF.Link | None
		holiday_list_table: DF.Table[FCRMHolidayList]
		time_setting_branch_wise: DF.Table[FCRMTimingSetting]
		week_days: DF.Table[CRMWeekDays]
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

		if not self.week_days:
			for day in WEEKDAYS:
				working = day not in ("Saturday", "Sunday")
				self.append(
					"week_days",
					{"week_day": day, **{f: int(working) for f in BRANCH_FIELDS.values()}},
				)


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


def is_holiday(date, branch=None):
	"""True when the date is a holiday in CRM Custom Settings for this branch.

	A row with none of the branch checks ticked is a holiday for every branch;
	otherwise only the ticked branches are blocked."""
	if not date:
		return False

	rows = frappe.get_all(
		"FCRM Holiday List",
		filters={
			"parent": "CRM Custom Settings",
			"parentfield": "holiday_list_table",
			"date": getdate(date),
		},
		fields=list(BRANCH_FIELDS.values()),
	)
	field = BRANCH_FIELDS.get(branch)
	return any(not any(row.values()) or (field and row.get(field)) for row in rows)


def is_working_day(date, branch=None):
	"""True when the weekday of `date` is a working day for this branch.

	The Week Days table ticks the branches that may create quotations that day;
	a row with no branch ticked is non-working for every branch."""
	if not date:
		return False

	field = BRANCH_FIELDS.get(branch)
	if not field:
		return True

	return bool(
		frappe.db.get_value(
			"CRM Week Days",
			{
				"parent": "CRM Custom Settings",
				"parentfield": "week_days",
				"week_day": WEEKDAYS[getdate(date).weekday()],
			},
			field,
		)
	)
