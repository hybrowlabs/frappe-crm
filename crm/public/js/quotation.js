// When a Quotation is created from CRM (custom_* fields prefilled in the URL),
// auto-add the relevant organization's previously ordered items as rows with qty 0.
// URL query params are applied on refresh, not onload, so run here.
frappe.ui.form.on('Quotation', {
	refresh(frm) {
		if (!frm.is_new() || frm.__crm_items_prefilled) return

		// Created from a CRM Deal — items come from the deal's organization.
		if (frm.doc.custom_deal) {
			frm.__crm_items_prefilled = true
			prefill_items(frm, 'crm.api.sales_order.get_previous_order_items', {
				deal: frm.doc.custom_deal,
			})
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
			prefill_items(
				frm,
				'crm.api.sales_order.get_previous_order_items_for_customer',
				{ customer: frm.doc.party_name },
			)
		}
	},
})

function prefill_items(frm, method, args) {
	frappe.call({
		method,
		args,
		callback(r) {
			if (!(r.message || []).length) return
			frm.clear_table('items')
			;(r.message || []).forEach((item_code) => {
				const row = frm.add_child('items', { item_code, qty: 0 })
				frm.script_manager
					.trigger('item_code', row.doctype, row.name)
					.then(() => {
						frappe.model.set_value(row.doctype, row.name, 'qty', 0)
					})
			})
			frm.refresh_field('items')
		},
	})
}
