from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

import frappe
from frappe import _

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access

PROMPT_TEMPLATES: list[dict[str, Any]] = [
	{
		"template_id": "general_assistant",
		"name": _("General Assistant"),
		"description": _("General assistive guidance with governance guardrails."),
		"tags": ["general", "assistive"],
	},
	{
		"template_id": "lot_compliance",
		"name": _("Lot Compliance Check"),
		"description": _("Checks likely compliance gaps for lot-level quality and traceability."),
		"tags": ["compliance", "lot", "qa"],
	},
	{
		"template_id": "capa_draft",
		"name": _("CAPA Draft"),
		"description": _("Drafts a corrective and preventive action recommendation."),
		"tags": ["capa", "quality"],
	},
	{
		"template_id": "evidence_summary",
		"name": _("Evidence Summary"),
		"description": _("Summarizes evidence into an auditor-friendly narrative."),
		"tags": ["evidence", "audit"],
	},
	{
		"template_id": "risk_audit",
		"name": _("Risk Audit"),
		"description": _("Highlights likely operational and compliance risks with suggested checks."),
		"tags": ["risk", "compliance"],
	},
]

AI_INTERACTION_LOG_DOCTYPE = "AI Interaction Log"
AI_DECISION_MAP = {"pending": "Pending", "accepted": "Accepted", "rejected": "Rejected"}


def _safe_int(value: Any, default: int = 0) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _db_exists(doctype: str, name: str | None = None) -> bool:
	try:
		return bool(frappe.db.exists(doctype, name))
	except RuntimeError:
		# Allows standalone pytest runs where frappe local context is not bound.
		return False


def _ai_log_supported() -> bool:
	return _db_exists("DocType", AI_INTERACTION_LOG_DOCTYPE)


def _normalize_ai_decision(decision: str) -> str:
	key = (decision or "").strip().lower()
	if key not in AI_DECISION_MAP:
		frappe.throw(_("Decision must be one of: pending, accepted, rejected"), frappe.ValidationError)
	return AI_DECISION_MAP[key]


def _gateway_meta(gateway_result: dict[str, Any] | None) -> dict[str, Any]:
	payload = gateway_result or {}
	return {
		"prompt_hash": str(payload.get("prompt_hash") or ""),
		"response_hash": str(payload.get("response_hash") or ""),
		"redaction_applied": bool(payload.get("redaction_applied") or False),
		"redaction_count": _safe_int(payload.get("redaction_count"), 0),
		"template_id": str(payload.get("template_id") or ""),
		"model": str(payload.get("model") or ""),
		"tokens_used": _safe_int(payload.get("tokens_used"), 0),
	}


def _create_ai_interaction_log(
	*,
	site: str,
	source_doctype: str,
	source_name: str,
	task: str,
	endpoint: str,
	provider: str,
	requested_by: str,
	gateway_meta: dict[str, Any],
	warning_text: str = "",
) -> str:
	if not _ai_log_supported():
		return ""

	try:
		doc = frappe.get_doc(
			{
				"doctype": AI_INTERACTION_LOG_DOCTYPE,
				"site": site,
				"requested_by": requested_by or frappe.session.user,
				"source_doctype": source_doctype,
				"source_name": source_name,
				"task": task,
				"endpoint": endpoint,
				"provider": provider,
				"model_used": gateway_meta.get("model") or "",
				"prompt_hash": gateway_meta.get("prompt_hash") or "",
				"response_hash": gateway_meta.get("response_hash") or "",
				"redaction_applied": int(bool(gateway_meta.get("redaction_applied"))),
				"redaction_count": _safe_int(gateway_meta.get("redaction_count"), 0),
				"tokens_used": _safe_int(gateway_meta.get("tokens_used"), 0),
				"warning_text": warning_text or "",
				"decision": "Pending",
			}
		)
		doc.insert(ignore_permissions=True)
		return str(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI interaction log insert failed")
		return ""


def _safe_json_loads(raw: str | None, default: Any) -> Any:
	text = (raw or "").strip()
	if not text:
		return default
	try:
		return json.loads(text)
	except json.JSONDecodeError:
		return default


def _parse_csv_values(raw: str | None) -> list[str]:
	text = (raw or "").replace("\n", ",")
	parts = [p.strip() for p in text.split(",")]
	return [p for p in parts if p]


def _get_active_season_policy(site: str, crop: str | None) -> dict[str, Any] | None:
	filters: dict[str, Any] = {"site": site, "active": 1}
	if crop:
		filters["crop"] = crop

	rows = frappe.get_all(
		"Season Policy",
		filters=filters,
		fields=[
			"name",
			"mandatory_test_types",
			"mandatory_certificate_types",
			"max_test_age_days",
		],
		order_by="modified desc",
		limit_page_length=1,
	)
	if rows:
		return rows[0]

	if crop:
		fallback = frappe.get_all(
			"Season Policy",
			filters={"site": site, "active": 1},
			fields=[
				"name",
				"mandatory_test_types",
				"mandatory_certificate_types",
				"max_test_age_days",
			],
			order_by="modified desc",
			limit_page_length=1,
		)
		if fallback:
			return fallback[0]

	return None


def _normalize_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
	filters = filters or {}
	return {
		"include_closed_nonconformance": bool(filters.get("include_closed_nonconformance") or False),
		"include_expired_certificates": bool(filters.get("include_expired_certificates") or False),
		"from_date": str(filters.get("from_date") or "").strip(),
		"to_date": str(filters.get("to_date") or "").strip(),
	}


def _safe_getdate(raw_value: str) -> date | None:
	if not raw_value:
		return None
	try:
		return frappe.utils.getdate(raw_value)
	except (TypeError, ValueError):
		return None


def _collect_lot_compliance_findings(lot_doc: Any, filters: dict[str, Any] | None = None) -> dict[str, Any]:
	site = str(lot_doc.get("site") or "")
	crop = str(lot_doc.get("crop") or "")
	active_filters = _normalize_filters(filters)
	from_date = _safe_getdate(active_filters.get("from_date") or "")
	to_date = _safe_getdate(active_filters.get("to_date") or "")
	include_closed_nonconformance = bool(active_filters.get("include_closed_nonconformance"))
	include_expired_certificates = bool(active_filters.get("include_expired_certificates"))

	policy = _get_active_season_policy(site, crop)

	required_tests = _parse_csv_values(policy.get("mandatory_test_types") if policy else "")
	required_certs = _parse_csv_values(policy.get("mandatory_certificate_types") if policy else "")
	max_age_days = int(policy.get("max_test_age_days") or 7) if policy else 7

	missing_or_stale_tests: list[str] = []
	for test_type in required_tests:
		records = frappe.get_all(
			"QCTest",
			filters={
				"lot": lot_doc.name,
				"site": site,
				"test_type": test_type,
				"pass_fail": "Pass",
			},
			fields=["name", "test_date"],
			order_by="test_date desc",
			limit_page_length=1,
		)
		if not records:
			missing_or_stale_tests.append(test_type)
			continue

		test_date = records[0].get("test_date")
		if not test_date:
			missing_or_stale_tests.append(test_type)
			continue

		days_old = (frappe.utils.getdate(frappe.utils.nowdate()) - frappe.utils.getdate(test_date)).days
		if days_old > max_age_days:
			missing_or_stale_tests.append(test_type)

	missing_or_expired_certs: list[str] = []
	for cert_type in required_certs:
		records = frappe.get_all(
			"Certificate",
			filters={"lot": lot_doc.name, "site": site, "cert_type": cert_type},
			fields=["name", "expiry_date"],
			order_by="modified desc",
			limit_page_length=1,
		)
		if not records:
			missing_or_expired_certs.append(cert_type)
			continue

		expiry = records[0].get("expiry_date")
		if expiry and frappe.utils.getdate(expiry) < frappe.utils.getdate(frappe.utils.nowdate()):
			missing_or_expired_certs.append(cert_type)

	expired_certificates = frappe.get_all(
		"Certificate",
		filters={"lot": lot_doc.name, "site": site, "expiry_date": ["<", frappe.utils.nowdate()]},
		fields=["name", "cert_type", "expiry_date"],
		order_by="expiry_date asc",
		limit_page_length=100,
	)
	if not include_expired_certificates:
		expired_certificates = []
	elif from_date or to_date:
		filtered_expired: list[dict[str, Any]] = []
		for record in expired_certificates:
			expiry_date = record.get("expiry_date")
			if not expiry_date:
				continue
			expiry = frappe.utils.getdate(expiry_date)
			if from_date and expiry < from_date:
				continue
			if to_date and expiry > to_date:
				continue
			filtered_expired.append(record)
		expired_certificates = filtered_expired

	nonconformance_filters: dict[str, Any] = {"lot": lot_doc.name, "site": site}
	if not include_closed_nonconformance:
		nonconformance_filters["status"] = ["!=", "Closed"]

	nonconformance = frappe.get_all(
		"Nonconformance",
		filters=nonconformance_filters,
		fields=["name", "status", "modified"],
		order_by="modified desc",
		limit_page_length=100,
	)
	if from_date or to_date:
		filtered_nonconformance: list[dict[str, Any]] = []
		for record in nonconformance:
			modified = record.get("modified")
			if not modified:
				continue
			modified_date = frappe.utils.getdate(modified)
			if from_date and modified_date < from_date:
				continue
			if to_date and modified_date > to_date:
				continue
			filtered_nonconformance.append(record)
		nonconformance = filtered_nonconformance

	return {
		"policy": policy or {},
		"filters": active_filters,
		"max_test_age_days": max_age_days,
		"missing_or_stale_tests": sorted(set(missing_or_stale_tests)),
		"missing_or_expired_required_certificates": sorted(set(missing_or_expired_certs)),
		"expired_certificates": expired_certificates,
		"open_nonconformance": nonconformance,
		"counts": {
			"missing_or_stale_tests": len(set(missing_or_stale_tests)),
			"missing_or_expired_required_certificates": len(set(missing_or_expired_certs)),
			"expired_certificates": len(expired_certificates),
			"open_nonconformance": len(nonconformance),
		},
	}


def _local_compliance_suggestion(lot_name: str, findings: dict[str, Any]) -> str:
	counts = findings.get("counts") or {}
	return (
		"Compliance suggestion: review missing/stale QC tests ({}), required/expired certificates ({}), "
		"and open nonconformance records ({}) for lot {}. Prioritize high-risk gaps and assign owners with due dates."
	).format(
		int(counts.get("missing_or_stale_tests") or 0),
		int(counts.get("missing_or_expired_required_certificates") or 0),
		int(counts.get("open_nonconformance") or 0),
		lot_name,
	)


def _local_capa_suggestion(nonconformance_name: str, lot_name: str, nc_status: str) -> str:
	lot_label = lot_name or "N/A"
	return (
		"CAPA draft suggestion: for Nonconformance {0} (lot {1}, status {2}), define root cause hypothesis, "
		"immediate containment actions, corrective owner and due date, preventive action, and verification evidence. "
		"Decision required by authorized staff."
	).format(nonconformance_name, lot_label, nc_status or "Open")


def _collect_evidence_pack_context(evidence_doc: Any) -> dict[str, Any]:
	site = str(evidence_doc.get("site") or "")
	if not site:
		return {"counts": {}, "recent": {}}

	from_date = str(evidence_doc.get("from_date") or "").strip()
	to_date = str(evidence_doc.get("to_date") or "").strip()

	qc_filters: dict[str, Any] = {"site": site}
	if from_date:
		qc_filters["test_date"] = [">=", from_date]
	if to_date:
		existing = qc_filters.get("test_date")
		if isinstance(existing, list):
			qc_filters["test_date"] = ["between", [from_date or "1900-01-01", to_date]]
		else:
			qc_filters["test_date"] = ["<=", to_date]

	nc_filters: dict[str, Any] = {"site": site}
	if from_date:
		nc_filters["modified"] = [">=", f"{from_date} 00:00:00"]
	if to_date:
		if "modified" in nc_filters:
			nc_filters["modified"] = ["between", [f"{from_date or '1900-01-01'} 00:00:00", f"{to_date} 23:59:59"]]
		else:
			nc_filters["modified"] = ["<=", f"{to_date} 23:59:59"]

	lot_rows = frappe.get_all(
		"Lot",
		filters={"site": site},
		fields=["name", "status", "crop", "modified"],
		order_by="modified desc",
		limit_page_length=20,
	)
	qc_rows = frappe.get_all(
		"QCTest",
		filters=qc_filters,
		fields=["name", "test_type", "pass_fail", "test_date"],
		order_by="test_date desc",
		limit_page_length=20,
	)
	cert_rows = frappe.get_all(
		"Certificate",
		filters={"site": site},
		fields=["name", "cert_type", "expiry_date", "modified"],
		order_by="modified desc",
		limit_page_length=20,
	)
	nc_rows = frappe.get_all(
		"Nonconformance",
		filters=nc_filters,
		fields=["name", "status", "lot", "modified"],
		order_by="modified desc",
		limit_page_length=20,
	)

	return {
		"counts": {
			"lots": frappe.db.count("Lot", {"site": site}),
			"qc_tests": frappe.db.count("QCTest", qc_filters),
			"certificates": frappe.db.count("Certificate", {"site": site}),
			"nonconformance": frappe.db.count("Nonconformance", nc_filters),
		},
		"recent": {
			"lots": lot_rows,
			"qc_tests": qc_rows,
			"certificates": cert_rows,
			"nonconformance": nc_rows,
		},
	}


def _local_evidence_summary_suggestion(evidence_name: str, counts: dict[str, Any]) -> str:
	return (
		"Evidence summary suggestion: build a concise chronology for EvidencePack {0} using available records "
		"(lots: {1}, QC tests: {2}, certificates: {3}, nonconformance: {4}). "
		"Highlight unresolved risks and approvals needed. Decision required by authorized staff."
	).format(
		evidence_name,
		int(counts.get("lots") or 0),
		int(counts.get("qc_tests") or 0),
		int(counts.get("certificates") or 0),
		int(counts.get("nonconformance") or 0),
	)


def _resolve_gateway_url(endpoint_path: str) -> str:
	configured = (frappe.conf.get("ai_gateway_url") or os.environ.get("AI_GATEWAY_URL") or "").strip()
	if not configured:
		raise ValueError("AI gateway URL is not configured")

	parsed = urllib.parse.urlparse(configured)
	if not parsed.scheme:
		raise ValueError("AI gateway URL is invalid")

	endpoint = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"

	if parsed.path and parsed.path != "/":
		base_path = parsed.path.rstrip("/")
		if base_path.endswith("/suggest"):
			base_path = base_path[: -len("/suggest")]
		new_path = f"{base_path}{endpoint}" if base_path else endpoint
	else:
		new_path = endpoint

	return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, new_path, "", "", ""))


def _call_ai_gateway(payload: dict[str, Any], endpoint_path: str = "/suggest") -> dict[str, Any]:
	gateway_url = _resolve_gateway_url(endpoint_path)
	timeout_seconds = int(frappe.conf.get("ai_gateway_timeout") or os.environ.get("AI_GATEWAY_TIMEOUT") or 20)

	request = urllib.request.Request(
		gateway_url,
		data=json.dumps(payload).encode("utf-8"),
		headers={"Content-Type": "application/json"},
		method="POST",
	)
	with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
		body = response.read().decode("utf-8")
		return json.loads(body)


def _get_gateway_models() -> dict[str, Any]:
	gateway_url = _resolve_gateway_url("/models")
	timeout_seconds = int(frappe.conf.get("ai_gateway_timeout") or os.environ.get("AI_GATEWAY_TIMEOUT") or 20)
	request = urllib.request.Request(gateway_url, headers={"Accept": "application/json"}, method="GET")
	with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
		body = response.read().decode("utf-8")
		return json.loads(body)


def _get_gateway_prompt_templates() -> dict[str, Any]:
	gateway_url = _resolve_gateway_url("/prompt-templates")
	timeout_seconds = int(frappe.conf.get("ai_gateway_timeout") or os.environ.get("AI_GATEWAY_TIMEOUT") or 20)
	request = urllib.request.Request(gateway_url, headers={"Accept": "application/json"}, method="GET")
	with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
		body = response.read().decode("utf-8")
		return json.loads(body)


@frappe.whitelist()
def set_ai_interaction_decision(interaction_log: str, decision: str) -> dict[str, Any]:
	"""Update decision outcome for an AI interaction record."""
	interaction_name = (interaction_log or "").strip()
	if not interaction_name:
		frappe.throw(_("Interaction log is required"), frappe.ValidationError)

	if not _ai_log_supported():
		return {"ok": False, "status": "not-supported", "interaction_log": interaction_name}

	normalized_decision = _normalize_ai_decision(decision)
	log_doc = frappe.get_doc(AI_INTERACTION_LOG_DOCTYPE, interaction_name)

	site = str(log_doc.get("site") or "")
	if site:
		assert_site_access(site)

	log_doc.check_permission("write")
	log_doc.decision = normalized_decision
	log_doc.decided_by = frappe.session.user
	log_doc.decided_at = frappe.utils.now_datetime()
	log_doc.save()

	return {
		"ok": True,
		"interaction_log": log_doc.name,
		"decision": log_doc.decision,
		"decided_by": log_doc.decided_by,
		"decided_at": log_doc.decided_at,
	}


@frappe.whitelist()
def get_ai_prompt_templates() -> dict[str, Any]:
	"""Return available prompt templates for assistive AI use."""
	try:
		gateway_result = _get_gateway_prompt_templates()
		return {
			"ok": True,
			"source": "gateway",
			"templates": gateway_result.get("templates") or PROMPT_TEMPLATES,
		}
	except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
		return {
			"ok": True,
			"source": "local-fallback",
			"templates": PROMPT_TEMPLATES,
		}


@frappe.whitelist()
def get_ai_available_models() -> dict[str, Any]:
	"""Return available AI models from gateway, with safe fallback."""
	default_model = os.environ.get("OLLAMA_MODEL") or "llama3.2:3b"
	try:
		gateway_result = _get_gateway_models()
		models = gateway_result.get("models") or []
		return {
			"ok": True,
			"source": "gateway",
			"provider": gateway_result.get("provider") or "gateway",
			"default_model": gateway_result.get("default_model") or default_model,
			"models": models,
		}
	except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
		return {
			"ok": True,
			"source": "local-fallback",
			"provider": "local-fallback",
			"default_model": default_model,
			"models": [default_model],
		}


@frappe.whitelist()
def get_lot_compliance_suggestion(lot: str) -> dict[str, Any]:
	"""Return assistive compliance suggestion for a Lot.

	This endpoint is read-only/propose-only and never writes workflow/state changes.
	"""

	lot_name = (lot or "").strip()
	if not lot_name:
		frappe.throw(_("Lot is required"), frappe.ValidationError)

	lot_doc = frappe.get_doc("Lot", lot_name)
	site = str(lot_doc.get("site") or "")
	if not site:
		frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
	assert_site_access(site)

	findings = _collect_lot_compliance_findings(lot_doc)
	context_payload = {
		"lot": lot_doc.name,
		"site": site,
		"crop": lot_doc.get("crop"),
		"status": lot_doc.get("status"),
		"findings": findings,
	}

	gateway_payload = {
		"task": "compliance-check",
		"site": site,
		"record_type": "Lot",
		"record_name": lot_doc.name,
		"context": json.dumps(context_payload, ensure_ascii=False, default=str),
		"user": frappe.session.user,
		"max_tokens": 400,
		"template_id": "lot_compliance",
	}

	provider = "local-fallback"
	gateway_result: dict[str, Any] = {}
	suggestion_text = _local_compliance_suggestion(lot_doc.name, findings)
	warning = _("AI Gateway unavailable. Showing local assistive suggestion.")

	try:
		gateway_result = _call_ai_gateway(gateway_payload, endpoint_path="/suggest")
		suggestion_text = str(gateway_result.get("suggestion") or "").strip() or suggestion_text
		provider = str(gateway_result.get("provider") or "gateway")
		warning = ""
	except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
		pass

	gateway_meta = _gateway_meta(gateway_result)
	interaction_log = _create_ai_interaction_log(
		site=site,
		source_doctype="Lot",
		source_name=lot_doc.name,
		task="compliance-check",
		endpoint="/suggest",
		provider=provider,
		requested_by=frappe.session.user,
		gateway_meta=gateway_meta,
		warning_text=warning,
	)

	return {
		"ok": True,
		"task": "compliance-check",
		"lot": lot_doc.name,
		"site": site,
		"provider": provider,
		"assistive_only": True,
		"decision_required": True,
		"warning": warning,
		"suggestion": suggestion_text,
		"findings": findings,
		"interaction_log": interaction_log,
		"gateway": gateway_meta,
	}


@frappe.whitelist()
def get_nonconformance_capa_suggestion(
	nonconformance: str,
	model: str | None = None,
	template_id: str | None = None,
	max_tokens: int | None = None,
) -> dict[str, Any]:
	"""Return assistive CAPA draft suggestion for a Nonconformance."""
	nc_name = (nonconformance or "").strip()
	if not nc_name:
		frappe.throw(_("Nonconformance is required"), frappe.ValidationError)

	nc_doc = frappe.get_doc("Nonconformance", nc_name)
	site = str(nc_doc.get("site") or "")
	if not site:
		frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
	assert_site_access(site)

	lot_name = str(nc_doc.get("lot") or "")
	lot_context: dict[str, Any] = {}
	if lot_name and _db_exists("Lot", lot_name):
		lot_doc = frappe.get_doc("Lot", lot_name)
		if str(lot_doc.get("site") or "") == site:
			lot_context = {
				"lot": lot_doc.name,
				"status": lot_doc.get("status"),
				"crop": lot_doc.get("crop"),
				"findings": _collect_lot_compliance_findings(lot_doc),
			}

	context_payload = {
		"nonconformance": nc_doc.name,
		"site": site,
		"status": nc_doc.get("status"),
		"lot": lot_name,
		"capa_description": nc_doc.get("capa_description"),
		"lot_context": lot_context,
	}

	gateway_payload = {
		"task": "capa-draft",
		"site": site,
		"record_type": "Nonconformance",
		"record_name": nc_doc.name,
		"message": str(nc_doc.get("capa_description") or ""),
		"context": json.dumps(context_payload, ensure_ascii=False, default=str),
		"user": frappe.session.user,
		"model": (model or "").strip() or None,
		"template_id": (template_id or "").strip() or "capa_draft",
		"max_tokens": int(max_tokens or 450),
	}

	provider = "local-fallback"
	gateway_result: dict[str, Any] = {}
	suggestion_text = _local_capa_suggestion(
		nonconformance_name=nc_doc.name,
		lot_name=lot_name,
		nc_status=str(nc_doc.get("status") or ""),
	)
	warning = _("AI Gateway unavailable. Showing local assistive suggestion.")

	try:
		gateway_result = _call_ai_gateway(gateway_payload, endpoint_path="/suggest")
		suggestion_text = str(gateway_result.get("suggestion") or "").strip() or suggestion_text
		provider = str(gateway_result.get("provider") or "gateway")
		warning = ""
	except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
		pass

	gateway_meta = _gateway_meta(gateway_result)
	interaction_log = _create_ai_interaction_log(
		site=site,
		source_doctype="Nonconformance",
		source_name=nc_doc.name,
		task="capa-draft",
		endpoint="/suggest",
		provider=provider,
		requested_by=frappe.session.user,
		gateway_meta=gateway_meta,
		warning_text=warning,
	)

	return {
		"ok": True,
		"task": "capa-draft",
		"nonconformance": nc_doc.name,
		"site": site,
		"lot": lot_name,
		"provider": provider,
		"assistive_only": True,
		"decision_required": True,
		"warning": warning,
		"suggestion": suggestion_text,
		"lot_context": lot_context,
		"interaction_log": interaction_log,
		"gateway": gateway_meta,
	}


@frappe.whitelist()
def get_evidence_pack_summary_suggestion(
	evidence_pack: str,
	model: str | None = None,
	template_id: str | None = None,
	max_tokens: int | None = None,
) -> dict[str, Any]:
	"""Return assistive narrative summary suggestion for an EvidencePack."""
	evidence_name = (evidence_pack or "").strip()
	if not evidence_name:
		frappe.throw(_("EvidencePack is required"), frappe.ValidationError)

	evidence_doc = frappe.get_doc("EvidencePack", evidence_name)
	site = str(evidence_doc.get("site") or "")
	if not site:
		frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
	assert_site_access(site)

	evidence_context = _collect_evidence_pack_context(evidence_doc)
	context_payload = {
		"evidence_pack": evidence_doc.name,
		"title": evidence_doc.get("title"),
		"site": site,
		"from_date": evidence_doc.get("from_date"),
		"to_date": evidence_doc.get("to_date"),
		"status": evidence_doc.get("status"),
		"notes": evidence_doc.get("notes"),
		"context": evidence_context,
	}

	gateway_payload = {
		"task": "evidence-summary",
		"site": site,
		"record_type": "EvidencePack",
		"record_name": evidence_doc.name,
		"context": json.dumps(context_payload, ensure_ascii=False, default=str),
		"user": frappe.session.user,
		"model": (model or "").strip() or None,
		"template_id": (template_id or "").strip() or "evidence_summary",
		"max_tokens": int(max_tokens or 500),
	}

	provider = "local-fallback"
	gateway_result: dict[str, Any] = {}
	suggestion_text = _local_evidence_summary_suggestion(
		evidence_name=evidence_doc.name,
		counts=evidence_context.get("counts") or {},
	)
	warning = _("AI Gateway unavailable. Showing local assistive suggestion.")

	try:
		gateway_result = _call_ai_gateway(gateway_payload, endpoint_path="/suggest")
		suggestion_text = str(gateway_result.get("suggestion") or "").strip() or suggestion_text
		provider = str(gateway_result.get("provider") or "gateway")
		warning = ""
	except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
		pass

	gateway_meta = _gateway_meta(gateway_result)
	interaction_log = _create_ai_interaction_log(
		site=site,
		source_doctype="EvidencePack",
		source_name=evidence_doc.name,
		task="evidence-summary",
		endpoint="/suggest",
		provider=provider,
		requested_by=frappe.session.user,
		gateway_meta=gateway_meta,
		warning_text=warning,
	)

	return {
		"ok": True,
		"task": "evidence-summary",
		"evidence_pack": evidence_doc.name,
		"site": site,
		"provider": provider,
		"assistive_only": True,
		"decision_required": True,
		"warning": warning,
		"suggestion": suggestion_text,
		"context": evidence_context,
		"interaction_log": interaction_log,
		"gateway": gateway_meta,
	}


@frappe.whitelist()
def chat_with_lot_assistant(
	lot: str,
	message: str,
	model: str | None = None,
	template_id: str | None = None,
	filters_json: str | None = None,
	history_json: str | None = None,
	max_tokens: int | None = None,
) -> dict[str, Any]:
	"""Return assistive chat response for Lot context with optional model/template/filters."""

	lot_name = (lot or "").strip()
	if not lot_name:
		frappe.throw(_("Lot is required"), frappe.ValidationError)

	user_message = (message or "").strip()
	if not user_message:
		frappe.throw(_("Message is required"), frappe.ValidationError)

	lot_doc = frappe.get_doc("Lot", lot_name)
	site = str(lot_doc.get("site") or "")
	if not site:
		frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
	assert_site_access(site)

	raw_filters = _safe_json_loads(filters_json, {})
	filters = raw_filters if isinstance(raw_filters, dict) else {}
	history_payload = _safe_json_loads(history_json, [])
	history = history_payload if isinstance(history_payload, list) else []

	findings = _collect_lot_compliance_findings(lot_doc, filters=filters)
	context_payload = {
		"lot": lot_doc.name,
		"site": site,
		"crop": lot_doc.get("crop"),
		"status": lot_doc.get("status"),
		"filters": _normalize_filters(filters),
		"findings": findings,
	}

	gateway_payload = {
		"task": "chat",
		"site": site,
		"record_type": "Lot",
		"record_name": lot_doc.name,
		"message": user_message,
		"context": json.dumps(context_payload, ensure_ascii=False, default=str),
		"user": frappe.session.user,
		"model": (model or "").strip() or None,
		"template_id": (template_id or "").strip() or "general_assistant",
		"filters": _normalize_filters(filters),
		"chat_history": history,
		"max_tokens": int(max_tokens or 500),
	}

	local_reply = _(
		"Suggested next step for lot {0}: review current findings, confirm assumptions, and apply QA approval workflow. "
		"Decision required by authorized staff."
	).format(lot_doc.name)

	provider = "local-fallback"
	gateway_result: dict[str, Any] = {}
	warning = _("AI Gateway unavailable. Showing local assistive suggestion.")

	try:
		gateway_result = _call_ai_gateway(gateway_payload, endpoint_path="/chat")
		local_reply = str(gateway_result.get("reply") or "").strip() or local_reply
		provider = str(gateway_result.get("provider") or "gateway")
		warning = ""
	except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
		pass

	gateway_meta = _gateway_meta(gateway_result)
	interaction_log = _create_ai_interaction_log(
		site=site,
		source_doctype="Lot",
		source_name=lot_doc.name,
		task="chat",
		endpoint="/chat",
		provider=provider,
		requested_by=frappe.session.user,
		gateway_meta=gateway_meta,
		warning_text=warning,
	)

	return {
		"ok": True,
		"task": "chat",
		"lot": lot_doc.name,
		"site": site,
		"provider": provider,
		"assistive_only": True,
		"decision_required": True,
		"warning": warning,
		"reply": local_reply,
		"findings": findings,
		"interaction_log": interaction_log,
		"gateway": gateway_meta,
	}
