// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Custom Settings", {
	setup(frm) {
		frm.$wrapper.on("click", "[data-select-warehouses]", (e) => {
			e.preventDefault();
			const cdn = $(e.currentTarget).attr("data-select-warehouses");
			select_child_warehouses("CRM Branch Stock Warehouse", cdn);
		});
	},

	refresh(frm) {
		// A grid Button shows only while its row is being edited; draw one in
		// the static cell too so every row shows it.
		frm.fields_dict.branch_stock_warehouses.grid.update_docfield_property(
			"select_warehouses",
			"formatter",
			(value, df, options, doc) =>
				`<button class="btn btn-xs btn-default" data-select-warehouses="${doc.name}">
					${__("Select Warehouses")}
				</button>`
		);
		// One line per warehouse is cut off in the grid cell; list them inline.
		frm.fields_dict.branch_stock_warehouses.grid.update_docfield_property(
			"child_warehouses",
			"formatter",
			(value) =>
				frappe.utils.escape_html((value || "").split("\n").filter(Boolean).join(", "))
		);
		frm.refresh_field("branch_stock_warehouses");
	},

	holiday_list(frm) {
		if (!frm.doc.holiday_list) {
			frm.clear_table("holiday_list_table");
			frm.refresh_field("holiday_list_table");
			return;
		}

		const holiday_list = frm.doc.holiday_list;
		frappe.call({
			method: "crm.fcrm.doctype.crm_custom_settings.crm_custom_settings.get_holiday_list_dates",
			args: { holiday_list },
			callback(response) {
				// Ignore a response for a list that was changed while the request was running.
				if (frm.doc.holiday_list !== holiday_list) return;

				// A newly selected list replaces the dates copied from the previous list.
				frm.clear_table("holiday_list_table");

				(response.message || []).forEach((date) => {
					frm.add_child("holiday_list_table", {
						date,
					});
				});

				frm.refresh_field("holiday_list_table");
			},
		});
	},
});

frappe.ui.form.on("CRM Branch Stock Warehouse", {
	parent_warehouse(frm, cdt, cdn) {
		// The ticked children belong to the old parent.
		frappe.model.set_value(cdt, cdn, "child_warehouses", "");
	},

	select_warehouses(frm, cdt, cdn) {
		select_child_warehouses(cdt, cdn);
	},
});

function select_child_warehouses(cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.parent_warehouse) {
		frappe.msgprint(__("Select a Parent Warehouse first."));
		return;
	}

	frappe.call({
		method: "crm.fcrm.doctype.crm_custom_settings.crm_custom_settings.get_child_warehouses",
		args: { parent_warehouse: row.parent_warehouse },
		callback(response) {
			const warehouses = response.message || [];
			if (!warehouses.length) {
				frappe.msgprint(
					__("{0} has no warehouses under it.", [row.parent_warehouse])
				);
				return;
			}

			const ticked = (row.child_warehouses || "").split("\n").filter(Boolean);
			const dialog = new frappe.ui.Dialog({
				title: __("Child Warehouses of {0}", [row.parent_warehouse]),
				fields: [
					{
						fieldname: "warehouses",
						fieldtype: "MultiCheck",
						columns: 1,
						select_all: true,
						options: warehouses.map((name) => ({
							label: name,
							value: name,
							checked: ticked.includes(name),
						})),
					},
				],
				primary_action_label: __("Set"),
				primary_action(values) {
					frappe.model.set_value(
						cdt,
						cdn,
						"child_warehouses",
						(values.warehouses || []).join("\n")
					);
					dialog.hide();
				},
			});
			dialog.show();
		},
	});
}
