// When a Quotation is created from CRM (custom_* fields prefilled in the URL),
// auto-add the relevant organization's previously ordered items as rows with qty 0.
// URL query params are applied on refresh, not onload, so run here.
frappe.ui.form.on('Quotation', {
	refresh(frm) {
		if (!frm.is_new() || frm.__crm_items_prefilled) return

		// Created from a CRM Deal — items + sales person come from the deal.
		if (frm.doc.custom_deal) {
			frm.__crm_items_prefilled = true
			prefill_items(frm, 'crm.api.sales_order.get_previous_order_items', {
				deal: frm.doc.custom_deal,
			})
			set_sales_person(frm, { crm_deal: frm.doc.custom_deal })
			return
		}

		// Repeat order from an Organization — no deal; items come from the
		// customer's linked organization. Keyed on quotation_to=Customer +
		// custom_created_from_crm (set by get_repeat_order_quotation_url).
		if (
			frm.doc.custom_created_from_crm &&
			frm.doc.quotation_to === 'Customer' &&
			frm.doc.party_name
		) {
			frm.__crm_items_prefilled = true
			// The repeat-order modal passes an explicit selection of item codes on the
			// (hidden) custom_crm_items field — Frappe keeps it on the new doc because
			// it is a real field, unlike a bare URL query param. Use it directly, then
			// clear it so it isn't persisted. Otherwise fall back to all items.
			// No deal here, so the sales person is matched from the current user.
			set_sales_person(frm, {})
			const selected = parse_selected_items(frm.doc.custom_crm_items)
			if (selected) {
				frm.set_value('custom_crm_items', '')
				set_items(frm, selected)
				return
			}
			prefill_items(
				frm,
				'crm.api.sales_order.get_previous_order_items_for_customer',
				{ customer: frm.doc.party_name },
			)
		}
	},
})

// Prefill custom_sale_by with the Sales Person (matched by email) for this quote:
// the deal's assignee when crm_deal is given, else the current user. Server-only
// field, so guarded on its presence. Left blank when nothing matches.
function set_sales_person(frm, args) {
	if (!frm.get_docfield('custom_sale_by')) return
	frappe.call({
		method:
			'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotation_sales_person',
		args,
		callback(r) {
			if (r.message) frm.set_value('custom_sale_by', r.message)
		},
	})
}

function parse_selected_items(raw) {
	if (!raw) return null
	try {
		const list = JSON.parse(raw)
		return Array.isArray(list) && list.length ? list : null
	} catch (e) {
		return null
	}
}

function prefill_items(frm, method, args) {
	frappe.call({
		method,
		args,
		callback(r) {
			set_items(frm, r.message || [])
		},
	})
}

function set_items(frm, item_codes) {
	if (!(item_codes || []).length) return
	frm.clear_table('items')
	item_codes.forEach((item_code) => {
		const row = frm.add_child('items', { item_code, qty: 0 })
		frm.script_manager
			.trigger('item_code', row.doctype, row.name)
			.then(() => {
				frappe.model.set_value(row.doctype, row.name, 'qty', 0)
			})
	})
	frm.refresh_field('items')
}
