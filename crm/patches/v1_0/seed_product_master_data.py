import json
import os

import frappe

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _load(filename):
	with open(os.path.join(DATA_DIR, filename)) as f:
		return json.load(f)


def _ensure_subcategories(doc, sub_categories):
	"""Append any missing sub-categories to a `product_sub_categories` multiselect.

	Returns True if the doc was modified.
	"""
	existing = {row.product_sub_category for row in doc.product_sub_categories}
	changed = False
	for sub in sub_categories:
		if sub not in existing:
			doc.append("product_sub_categories", {"product_sub_category": sub})
			changed = True
	return changed


def seed_categories(hierarchy):
	for category in hierarchy["categories"]:
		if not frappe.db.exists("CRM Product Category", category):
			frappe.get_doc(
				{"doctype": "CRM Product Category", "product_category": category}
			).insert(ignore_permissions=True)


def seed_sub_categories(hierarchy):
	for row in hierarchy["sub_categories"]:
		if not frappe.db.exists("CRM Product Sub Category", row["sub_category"]):
			frappe.get_doc(
				{
					"doctype": "CRM Product Sub Category",
					"product_sub_category": row["sub_category"],
					"product_category": row["category"],
				}
			).insert(ignore_permissions=True)


def seed_variants(hierarchy):
	for row in hierarchy["variants"]:
		if frappe.db.exists("CRM Product Variant", row["variant"]):
			doc = frappe.get_doc("CRM Product Variant", row["variant"])
			if _ensure_subcategories(doc, row["sub_categories"]):
				doc.save(ignore_permissions=True)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "CRM Product Variant",
				"product_variant": row["variant"],
				"unit_of_measure": row["uom"],
			}
		)
		_ensure_subcategories(doc, row["sub_categories"])
		doc.insert(ignore_permissions=True)


def seed_pain_points(pain_points):
	for row in pain_points:
		if frappe.db.exists("CRM Pain Point", row["pain_point"]):
			doc = frappe.get_doc("CRM Pain Point", row["pain_point"])
			if _ensure_subcategories(doc, row["sub_categories"]):
				doc.save(ignore_permissions=True)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "CRM Pain Point",
				"pain_point": row["pain_point"],
				"pain_type": row["pain_type"],
			}
		)
		_ensure_subcategories(doc, row["sub_categories"])
		doc.insert(ignore_permissions=True)


def execute():
	# Bail out gracefully if the masters aren't installed yet.
	required = (
		"CRM Product Category",
		"CRM Product Sub Category",
		"CRM Product Variant",
		"CRM Pain Point",
	)
	if any(not frappe.db.exists("DocType", dt) for dt in required):
		return

	hierarchy = _load("product_hierarchy.json")
	pain_points = _load("pain_points_matched.json")

	# 1) Product hierarchy: Category -> Sub Category -> Variant
	seed_categories(hierarchy)
	seed_sub_categories(hierarchy)
	seed_variants(hierarchy)

	# 2) Matched pain points (mapped to existing sub-categories)
	seed_pain_points(pain_points)

	frappe.db.commit()
