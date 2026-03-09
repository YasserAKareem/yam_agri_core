// Copyright (c) 2026, YAM Agri Core and contributors
// For license information, please see license.txt

frappe.ui.form.on("Investment Opportunity", {
	refresh: function(frm) {
		// Add custom button for AI analysis
		if (!frm.is_new() && frm.doc.gtd_status !== "Completed") {
			frm.add_custom_button(__("Get AI Analysis"), function() {
				frappe.call({
					method: "get_ai_analysis",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Analyzing opportunity with AI..."),
					callback: function(r) {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: __("AI analysis completed successfully"),
								indicator: "green"
							});
							frm.reload_doc();
						} else {
							frappe.show_alert({
								message: __("AI analysis failed: {0}", [r.message.error || "Unknown error"]),
								indicator: "red"
							});
						}
					}
				});
			}, __("AI Tools"));
		}

		// Add GTD workflow buttons
		if (frm.doc.gtd_status === "Captured") {
			frm.add_custom_button(__("Clarify"), function() {
				frm.set_value("gtd_status", "Clarified");
			}, __("GTD Workflow"));
		}

		if (frm.doc.gtd_status === "Clarified") {
			frm.add_custom_button(__("Set Next Action"), function() {
				frm.set_value("gtd_status", "Next Action");
				frm.scroll_to_field("next_action");
			}, __("GTD Workflow"));

			frm.add_custom_button(__("Create Project"), function() {
				frm.set_value("gtd_status", "Project");
				frm.scroll_to_field("next_action");
			}, __("GTD Workflow"));

			frm.add_custom_button(__("Move to Someday/Maybe"), function() {
				frm.set_value("gtd_status", "Someday-Maybe");
			}, __("GTD Workflow"));
		}

		// Color-code based on priority
		if (frm.doc.priority === "High") {
			frm.dashboard.set_headline_alert(__("High Priority Opportunity"), "red");
		}

		// Warning for high risk
		if (frm.doc.risk_level === "Critical" || frm.doc.risk_level === "High") {
			frm.dashboard.set_headline_alert(
				__("Risk Level: {0}", [frm.doc.risk_level]),
				frm.doc.risk_level === "Critical" ? "red" : "orange"
			);
		}
	},

	gtd_status: function(frm) {
		// Clear next action fields if not needed
		if (frm.doc.gtd_status !== "Next Action" && frm.doc.gtd_status !== "Project") {
			frm.set_value("next_action", "");
			frm.set_value("next_action_owner", "");
			frm.set_value("gtd_context", "");
		}
	},

	investment_size: function(frm) {
		// Show investment category
		if (frm.doc.investment_size) {
			let category;
			if (frm.doc.investment_size < 1000000) {
				category = __("Small Investment (< $1M)");
			} else if (frm.doc.investment_size < 10000000) {
				category = __("Medium Investment ($1M - $10M)");
			} else {
				category = __("Large Investment (> $10M)");
			}
			frappe.show_alert({
				message: category,
				indicator: "blue"
			});
		}
	},

	expected_jobs: function(frm) {
		// Alert for significant job creation
		if (frm.doc.expected_jobs && frm.doc.expected_jobs >= 100) {
			frappe.show_alert({
				message: __("Significant job creation opportunity: {0} jobs", [frm.doc.expected_jobs]),
				indicator: "green"
			});
		}
	}
});
