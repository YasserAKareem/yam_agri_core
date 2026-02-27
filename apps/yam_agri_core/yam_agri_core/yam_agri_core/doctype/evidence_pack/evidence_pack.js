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

function yamEpPromptAiDecision(frm, interactionLog, suggestionText) {
	if (!interactionLog) {
		return;
	}

	frappe.confirm(
		__("Do you accept this AI evidence summary suggestion?"),
		() => {
			const finalize = () => yamEpSubmitAiDecision(interactionLog, "accepted");
			if (!suggestionText) {
				finalize();
				return;
			}

			frm.set_value("approved_ai_narrative", suggestionText);
			if (!frm.is_dirty()) {
				finalize();
				return;
			}

			frm
				.save()
				.then(() => {
					finalize();
				})
				.catch(() => {
					frappe.show_alert({
						message: __("Narrative was not saved, but decision will still be logged."),
						indicator: "orange",
					});
					finalize();
				});
		},
		() => yamEpSubmitAiDecision(interactionLog, "rejected")
	);
}

function yamOpenFileIfAvailable(fileUrl, label) {
	if (!fileUrl) {
		frappe.msgprint({
			title: label,
			message: __("No file available yet. Generate it first."),
			indicator: "orange",
		});
		return;
	}
	window.open(fileUrl, "_blank");
}

function yamGenerateEvidencePack(frm) {
	frappe.call({
		method: "yam_agri_core.yam_agri_core.api.evidence_pack.generate_evidence_pack_links",
		args: { evidence_pack: frm.doc.name, rebuild: 1, include_quarantine: 1 },
		freeze: true,
		freeze_message: __("Building EvidencePack links..."),
		callback(r) {
			const msg = (r && r.message) || {};
			if (!msg.ok) {
				frappe.msgprint({
					title: __("EvidencePack Builder"),
					message: __("Could not generate linked documents."),
					indicator: "red",
				});
				return;
			}

			const counts = msg.counts || {};
			frappe.msgprint({
				title: __("EvidencePack Builder"),
				message:
					`<div><strong>${__("Status")}</strong>: ${frappe.utils.escape_html(msg.status || "")}</div>` +
					`<div><strong>${__("Linked Records")}</strong>: ${msg.record_count || 0}</div>` +
					`<div style="margin-top:8px;">${__("QCTest")}: ${counts.QCTest || 0}</div>` +
					`<div>${__("Certificate")}: ${counts.Certificate || 0}</div>` +
					`<div>${__("ScaleTicket")}: ${counts.ScaleTicket || 0}</div>` +
					`<div>${__("Observation")}: ${counts.Observation || 0}</div>` +
					`<div>${__("Nonconformance")}: ${counts.Nonconformance || 0}</div>`,
				wide: true,
			});
			frm.reload_doc();
		},
	});
}

function yamExportEvidencePdf(frm) {
	frappe.call({
		method: "yam_agri_core.yam_agri_core.api.evidence_pack.export_evidence_pack_pdf",
		args: { evidence_pack: frm.doc.name },
		freeze: true,
		freeze_message: __("Rendering EvidencePack PDF..."),
		callback(r) {
			const msg = (r && r.message) || {};
			if (!msg.ok) {
				frappe.msgprint({
					title: __("EvidencePack PDF"),
					message: __("PDF export failed."),
					indicator: "red",
				});
				return;
			}

			yamOpenFileIfAvailable(msg.pdf_file, __("EvidencePack PDF"));
			frm.reload_doc();
		},
	});
}

function yamExportEvidenceZip(frm) {
	frappe.call({
		method: "yam_agri_core.yam_agri_core.api.evidence_pack.export_evidence_pack_zip",
		args: { evidence_pack: frm.doc.name },
		freeze: true,
		freeze_message: __("Building EvidencePack ZIP..."),
		callback(r) {
			const msg = (r && r.message) || {};
			if (!msg.ok) {
				frappe.msgprint({
					title: __("EvidencePack ZIP"),
					message: __("ZIP export failed."),
					indicator: "red",
				});
				return;
			}

			yamOpenFileIfAvailable(msg.zip_file, __("EvidencePack ZIP"));
			frm.reload_doc();
		},
	});
}

function yamMarkEvidencePackSent(frm) {
	frappe.confirm(
		__("Mark this EvidencePack as Sent?"),
		() => {
			frappe.call({
				method: "yam_agri_core.yam_agri_core.api.evidence_pack.mark_evidence_pack_sent",
				args: { evidence_pack: frm.doc.name },
				freeze: true,
				freeze_message: __("Updating status..."),
				callback(r) {
					const msg = (r && r.message) || {};
					if (!msg.ok) {
						frappe.msgprint({
							title: __("EvidencePack"),
							message: __("Status update failed."),
							indicator: "red",
						});
						return;
					}
					frm.reload_doc();
				},
			});
		},
		() => {}
	);
}

frappe.ui.form.on("EvidencePack", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(__("Save this EvidencePack first, then generate links/PDF/ZIP and AI summary."), "orange");
			return;
		}
		frm.set_intro("");

		frm.add_custom_button(
			__("Generate Linked Evidence"),
			() => {
				yamGenerateEvidencePack(frm);
			},
			__("Evidence")
		);

		frm.add_custom_button(
			__("Export PDF"),
			() => {
				yamExportEvidencePdf(frm);
			},
			__("Evidence")
		);

		frm.add_custom_button(
			__("Export ZIP"),
			() => {
				yamExportEvidenceZip(frm);
			},
			__("Evidence")
		);

		if (["Ready", "Prepared"].includes(frm.doc.status)) {
			frm.add_custom_button(
				__("Mark Sent"),
				() => {
					yamMarkEvidencePackSent(frm);
				},
				__("Evidence")
			);
		}

		frm.add_custom_button(
			__("Auditor Portal Stub"),
			() => {
				window.open("/evidence-pack-auditor", "_blank");
			},
			__("Evidence")
		);

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

						yamEpPromptAiDecision(frm, msg.interaction_log || "", msg.suggestion || "");
					},
				});
			},
			__("AI")
		);
	},
});
