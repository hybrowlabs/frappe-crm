import json

import frappe

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_default_layout


def execute():
	"""Rebuild the CRM Deal 'Data Fields' layout so the Data tab shows every field,
	flattened into a single tab so nothing is hidden behind sub-tabs."""
	layout = build_all_fields_layout("CRM Deal")

	name = frappe.db.exists("CRM Fields Layout", {"dt": "CRM Deal", "type": "Data Fields"})
	if name:
		doc = frappe.get_doc("CRM Fields Layout", name)
	else:
		doc = frappe.new_doc("CRM Fields Layout")
		doc.dt = "CRM Deal"
		doc.type = "Data Fields"

	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)


def build_all_fields_layout(doctype):
	tabs = get_default_layout(doctype)

	sections = []
	seen = set()
	for tab in tabs:
		for section in tab.get("sections", []):
			for column in section.get("columns", []):
				column["fields"] = [
					f for f in column.get("fields", []) if not (f in seen or seen.add(f))
				]
			sections.append(section)

	return [{"name": "all_fields_tab", "sections": sections}]
