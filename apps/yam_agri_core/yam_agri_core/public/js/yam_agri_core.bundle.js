(() => {
	const path = window.location.pathname || "";
	if (!path.startsWith("/desk/")) {
		return;
	}

	const match = path.match(/^\/desk\/([^/]+)(?:\/view\/list)?\/?$/i);
	if (!match || !match[1]) {
		return;
	}

	const firstSegment = decodeURIComponent(match[1]);
	const reservedDeskPages = new Set([
		"workspace",
		"modules",
		"list",
		"Form",
		"report",
		"query-report",
		"print",
		"background_jobs",
		"backups",
		"users",
		"role",
		"setup-wizard",
	]);
	if (reservedDeskPages.has(firstSegment)) {
		return;
	}

	const appRoute = `/app/${firstSegment.toLowerCase()}`;
	if (window.location.pathname !== appRoute) {
		window.location.replace(appRoute + window.location.search + window.location.hash);
	}
})();

(() => {
	if (typeof frappe === "undefined" || !frappe.ui || !frappe.ui.form) {
		return;
	}

	const openChatDialog = (frm) => {
		const dialog = new frappe.ui.Dialog({
			title: __("AI Assistant Chat"),
			fields: [
				{
					fieldname: "message",
					label: __("Message"),
					fieldtype: "Small Text",
					reqd: 1,
				},
			],
			primary_action_label: __("Send"),
			primary_action(values) {
				frappe.call({
					method: "yam_agri_core.yam_agri_core.api.ai_assist.chat_with_lot_assistant",
					args: {
						lot: frm.doc.name,
						message: values.message,
						filters_json: JSON.stringify({}),
						history_json: JSON.stringify([]),
					},
					freeze: true,
					freeze_message: __("Generating assistive chat response..."),
					callback(r) {
						const msg = r.message || {};
						if (!msg.ok) {
							frappe.msgprint({
								title: __("AI Assistant Chat"),
								message: __("No response available."),
								indicator: "orange",
							});
							return;
						}

						const warning = msg.warning
							? `<div style="margin-bottom:8px;color:#b54708;">${frappe.utils.escape_html(msg.warning)}</div>`
							: "";
						const reply = frappe.utils.escape_html(msg.reply || "");

						frappe.msgprint({
							title: __("AI Assistant Chat"),
							message:
								warning +
								`<div><strong>${__("Assistive only — Review required")}</strong></div>` +
								`<div style="margin-top:8px;white-space:pre-wrap;">${reply}</div>`,
							wide: true,
						});

						dialog.hide();
					},
				});
			},
		});

		dialog.show();
	};

	frappe.ui.form.on("Lot", {
		refresh(frm) {
			if (frm.is_new()) {
				return;
			}

			if (!frm.__yam_ai_popup_bound) {
				frm.add_custom_button(__("AI Chat Popup"), () => openChatDialog(frm));
				frm.__yam_ai_popup_bound = true;
			}
		},
	});
})();
