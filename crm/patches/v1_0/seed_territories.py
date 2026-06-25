import frappe

TERRITORIES = [
	"Mumbai",
	"Gujarat",
	"Rajasthan",
	"Delhi",
	"Punjab",
	"UP",
	"Kolkata",
	"Hyderabad",
	"Coimbatore",
	"Bangalore",
	"Chennai",
	"Kerala",
	"Calicut",
	"Thrissur",
]


def execute():
	if not frappe.db.exists("DocType", "Territory"):
		return

	parent = frappe.db.get_value("Territory", {"is_group": 1}, "name")

	for territory in TERRITORIES:
		if frappe.db.exists("Territory", territory):
			continue
		frappe.get_doc(
			{
				"doctype": "Territory",
				"territory_name": territory,
				"parent_crm_territory": parent,
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()
