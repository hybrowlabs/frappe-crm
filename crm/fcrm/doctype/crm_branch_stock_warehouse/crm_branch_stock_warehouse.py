# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMBranchStockWarehouse(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		branch: DF.Link
		child_warehouses: DF.SmallText | None
		parent: DF.Data
		parent_warehouse: DF.Link
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types
	pass
