function yamGetAiPromptTemplates() {
	return new Promise((resolve) => {
		frappe.call({
			method: "yam_agri_core.yam_agri_core.api.ai_assist.get_ai_prompt_templates",
			callback(r) {
				const data = (r && r.message) || {};
				resolve(Array.isArray(data.templates) ? data.templates : []);
			},
			error() {
				resolve([]);
			},
		});
	});
}

function yamGetAiModels() {
	return new Promise((resolve) => {
		frappe.call({
			method: "yam_agri_core.yam_agri_core.api.ai_assist.get_ai_available_models",
			callback(r) {
				const data = (r && r.message) || {};
				const models = Array.isArray(data.models) ? data.models : [];
				resolve({ models, defaultModel: data.default_model || "" });
			},
			error() {
				resolve({ models: [], defaultModel: "" });
			},
		});
	});
}

function yamSubmitAiDecision(interactionLog, decision) {
	if (!interactionLog) {
		return;
	}

	frappe.call({
		method: "yam_agri_core.yam_agri_core.api.ai_assist.set_ai_interaction_decision",
		args: {
			interaction_log: interactionLog,
			decision,
		},
		callback(r) {
			const data = (r && r.message) || {};
			if (data.ok) {
				frappe.show_alert({
					message: __("AI decision logged: {0}", [data.decision || decision]),
					indicator: "green",
				});
				return;
			}

			frappe.show_alert({
				message: __("AI decision log update is not available."),
				indicator: "orange",
			});
		},
		error() {
			frappe.show_alert({
				message: __("Could not update AI decision log."),
				indicator: "red",
			});
		},
	});
}

function yamPromptAiDecision(interactionLog) {
	if (!interactionLog) {
		return;
	}

	frappe.confirm(
		__("Do you accept this AI suggestion?"),
		() => yamSubmitAiDecision(interactionLog, "accepted"),
		() => yamSubmitAiDecision(interactionLog, "rejected")
	);
}

async function yamOpenLotAiChatDialog(frm) {
	if (frm.is_new()) {
		frappe.msgprint({
			title: __("AI Assistant Chat"),
			message: __("Please save the Lot first, then use AI actions."),
			indicator: "orange",
		});
		return;
	}

	const [templates, modelPayload] = await Promise.all([yamGetAiPromptTemplates(), yamGetAiModels()]);
	const modelOptions = modelPayload.models.length ? modelPayload.models.join("\n") : "";
	const defaultModel = modelPayload.defaultModel || modelPayload.models[0] || "";
	const templateOptions = templates.map((item) => item.template_id).join("\n");
	const defaultTemplate = templates.find((item) => item.template_id === "lot_compliance")
		? "lot_compliance"
		: templates.length
			? templates[0].template_id
			: "";

	const dialog = new frappe.ui.Dialog({
		title: __("AI Assistant Chat"),
		fields: [
			{
				fieldname: "message",
				label: __("Message"),
				fieldtype: "Small Text",
				reqd: 1,
			},
			{
				fieldname: "model",
				label: __("Model"),
				fieldtype: "Select",
				options: modelOptions,
				default: defaultModel,
			},
			{
				fieldname: "template_id",
				label: __("Prompt Template"),
				fieldtype: "Select",
				options: templateOptions,
				default: defaultTemplate,
			},
			{
				fieldname: "include_expired_certificates",
				label: __("Include Expired Certificates"),
				fieldtype: "Check",
				default: 0,
			},
			{
				fieldname: "include_closed_nonconformance",
				label: __("Include Closed Nonconformance"),
				fieldtype: "Check",
				default: 0,
			},
			{
				fieldname: "from_date",
				label: __("From Date"),
				fieldtype: "Date",
			},
			{
				fieldname: "to_date",
				label: __("To Date"),
				fieldtype: "Date",
			},
		],
		primary_action_label: __("Send"),
		primary_action(values) {
			const filters = {
				include_expired_certificates: !!values.include_expired_certificates,
				include_closed_nonconformance: !!values.include_closed_nonconformance,
				from_date: values.from_date || "",
				to_date: values.to_date || "",
			};

			frappe.call({
				method: "yam_agri_core.yam_agri_core.api.ai_assist.chat_with_lot_assistant",
				args: {
					lot: frm.doc.name,
					message: values.message,
					model: values.model || "",
					template_id: values.template_id || "",
					filters_json: JSON.stringify(filters),
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
					const provider = frappe.utils.escape_html(msg.provider || "");
					const model = frappe.utils.escape_html((msg.gateway && msg.gateway.model) || values.model || "");
					const templateId = frappe.utils.escape_html(
						(msg.gateway && msg.gateway.template_id) || values.template_id || ""
					);
					const redactionCount = Number((msg.gateway && msg.gateway.redaction_count) || 0);
					const interactionLog = frappe.utils.escape_html(msg.interaction_log || "");

					frappe.msgprint({
						title: __("AI Assistant Chat"),
						message:
							warning +
							`<div><strong>${__("Assistive only - Review required")}</strong></div>` +
							`<div style="margin-top:8px;white-space:pre-wrap;">${reply}</div>` +
							`<hr>` +
							`<div>${__("Provider")}: ${provider}</div>` +
							`<div>${__("Model")}: ${model || __("Default")}</div>` +
							`<div>${__("Template")}: ${templateId || __("Default")}</div>` +
							`<div style="margin-top:8px;color:#667085;">${__("Redactions")}: ${redactionCount}</div>` +
							`<div style="color:#667085;">${__("Interaction Log")}: ${interactionLog || __("Not available")}</div>`,
						wide: true,
					});

					dialog.hide();
					yamPromptAiDecision(msg.interaction_log || "");
				},
			});
		},
	});

	dialog.show();
}

frappe.ui.form.on("Lot", {
	onload(frm) {
		frm._yam_original_status = frm.doc.status;
	},

	refresh(frm) {
		frm._yam_original_status = frm.doc.status;

		if (frm.is_new()) {
			frm.set_intro(__("Save this Lot first, then use AI Compliance Suggestion and AI Assistant Chat."), "orange");
		} else {
			frm.set_intro("");
		}

		if (!frm.is_new()) {
			frm.add_custom_button(
				__("AI Compliance Suggestion"),
				() => {
					frappe.call({
						method: "yam_agri_core.yam_agri_core.api.ai_assist.get_lot_compliance_suggestion",
						args: { lot: frm.doc.name },
						freeze: true,
						freeze_message: __("Generating assistive compliance suggestion..."),
						callback(r) {
							const msg = r.message || {};
							if (!msg.ok) {
								frappe.msgprint({
									title: __("AI Suggestion"),
									message: __("No suggestion available."),
									indicator: "orange",
								});
								return;
							}

							const counts = (msg.findings && msg.findings.counts) || {};
							const warning = msg.warning
								? `<div style="margin-bottom:8px;color:#b54708;">${frappe.utils.escape_html(msg.warning)}</div>`
								: "";
							const suggestion = frappe.utils.escape_html(msg.suggestion || "");
							const provider = frappe.utils.escape_html(msg.provider || "");
							const redactionCount = Number((msg.gateway && msg.gateway.redaction_count) || 0);
							const interactionLog = frappe.utils.escape_html(msg.interaction_log || "");

							frappe.msgprint({
								title: __("AI Compliance Suggestion"),
								message:
									warning +
									`<div><strong>${__("Assistive only - Review required")}</strong></div>` +
									`<div style="margin-top:8px;white-space:pre-wrap;">${suggestion}</div>` +
									`<hr>` +
									`<div>${__("Missing/Stale Tests")}: ${counts.missing_or_stale_tests || 0}</div>` +
									`<div>${__("Missing/Expired Required Certificates")}: ${counts.missing_or_expired_required_certificates || 0}</div>` +
									`<div>${__("Expired Certificates")}: ${counts.expired_certificates || 0}</div>` +
									`<div>${__("Open Nonconformance")}: ${counts.open_nonconformance || 0}</div>` +
									`<div style="margin-top:8px;color:#667085;">${__("Provider")}: ${provider} | ${__("Redactions")}: ${redactionCount}</div>` +
									`<div style="color:#667085;">${__("Interaction Log")}: ${interactionLog || __("Not available")}</div>`,
								wide: true,
							});

							yamPromptAiDecision(msg.interaction_log || "");
						},
					});
				},
				__("AI")
			);

			frm.add_custom_button(
				__("AI Assistant Chat"),
				() => {
					yamOpenLotAiChatDialog(frm);
				},
				__("AI")
			);
		}

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

		if (!frm.is_new()) {
			frm.dashboard.add_comment(__("Check the QC Tests and Certificates tabs for traceability details."), "blue", true);
		}
	},

	status(frm) {
		if (["Accepted", "Rejected"].includes(frm.doc.status) && !frappe.user.has_role("QA Manager")) {
			frappe.msgprint({
				title: __("Permission Required"),
				message: __("Only a QA Manager may set Lot status to {0}.", [frm.doc.status]),
				indicator: "red",
			});
			frm.set_value("status", frm._yam_original_status || "Draft");
		}
	},

	before_save(frm) {
		if (frm.is_new() && !frm.doc.site) {
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
