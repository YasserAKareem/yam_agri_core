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
		"gateway": {
			"prompt_hash": gateway_result.get("prompt_hash") if gateway_result else "",
			"response_hash": gateway_result.get("response_hash") if gateway_result else "",
			"redaction_applied": int(gateway_result.get("redaction_applied") or 0) if gateway_result else 0,
			"redaction_count": int(gateway_result.get("redaction_count") or 0) if gateway_result else 0,
		},
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
		"gateway": {
			"prompt_hash": gateway_result.get("prompt_hash") if gateway_result else "",
			"response_hash": gateway_result.get("response_hash") if gateway_result else "",
			"redaction_applied": int(gateway_result.get("redaction_applied") or 0) if gateway_result else 0,
			"redaction_count": int(gateway_result.get("redaction_count") or 0) if gateway_result else 0,
			"template_id": gateway_result.get("template_id") if gateway_result else "",
			"model": gateway_result.get("model") if gateway_result else "",
		},
	}
