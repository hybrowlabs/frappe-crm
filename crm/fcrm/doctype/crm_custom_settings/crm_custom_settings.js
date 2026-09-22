// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Custom Settings", {
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
