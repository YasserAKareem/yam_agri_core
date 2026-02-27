function yamEpSubmitAiDecision(interactionLog, decision) {
	if (!interactionLog) {
		return;
	}

	frappe.call({
		method: "yam_agri_core.yam_agri_core.api.ai_assist.set_ai_interaction_decision",
		args: { interaction_log: interactionLog, decision },
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

function yamEpPromptAiDecision(interactionLog) {
	if (!interactionLog) {
		return;
	}

	frappe.confirm(
		__("Do you accept this AI evidence summary suggestion?"),
		() => yamEpSubmitAiDecision(interactionLog, "accepted"),
		() => yamEpSubmitAiDecision(interactionLog, "rejected")
	);
}

frappe.ui.form.on("EvidencePack", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(__("Save this EvidencePack first, then use AI Narrative Summary."), "orange");
			return;
		}
		frm.set_intro("");

		frm.add_custom_button(
			__("AI Narrative Summary"),
			() => {
				frappe.call({
					method: "yam_agri_core.yam_agri_core.api.ai_assist.get_evidence_pack_summary_suggestion",
					args: { evidence_pack: frm.doc.name },
					freeze: true,
					freeze_message: __("Generating assistive evidence summary..."),
					callback(r) {
						const msg = r.message || {};
						if (!msg.ok) {
							frappe.msgprint({
								title: __("AI Narrative Summary"),
								message: __("No suggestion available."),
								indicator: "orange",
							});
							return;
						}

						const warning = msg.warning
							? `<div style="margin-bottom:8px;color:#b54708;">${frappe.utils.escape_html(msg.warning)}</div>`
							: "";
						const suggestion = frappe.utils.escape_html(msg.suggestion || "");
						const provider = frappe.utils.escape_html(msg.provider || "");
						const redactionCount = Number((msg.gateway && msg.gateway.redaction_count) || 0);
						const interactionLog = frappe.utils.escape_html(msg.interaction_log || "");
						const counts = (msg.context && msg.context.counts) || {};

						frappe.msgprint({
							title: __("AI Narrative Summary"),
							message:
								warning +
								`<div><strong>${__("Assistive only - Review required")}</strong></div>` +
								`<div style="margin-top:8px;white-space:pre-wrap;">${suggestion}</div>` +
								`<hr>` +
								`<div>${__("Lots")}: ${counts.lots || 0}</div>` +
								`<div>${__("QC Tests")}: ${counts.qc_tests || 0}</div>` +
								`<div>${__("Certificates")}: ${counts.certificates || 0}</div>` +
								`<div>${__("Nonconformance")}: ${counts.nonconformance || 0}</div>` +
								`<div style="margin-top:8px;color:#667085;">${__("Provider")}: ${provider} | ${__("Redactions")}: ${redactionCount}</div>` +
								`<div style="color:#667085;">${__("Interaction Log")}: ${interactionLog || __("Not available")}</div>`,
							wide: true,
						});

						yamEpPromptAiDecision(msg.interaction_log || "");
					},
				});
			},
			__("AI")
		);
	},
});
