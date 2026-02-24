// Lot — client-side form controller
// Frappe calls frappe.ui.form.on("<DocType>", { event: handler })

frappe.ui.form.on("Lot", {
	// Store the original status when the form loads so we can roll back safely
	onload(frm) {
		frm._yam_original_status = frm.doc.status;
	},

	// Fired when the form is first loaded/refreshed
	refresh(frm) {
		// Track status for rollback in the status handler
		frm._yam_original_status = frm.doc.status;

		// Show a "Dispatch" action button only for QA Managers when the lot is ready
		if (frm.doc.status === "For Dispatch" && frappe.user.has_role("QA Manager")) {
			frm.add_custom_button(__("Mark Dispatched"), () => {
				frappe.confirm(
					__("Mark Lot {0} as Dispatched?", [frm.doc.name]),
					() => {
						frm.set_value("status", "Dispatched");
						frm.save();
					}
				);
			});
		}

		// Show linked QC tests count in the dashboard area
		if (!frm.is_new()) {
			frm.dashboard.add_comment(
				__("Check the QC Tests and Certificates tabs for traceability details."),
				"blue",
				true
			);
		}
	},

	// Fired when the status field changes
	status(frm) {
		if (["Accepted", "Rejected"].includes(frm.doc.status) && !frappe.user.has_role("QA Manager")) {
			frappe.msgprint({
				title: __("Permission Required"),
				message: __("Only a QA Manager may set Lot status to {0}.", [frm.doc.status]),
				indicator: "red",
			});
			// Roll back to the last known safe status captured in onload/refresh
			frm.set_value("status", frm._yam_original_status || "Draft");
		}
	},

	// Auto-fill site from the user's default Site permission when creating new
	before_save(frm) {
		if (frm.is_new() && !frm.doc.site) {
			// Use frappe.perm.get_user_permissions() — available in Frappe 14+
			const perms =
				typeof frappe.perm !== "undefined" && typeof frappe.perm.get_user_permissions === "function"
					? frappe.perm.get_user_permissions()
					: null;
			const allowed = perms && perms["Site"];
			if (allowed && allowed.length === 1) {
				frm.set_value("site", allowed[0].doc);
			}
		}
	},
});
