from __future__ import annotations

import frappe
from frappe import _

from yam_agri_core.yam_agri_core.api.evidence_pack import get_auditor_evidence_pack_stub


def get_context(context):
	context.no_cache = 1
	context.title = _("Auditor EvidencePack Portal (Stub)")
	result = get_auditor_evidence_pack_stub(limit=50)
	context.portal_enabled = bool(result.get("enabled"))
	context.portal_message = result.get("message")
	context.records = result.get("records") or []
	context.user = frappe.session.user
