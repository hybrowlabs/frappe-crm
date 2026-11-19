# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Customer -> CRM Organization resolution for the ERPNext integration.

ERPNext's ``Customer`` is the party master, while CRM keeps its own
``CRM Organization``. With no link between the two the same company exists
twice, and a Deal raised against an already known Customer cannot reuse
anything ERPNext holds about it.

The link is many-to-one and lives on the Customer side, in
``Customer.crm_organization``. One company commonly has several Customer
records - separate units of a group, each with its own GSTIN - while
``CRM Organization`` is autonamed from ``organization_name`` and so holds one
record per name. Those Customers therefore share a single Organization, and
nothing on the Organization points back at one Customer, because no single one
would be right; reach the Customer through the Deal instead.

Contacts need no bridge. CRM and ERPNext already share the same ``Contact``
records; they only lack the ``Customer`` link row, which
:func:`link_contacts_to_customer` adds.

Everything here is local-site only. When ERPNext runs on a separate site the
Customer is remote and cannot be the target of a local link, so each entry
point returns without guessing.
"""

import frappe


def _has_local_customer() -> bool:
	"""Is there a local ERPNext Customer master to link against?"""
	settings = frappe.get_cached_doc("ERPNext CRM Settings")
	if not settings.enabled or settings.is_erpnext_in_different_site:
		return False
	return bool(frappe.db.exists("DocType", "Customer"))


def _stamp(customer: str, organization: str) -> None:
	"""Point the Customer at its Organization, leaving timestamps alone."""
	# The field only exists once the integration has created its custom fields;
	# a site mid-setup should degrade quietly rather than fail a deal save.
	if not frappe.get_meta("Customer").has_field("crm_organization"):
		return
	frappe.db.set_value(
		"Customer", customer, "crm_organization", organization, update_modified=False
	)


def get_organization_for_customer(customer: str, create: bool = False) -> str | None:
	"""The CRM Organization this Customer belongs to, or None.

	Resolution order: the Organization already recorded on the Customer, then one
	of exactly the Customer's name, then - only when ``create`` is set - a new
	Organization built from the Customer.

	Only exact name matches are reused. A near match is a judgement call that
	belongs to a person, not to a save hook.
	"""
	if not customer or not _has_local_customer():
		return None

	customer_name = frappe.db.get_value("Customer", customer, "customer_name")
	if customer_name is None:
		return None

	if frappe.get_meta("Customer").has_field("crm_organization"):
		organization = frappe.db.get_value("Customer", customer, "crm_organization")
		if organization and frappe.db.exists("CRM Organization", organization):
			return organization

	# Organizations are autonamed from organization_name, so an exact name match
	# is the only candidate there can be, and it is the record this Customer
	# should share. Several Customers of one group legitimately land here.
	if customer_name and frappe.db.exists("CRM Organization", customer_name):
		# Record the match only when resolving for real. A plain lookup answers a
		# dialog that is still open and may yet be cancelled, and must not leave a
		# write behind on an existing Customer.
		if create:
			_stamp(customer, customer_name)
		return customer_name

	if not create:
		return None

	return _create_organization_for_customer(customer, customer_name)


def _create_organization_for_customer(customer: str, customer_name: str | None = None) -> str:
	doc = frappe.get_doc("Customer", customer)

	organization = frappe.new_doc("CRM Organization")
	organization.organization_name = customer_name or doc.customer_name or customer
	organization.website = doc.get("website")
	organization.currency = doc.get("default_currency")

	# CRM keeps its own Territory and Industry trees, separate from ERPNext's.
	# Copy a value only when the CRM side has that record, else Link validation
	# rejects it.
	if doc.get("territory") and frappe.db.exists("CRM Territory", doc.territory):
		organization.territory = doc.territory
	if doc.get("industry") and frappe.db.exists("CRM Industry", doc.industry):
		organization.industry = doc.industry
	if doc.get("customer_primary_address") and frappe.db.exists(
		"Address", doc.customer_primary_address
	):
		organization.address = doc.customer_primary_address

	organization.insert(ignore_permissions=True)
	_stamp(customer, organization.name)
	return organization.name


def set_organization_on_customer(customer: str, organization: str) -> None:
	"""Back-link a Customer that was just created out of a Deal's Organization."""
	if not customer or not organization or not _has_local_customer():
		return
	if not frappe.db.exists("CRM Organization", organization):
		return
	_stamp(customer, organization)


@frappe.whitelist()
def get_deal_defaults_from_customer(customer: str) -> dict:
	"""Deal field values derived from an existing Customer.

	Read-only on purpose: it is called while a Create Deal dialog is still open,
	so it reports the Organization only when one already exists and never brings
	one into being. The Organization is resolved for real on save.
	"""
	if not customer or not _has_local_customer():
		return {}
	if not frappe.has_permission("Customer", "read", customer):
		return {}

	doc = frappe.db.get_value(
		"Customer",
		customer,
		[
			"customer_name",
			"website",
			"territory",
			"industry",
			"default_currency",
			"customer_primary_contact",
		],
		as_dict=True,
	)
	if not doc:
		return {}

	defaults = {
		"organization": get_organization_for_customer(customer, create=False),
		"organization_name": doc.customer_name,
		"website": doc.website,
		"currency": doc.default_currency,
	}

	# CRM's Territory and Industry are separate trees from ERPNext's; only offer a
	# value the CRM side can actually store.
	if doc.territory and frappe.db.exists("CRM Territory", doc.territory):
		defaults["territory"] = doc.territory
	if doc.industry and frappe.db.exists("CRM Industry", doc.industry):
		defaults["industry"] = doc.industry

	contacts = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Customer",
			"link_name": customer,
			"parenttype": "Contact",
		},
		pluck="parent",
	)
	defaults["contacts"] = contacts

	primary = doc.customer_primary_contact or (contacts[0] if len(contacts) == 1 else None)
	if primary and frappe.db.exists("Contact", primary):
		person = frappe.db.get_value(
			"Contact",
			primary,
			["salutation", "first_name", "last_name", "email_id", "mobile_no", "gender"],
			as_dict=True,
		)
		defaults["contact"] = primary
		defaults.update(
			{
				"salutation": person.salutation,
				"first_name": person.first_name,
				"last_name": person.last_name,
				"email": person.email_id,
				"mobile_no": person.mobile_no,
				"gender": person.gender,
			}
		)

	return {key: value for key, value in defaults.items() if value not in (None, "")}


def link_contacts_to_customer(contacts, customer: str) -> int:
	"""Add the ``Customer`` link row to each Contact that lacks it.

	CRM and ERPNext share the same Contact records, so nothing is copied here -
	only the Dynamic Link that makes a Contact selectable on the Customer's
	ERPNext transactions. Idempotent; returns how many Contacts were linked.
	"""
	if not customer or not _has_local_customer():
		return 0
	if not frappe.db.exists("Customer", customer):
		return 0

	linked = 0
	for name in {contact for contact in contacts if contact}:
		if not frappe.db.exists("Contact", name):
			continue

		contact = frappe.get_doc("Contact", name)
		if contact.has_link("Customer", customer):
			continue

		contact.append("links", {"link_doctype": "Customer", "link_name": customer})
		contact.flags.ignore_mandatory = True
		contact.save(ignore_permissions=True)
		linked += 1

	return linked
