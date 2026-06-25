import re

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Sales Person tree to mirror the staging export: (name, is_group, parent).
# The export shares one email across everyone; we instead mint a distinct
# firstnamelastname@example.com per person (see email_for) and a matching User.
SALES_PERSONS = [
	("Sales Team", 1, ""),
	("Vicky Mahendru", 1, "Sales Team"),
	("Deepa Chawda", 1, "Vicky Mahendru"),
	("Amit Tiwari", 0, "Deepa Chawda"),
	("Harshit Tiwari", 0, "Deepa Chawda"),
	("Kisan Dave", 1, "Vicky Mahendru"),
	("Sujeet Rajawat", 0, "Kisan Dave"),
	("Sumit Biswas", 0, "Kisan Dave"),
	("Pradeep Kulkarni", 0, "Kisan Dave"),
	("Mr.Anandu", 0, "Kisan Dave"),
	("Mr.Nitin", 0, "Kisan Dave"),
	("Mr.Raj", 0, "Kisan Dave"),
	("Palak Patel", 0, "Pradip Shiroya"),
	("Pradip Shiroya", 1, "Vicky Mahendru"),
	("Tushar Korat", 0, "Pradip Shiroya"),
	("Rushikesh Joshi", 0, "Pradip Shiroya"),
	("Fulfillment Desk", 1, "Vicky Mahendru"),
	("Devyani Khanvilkar", 0, "Fulfillment Desk"),
	("Ram Dhuri", 0, "Fulfillment Desk"),
	("Aditi Pandya", 0, "Fulfillment Desk"),
	("Hemangi Adkar", 0, "Fulfillment Desk"),
	("Sachin Naik", 0, "Fulfillment Desk"),
	("Prajakta Shinde", 0, "Fulfillment Desk"),
	("Mrunmai Shirke", 0, "Fulfillment Desk"),
	("Sarvesh Jadhav", 0, "Fulfillment Desk"),
	("Mr.Vaibhav", 0, "Fulfillment Desk"),
	("Rakesh Jangid", 1, "Sales Team"),
	("Vipin Shukla", 1, "Rakesh Jangid"),
	("Ajay Yadav", 0, "Vipin Shukla"),
	("Manoj Singh", 0, "Vipin Shukla"),
	("Rohit Yadav", 0, "Vipin Shukla"),
	("Suraj Yadav", 0, "Vipin Shukla"),
	("Pankaj Patil", 1, "Rakesh Jangid"),
	("Mohammed Noman", 0, "Pankaj Patil"),
	("Akshay Ajit", 1, "Rakesh Jangid"),
	("Vijay Gaud", 0, "Akshay Ajit"),
	("Rageshwari Gaikwad", 0, "Rakesh Jangid"),
	("Direct", 0, "Sales Team"),
]

# Territory tree to mirror the staging export: (name, parent, is_group, manager).
TERRITORIES = [
	("All Territories", "", 1, ""),
	("South India", "All Territories", 1, "Kisan Dave"),
	("Andhra Pradesh", "South India", 0, "Kisan Dave"),
	("Karnataka", "South India", 0, "Kisan Dave"),
	("Kerala", "South India", 0, "Kisan Dave"),
	("Telangana", "South India", 0, "Kisan Dave"),
	("Puducherry", "South India", 0, "Kisan Dave"),
	("Rajasthan", "All Territories", 1, "Kisan Dave"),
	("North India", "All Territories", 1, "Kisan Dave"),
	("Haryana", "North India", 0, "Kisan Dave"),
	("Himachal Pradesh", "North India", 0, "Kisan Dave"),
	("Punjab", "North India", 0, "Kisan Dave"),
	("Uttar Pradesh", "North India", 0, "Kisan Dave"),
	("Delhi", "North India", 0, "Kisan Dave"),
	("Jammu and Kashmir", "North India", 0, "Kisan Dave"),
	("Chandigarh", "North India", 0, "Kisan Dave"),
	("East India", "All Territories", 1, "Kisan Dave"),
	("West Bengal", "East India", 0, "Kisan Dave"),
	("Odisha", "East India", 0, "Kisan Dave"),
	("Rest of India", "All Territories", 1, "Kisan Dave"),
	("Arunachal Pradesh", "Rest of India", 0, "Kisan Dave"),
	("Assam", "Rest of India", 0, "Kisan Dave"),
	("Bihar", "Rest of India", 0, "Kisan Dave"),
	("Chhattisgarh", "Rest of India", 0, "Kisan Dave"),
	("Goa", "Rest of India", 0, "Kisan Dave"),
	("Jharkhand", "Rest of India", 0, "Kisan Dave"),
	("Madhya Pradesh", "Rest of India", 0, "Kisan Dave"),
	("Manipur", "Rest of India", 0, "Kisan Dave"),
	("Meghalaya", "Rest of India", 0, "Kisan Dave"),
	("Mizoram", "Rest of India", 0, "Kisan Dave"),
	("Nagaland", "Rest of India", 0, "Kisan Dave"),
	("Sikkim", "Rest of India", 0, "Kisan Dave"),
	("Uttarakhand", "Rest of India", 0, "Kisan Dave"),
	("Tripura", "Rest of India", 0, "Kisan Dave"),
	("Export", "All Territories", 1, "Vicky Mahendru"),
	("Italy", "Export", 0, "Vicky Mahendru"),
	("Germany", "Export", 0, "Vicky Mahendru"),
	("UAE", "Export", 0, "Vicky Mahendru"),
	("Rest Of The World", "Export", 0, "Vicky Mahendru"),
	("Sri Lanka", "Export", 0, "Vicky Mahendru"),
	("Ethiopia", "Export", 0, "Vicky Mahendru"),
	("Nepal", "Export", 0, "Vicky Mahendru"),
	("Bahrain", "Export", 0, "Vicky Mahendru"),
	("Mexico", "Export", 0, "Vicky Mahendru"),
	("USA", "Export", 0, "Vicky Mahendru"),
	("Bangladesh", "Export", 0, "Vicky Mahendru"),
	("Oman", "Export", 0, "Vicky Mahendru"),
	("Qatar", "Export", 0, "Vicky Mahendru"),
	("U.K.", "Export", 0, "Vicky Mahendru"),
	("Malaysia", "Export", 0, "Vicky Mahendru"),
	("Mauritius", "Export", 0, "Vicky Mahendru"),
	("Turkey", "Export", 0, "Vicky Mahendru"),
	("Hong Kong", "Export", 0, "Vicky Mahendru"),
	("Iran", "Export", 0, "Vicky Mahendru"),
	("Vietnam", "Export", 0, "Vicky Mahendru"),
	("Gujarat", "All Territories", 1, "Pradip Shiroya"),
	("Gujarat Rest", "Gujarat", 0, "Pradip Shiroya"),
	("Rajkot", "Gujarat", 0, "Pradip Shiroya"),
	("Surat", "Gujarat", 0, "Pradip Shiroya"),
	("Maharashtra", "All Territories", 1, "Kisan Dave"),
	("Mumbai South", "Maharashtra", 0, "Kisan Dave"),
	("Mumbai North", "Maharashtra", 0, "Kisan Dave"),
	("Maharashtra Rest", "Maharashtra", 0, "Kisan Dave"),
	("Tamil Nadu", "All Territories", 1, "Kisan Dave"),
	("Coimbatore", "Tamil Nadu", 0, "Kisan Dave"),
	("Tamil Nadu Rest", "Tamil Nadu", 0, "Kisan Dave"),
	("Seepz", "All Territories", 1, "Vicky Mahendru"),
]

EMAIL_FIELD = "custom_email_id"


def clean_name(name):
	"""Drop a leading honorific (Mr./Ms./etc.) from a Sales Person name."""
	return re.sub(r"^(?:mr|mrs|ms|dr)\.\s*", "", name.strip(), flags=re.I)


def email_for(name):
	"""Distinct firstnamelastname@example.com from a Sales Person name."""
	local = re.sub(r"[^a-z0-9]", "", clean_name(name).lower())
	return f"{local}@example.com"


def execute():
	if not (frappe.db.exists("DocType", "Sales Person") and frappe.db.exists("DocType", "Territory")):
		return

	ensure_email_field()
	import_sales_persons()
	import_territories()
	frappe.db.commit()


def ensure_email_field():
	"""The Territory Manager (Sales Person) is matched to a CRM User via this field
	(see crm.api.sales_manager). On staging it comes from another app; create it
	locally if missing so the data and the approval resolver line up."""
	if frappe.db.has_column("Sales Person", EMAIL_FIELD):
		return
	create_custom_fields(
		{
			"Sales Person": [
				{
					"fieldname": EMAIL_FIELD,
					"label": "Email Id",
					"fieldtype": "Data",
					"options": "Email",
					"insert_after": "sales_person_name",
				}
			]
		},
		ignore_validate=True,
	)


def ensure_user(email, full_name):
	"""Create a CRM (System) User for the Sales Person's email so the territory
	manager resolves to a real user. Idempotent; no welcome email."""
	if not email or frappe.db.exists("User", email):
		return
	parts = clean_name(full_name).split()
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": parts[0] if parts else email,
			"last_name": " ".join(parts[1:]) or None,
			"user_type": "System User",
			"send_welcome_email": 0,
		}
	)
	user.insert(ignore_permissions=True)
	user.add_roles("Sales User")


def import_sales_persons():
	insert_tree(
		SALES_PERSONS,
		doctype="Sales Person",
		name_of=lambda row: row[0],
		parent_of=lambda row: row[2],
		build=lambda row: {
			"doctype": "Sales Person",
			"sales_person_name": row[0],
			"is_group": row[1],
			"parent_sales_person": row[2] or None,
			EMAIL_FIELD: email_for(row[0]),
		},
		before=lambda row: ensure_user(email_for(row[0]), row[0]),
		drop_parent=lambda values: values.pop("parent_sales_person", None),
	)


def import_territories():
	insert_tree(
		TERRITORIES,
		doctype="Territory",
		name_of=lambda row: row[0],
		parent_of=lambda row: row[1],
		build=lambda row: {
			"doctype": "Territory",
			"territory_name": row[0],
			"parent_territory": row[1] or None,
			"is_group": row[2],
			"territory_manager": row[3] or None,
		},
		drop_parent=lambda values: values.pop("parent_territory", None),
	)


def insert_tree(rows, doctype, name_of, parent_of, build, drop_parent, before=None):
	"""Insert tree rows in any order: a row is created only once its parent exists.
	Rows whose parent never appears are inserted as roots in a final pass."""
	remaining = list(rows)
	while remaining:
		progress = False
		for row in list(remaining):
			parent = parent_of(row)
			if parent and not frappe.db.exists(doctype, parent):
				continue
			remaining.remove(row)
			progress = True
			if before:
				before(row)
			if not frappe.db.exists(doctype, name_of(row)):
				frappe.get_doc(build(row)).insert(ignore_permissions=True)
		if progress:
			continue
		# orphans — parent missing from the data, insert detached from the tree
		for row in list(remaining):
			remaining.remove(row)
			if before:
				before(row)
			if not frappe.db.exists(doctype, name_of(row)):
				values = build(row)
				drop_parent(values)
				frappe.get_doc(values).insert(ignore_permissions=True)
		break
