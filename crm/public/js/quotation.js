// When a Quotation is created from a CRM Deal (custom_deal prefilled in the URL),
// auto-add the deal organization's previously ordered items as rows with qty 0.
// URL query params (custom_deal) are applied on refresh, not onload, so run here.
frappe.ui.form.on('Quotation', {
	refresh(frm) {
		if (!frm.is_new() || !frm.doc.custom_deal) return
		if (frm.__crm_items_prefilled) return
		frm.__crm_items_prefilled = true

		frappe.call({
			method: 'crm.api.sales_order.get_previous_order_items',
			args: { deal: frm.doc.custom_deal },
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
	},
})
