# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time, getdate

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
		from crm.fcrm.doctype.crm_branch_stock_warehouse.crm_branch_stock_warehouse import (
			CRMBranchStockWarehouse,
		)
		from crm.fcrm.doctype.crm_branch_warehouse.crm_branch_warehouse import CRMBranchWarehouse
		from crm.fcrm.doctype.crm_week_days.crm_week_days import CRMWeekDays
		from crm.fcrm.doctype.fcrm_holiday_list.fcrm_holiday_list import FCRMHolidayList
		from crm.fcrm.doctype.fcrm_timing_setting.fcrm_timing_setting import FCRMTimingSetting
		from crm.fcrm.doctype.non_inventory_item.non_inventory_item import NonInventoryItem
		from frappe.types import DF

		branch_stock_warehouses: DF.Table[CRMBranchStockWarehouse]
		branch_warehouses: DF.Table[CRMBranchWarehouse]
		holiday_list: DF.Link | None
		holiday_list_table: DF.Table[FCRMHolidayList]
		lead_sla_days: DF.Int
		non_inventory_items: DF.Table[NonInventoryItem]
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

		self.validate_branch_stock_warehouses()
		self.validate_time_settings()
		self.validate_non_inventory_items()

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


	def validate_branch_stock_warehouses(self):
		"""One row per branch, at least one child warehouse, and every child a
		stock-holding warehouse under the row's parent warehouse."""
		seen = set()
		for row in self.branch_stock_warehouses:
			if row.branch in seen:
				frappe.throw(
					_("Stock Warehouses Row #{0}: Branch {1} is listed more than once.").format(
						row.idx, row.branch
					)
				)
			seen.add(row.branch)
			children = split_warehouses(row.child_warehouses)
			if not children:
				frappe.throw(
					_("Stock Warehouses Row #{0}: select at least one child warehouse for {1}.").format(
						row.idx, row.branch
					)
				)
			allowed = set(get_child_warehouses(row.parent_warehouse))
			for warehouse in children:
				if warehouse not in allowed:
					frappe.throw(
						_("Stock Warehouses Row #{0}: {1} is not under {2}.").format(
							row.idx, warehouse, row.parent_warehouse
						)
					)
			row.child_warehouses = "\n".join(children)

	def validate_non_inventory_items(self):
		"""One row per Branch + Currency + Item. Rows without an item are not compared."""
		seen = {}
		for row in self.non_inventory_items:
			if not row.item:
				continue
			if frappe.get_cached_value("Item", row.item, "is_stock_item"):
				frappe.throw(
					_("Row #{0}: {1} is a stock item. Pick a non-inventory (service) item.").format(
						row.idx, row.item
					),
					title=_("Not a Non-Inventory Item"),
				)
			key = (row.branch, row.currency_type, row.item)
			if key in seen:
				frappe.throw(
					_("Row #{0}: Item {1} is already added for Branch {2} and Currency {3} in Row #{4}.").format(
						row.idx, row.item, row.branch, row.currency_type, seen[key]
					),
					title=_("Duplicate Entry"),
				)
			seen[key] = row.idx

	def validate_time_settings(self):
		"""From Time before To Time, and no two rows of one branch overlapping for
		a document both tick (Quotation / Sales Order), or when either row ticks
		neither. Rows that only touch
		(10:00-13:00 and 13:00-15:00) do not overlap."""
		documents = (("quotation", _("Quotation")), ("sales_order", _("Sales Order")))
		rows = self.time_setting_branch_wise
		for row in rows:
			if get_time(row.from_time) >= get_time(row.to_time):
				frappe.throw(
					_("Row #{0}: From Time must be before To Time for {1}.").format(row.idx, row.branch),
					title=_("Invalid Time"),
				)
		for i, row in enumerate(rows):
			for earlier in rows[:i]:
				if earlier.branch != row.branch:
					continue
				if not (
					get_time(row.from_time) < get_time(earlier.to_time)
					and get_time(earlier.from_time) < get_time(row.to_time)
				):
					continue
				shared = [label for field, label in documents if row.get(field) and earlier.get(field)]
				# A row with neither document ticked gates nothing, so it can
				# never be told apart from the row it overlaps: refuse that too.
				untouched = not any(row.get(f) for f, _label in documents) or not any(
					earlier.get(f) for f, _label in documents
				)
				if shared or untouched:
					frappe.throw(
						_("Row #{0}: {1} {2} - {3} overlaps with Row #{4} ({5} - {6}) for {7}.").format(
							row.idx,
							row.branch,
							row.from_time,
							row.to_time,
							earlier.idx,
							earlier.from_time,
							earlier.to_time,
							", ".join(shared) or _("Quotation / Sales Order"),
						),
						title=_("Overlapping Time"),
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


def split_warehouses(value):
	"""The warehouse names in a Child Warehouses field (one per line), in order, without repeats."""
	return list(dict.fromkeys(w.strip() for w in (value or "").splitlines() if w.strip()))


@frappe.whitelist()
def get_child_warehouses(parent_warehouse):
	"""Stock-holding (non-group) warehouses anywhere under a group warehouse, for
	the Select Warehouses checklist."""
	frappe.has_permission("CRM Custom Settings", "write", throw=True)
	if not parent_warehouse:
		return []
	lft, rgt = frappe.db.get_value("Warehouse", parent_warehouse, ["lft", "rgt"]) or (None, None)
	if lft is None:
		return []
	return frappe.get_all(
		"Warehouse",
		filters={"lft": (">", lft), "rgt": ("<", rgt), "is_group": 0},
		pluck="name",
		order_by="lft asc",
	)


def get_branch_stock_warehouses(branch):
	"""The child warehouses whose stock the Available Stock page adds up for this branch."""
	return split_warehouses(
		frappe.db.get_value(
			"CRM Branch Stock Warehouse",
			{"parent": "CRM Custom Settings", "parentfield": "branch_stock_warehouses", "branch": branch},
			"child_warehouses",
		)
	)


def get_print_format(branch, fieldname):
	"""The print format this branch's row sets, or None so the caller falls back
	to the doctype's own default. `fieldname` is quotation_print_format or
	sales_order_print_format."""
	if not branch:
		return None
	return frappe.db.get_value(
		"CRM Branch Warehouse",
		{"parent": "CRM Custom Settings", "parentfield": "branch_warehouses", "branch": branch},
		fieldname,
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
