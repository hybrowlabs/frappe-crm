from crm.fcrm.doctype.crm_organization.crm_organization import update_repeat_business_signals


def execute():
	# Backfill last_order (and the two order-signal checkboxes) for existing organizations.
	update_repeat_business_signals()
