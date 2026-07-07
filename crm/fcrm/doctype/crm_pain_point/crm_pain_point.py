# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CRMPainPoint(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.fcrm.doctype.crm_product_category_select.crm_product_category_select import CRMProductCategorySelect
		from crm.fcrm.doctype.crm_product_sub_category_select.crm_product_sub_category_select import CRMProductSubCategorySelect
		from frappe.types import DF

		pain_point: DF.Data
		pain_type: DF.Literal["Technical", "Commercial"]
		product_categories: DF.TableMultiSelect[CRMProductCategorySelect]
		product_sub_categories: DF.TableMultiSelect[CRMProductSubCategorySelect]
	# end: auto-generated types

	pass
