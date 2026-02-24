// QCTest — client-side form controller

frappe.ui.form.on("QCTest", {
	refresh(frm) {
		if (!frm.is_new()) {
			const testDate = frm.doc.test_date;
			if (testDate) {
				const days = frappe.datetime.get_diff(frappe.datetime.nowdate(), testDate);
				if (days > 7) {
					frm.dashboard.add_comment(
						__("Warning: This QC test is {0} days old. Season policy requires tests within 7 days.", [days]),
						"orange",
						true
					);
				}
			}
		}
	},

	// Auto-fill site from the linked Lot when a Lot is selected
	lot(frm) {
		if (frm.doc.lot) {
			frappe.db.get_value("Lot", frm.doc.lot, "site", (r) => {
				if (r?.site) {
					frm.set_value("site", r.site);
				}
			});
		}
	},
});
