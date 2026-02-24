// Site — client-side form controller

frappe.ui.form.on("Site", {
	refresh(frm) {
		if (!frm.is_new()) {
			// Quick link to open all Lots for this Site
			frm.add_custom_button(__("View Lots"), () => {
				frappe.set_route("List", "Lot", { site: frm.doc.name });
			}, __("Navigate"));

			// Quick link to Storage Bins
			frm.add_custom_button(__("View Storage Bins"), () => {
				frappe.set_route("List", "StorageBin", { site: frm.doc.name });
			}, __("Navigate"));
		}
	},
});
