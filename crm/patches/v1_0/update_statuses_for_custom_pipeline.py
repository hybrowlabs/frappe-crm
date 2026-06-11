import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Custom Precious Alloys pipeline layered on the official statuses.
# Non-destructive: existing status PKs are never renamed or deleted. We only
# set `label` (display name) + `position`, and create the brand-new stages.
# See STATUS_MIGRATION.md for the full before -> expected -> final mapping.

# name (PK) = official value, kept as-is. `new` rows are created.
DEAL_STATUSES = [
	{"name": "Req. Discussion", "label": "Req. Discussion", "position": 1,
		"new": True, "color": "gray", "type": "Open", "probability": 5},
	{"name": "Qualification", "label": "Qualified", "position": 2},
	{"name": "Demo/Making", "label": "Tech Evaluation", "position": 3},
	{"name": "Retrial", "label": "Retrial", "position": 4,
		"new": True, "color": "red", "type": "Ongoing", "probability": 30},
	{"name": "Evaluation Completed", "label": "Evaluation Completed", "position": 5,
		"new": True, "color": "green", "type": "Ongoing", "probability": 50},
	{"name": "Proposal/Quotation", "label": "Proposal/Quotation", "position": 6},
	{"name": "Negotiation", "label": "Negotiation", "position": 7},
	{"name": "Ready to Close", "label": "Ready to Close", "position": 8},
	{"name": "Won", "label": "Won", "position": 9},
	{"name": "Lost", "label": "Lost", "position": 10},
]

# Lead status: only labels change — existing sequence/positions are left untouched.
LEAD_STATUSES = [
	{"name": "New", "label": "New"},
	{"name": "Contacted", "label": "Contacted"},
	{"name": "Nurture", "label": "Nurturing"},
	{"name": "Converted", "label": "Converted"},
	{"name": "Junk", "label": "Not Relevant"},
	{"name": "Qualified", "label": "Qualified"},
	{"name": "Unqualified", "label": "Unqualified"},
]


def execute():
	ensure_label_field()
	apply_statuses("CRM Deal Status", "deal_status", DEAL_STATUSES)
	apply_statuses("CRM Lead Status", "lead_status", LEAD_STATUSES)
	frappe.clear_cache()


def ensure_label_field():
	"""Create the `label` field only where it is missing (idempotent)."""
	custom_fields = {}
	for doctype, after in (("CRM Deal Status", "deal_status"), ("CRM Lead Status", "lead_status")):
		if not frappe.db.has_column(doctype, "label"):
			custom_fields[doctype] = [
				{
					"fieldname": "label",
					"label": "Label",
					"fieldtype": "Data",
					"translatable": 1,
					"insert_after": after,
				}
			]
	if custom_fields:
		create_custom_fields(custom_fields, ignore_validate=True)


def apply_statuses(doctype, name_field, statuses):
	has_probability = frappe.get_meta(doctype).has_field("probability")

	for s in statuses:
		if frappe.db.exists(doctype, s["name"]):
			# keep PK / color / type / probability as-is; set label, and
			# position only when explicitly given (lead sequence is untouched)
			values = {"label": s["label"]}
			if s.get("position") is not None:
				values["position"] = s["position"]
			frappe.db.set_value(doctype, s["name"], values)
		elif s.get("new"):
			doc = frappe.new_doc(doctype)
			doc.set(name_field, s["name"])
			doc.label = s["label"]
			doc.position = s["position"]
			doc.color = s.get("color", "gray")
			doc.type = s.get("type", "Open")
			if has_probability and s.get("probability") is not None:
				doc.probability = s["probability"]
			doc.insert(ignore_permissions=True)
