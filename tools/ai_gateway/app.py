from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="YAM AI Gateway", version="0.2.0")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
ENABLE_OLLAMA = os.environ.get("ENABLE_OLLAMA", "0") == "1"
OLLAMA_ALLOWED_MODELS = os.environ.get("OLLAMA_ALLOWED_MODELS", "")


def _derive_ollama_base_url(generate_url: str) -> str:
	url = (generate_url or "").strip().rstrip("/")
	if url.endswith("/api/generate"):
		return url[: -len("/api/generate")]
	if "/api/" in url:
		return url.split("/api/", maxsplit=1)[0]
	return url


OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", _derive_ollama_base_url(OLLAMA_URL)).rstrip("/")
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

_allowed_models = [item.strip() for item in OLLAMA_ALLOWED_MODELS.split(",") if item.strip()]
if not _allowed_models:
	_allowed_models = [OLLAMA_MODEL]
ALLOWED_MODEL_LIST = _allowed_models
ALLOWED_MODEL_SET = set(ALLOWED_MODEL_LIST)
DEFAULT_MODEL = OLLAMA_MODEL if OLLAMA_MODEL in ALLOWED_MODEL_SET else ALLOWED_MODEL_LIST[0]

_STATE: dict[str, Any] = {
	"requests_total": 0,
	"requests_redacted": 0,
	"provider_last": "rules",
	"last_error": "",
	"recent_tasks": [],
}

ALLOWED_TASKS = {"compliance-check", "capa-draft", "evidence-summary", "risk-audit", "chat"}

PROMPT_TEMPLATES: dict[str, dict[str, Any]] = {
	"general_assistant": {
		"name": "General Assistant",
		"description": "General assistive guidance with governance guardrails.",
		"required_vars": ["task", "site", "record_type", "record_name", "message", "context"],
		"tags": ["general", "assistive"],
		"template": (
			"Task: {task}\n"
			"Site: {site}\n"
			"Record: {record_type} {record_name}\n"
			"User message: {message}\n"
			"Context: {context}\n"
		),
	},
	"lot_compliance": {
		"name": "Lot Compliance Check",
		"description": "Checks likely compliance gaps for lot-level quality and traceability.",
		"required_vars": ["site", "record_name", "context", "filters"],
		"tags": ["compliance", "lot", "qa"],
		"template": (
			"Perform a lot compliance review.\n"
			"Site: {site}\n"
			"Lot: {record_name}\n"
			"Context: {context}\n"
			"Filters (redacted JSON): {filters}\n"
		),
	},
	"capa_draft": {
		"name": "CAPA Draft",
		"description": "Drafts a corrective and preventive action recommendation.",
		"required_vars": ["record_type", "record_name", "message", "context"],
		"tags": ["capa", "quality", "nonconformance"],
		"template": (
			"Draft CAPA suggestion only (assistive).\n"
			"Record: {record_type} {record_name}\n"
			"Issue summary: {message}\n"
			"Evidence/context: {context}\n"
		),
	},
	"evidence_summary": {
		"name": "Evidence Summary",
		"description": "Summarizes available evidence into an auditor-friendly narrative.",
		"required_vars": ["site", "record_type", "record_name", "context", "chat_history"],
		"tags": ["evidence", "audit", "summary"],
		"template": (
			"Build an evidence summary.\n"
			"Site: {site}\n"
			"Record: {record_type} {record_name}\n"
			"Context: {context}\n"
			"Recent history (redacted JSON): {chat_history}\n"
		),
	},
	"risk_audit": {
		"name": "Risk Audit",
		"description": "Highlights likely operational and compliance risks with suggested checks.",
		"required_vars": ["site", "task", "context", "filters"],
		"tags": ["risk", "audit", "compliance"],
		"template": (
			"Run a risk-oriented audit assistant pass.\n"
			"Task: {task}\n"
			"Site: {site}\n"
			"Context: {context}\n"
			"Filters (redacted JSON): {filters}\n"
		),
	},
}

PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\-\s]{7,}\d)(?!\d)")
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")
GPS_RE = re.compile(r"\b-?\d{1,2}\.\d{4,},\s*-?\d{1,3}\.\d{4,}\b")
PRICE_RE = re.compile(r"\b(?:USD|YER|SAR|\$)\s?\d+(?:[.,]\d+)?\b", re.IGNORECASE)
CUSTOMER_ID_RE = re.compile(r"\b(?:customer[_\s-]?id|cust[_\s-]?id)\s*[:=]\s*[A-Za-z0-9_-]+\b", re.IGNORECASE)
ASSISTANT_PREFIX_RE = re.compile(r"^\s*assistant\s*:\s*", re.IGNORECASE)


class SuggestRequest(BaseModel):
	task: str = Field(min_length=1)
	site: str = Field(min_length=1)
	record_type: str = Field(min_length=1)
	record_name: str = Field(min_length=1)
	context: str = Field(default="")
	user: str = Field(default="")
	max_tokens: int = Field(default=400, ge=64, le=1200)
	model: str | None = None
	template_id: str | None = None
	template_vars: dict[str, Any] = Field(default_factory=dict)
	filters: dict[str, Any] = Field(default_factory=dict)
	chat_history: list[dict[str, Any]] = Field(default_factory=list)


class SuggestResponse(BaseModel):
	ok: bool
	task: str
	suggestion: str
	provider: str
	assistive_only: bool
	redaction_applied: bool
	redaction_count: int
	prompt_hash: str
	response_hash: str
	decision_required: bool
	timestamp: str


class ChatTurn(BaseModel):
	role: str = Field(min_length=1)
	content: str = Field(default="")


class ChatRequest(BaseModel):
	task: str = Field(default="chat")
	site: str = Field(default="")
	record_type: str = Field(default="")
	record_name: str = Field(default="")
	message: str = Field(min_length=1)
	context: str = Field(default="")
	user: str = Field(default="")
	max_tokens: int = Field(default=400, ge=64, le=1600)
	model: str | None = None
	template_id: str | None = None
	template_vars: dict[str, Any] = Field(default_factory=dict)
	filters: dict[str, Any] = Field(default_factory=dict)
	chat_history: list[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
	ok: bool
	task: str
	reply: str
	provider: str
	model: str
	template_id: str
	assistive_only: bool
	decision_required: bool
	redaction_applied: bool
	redaction_count: int
	prompt_hash: str
	response_hash: str
	timestamp: str


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
	return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_json_dumps(value: Any) -> str:
	return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _clean_assistant_prefix(text: str) -> str:
	return ASSISTANT_PREFIX_RE.sub("", (text or "").strip()).strip()


def _redact_text(text: str) -> tuple[str, int]:
	redacted = text or ""
	count = 0
	for pattern, repl in (
		(PHONE_RE, "[REDACTED_PHONE]"),
		(EMAIL_RE, "[REDACTED_EMAIL]"),
		(GPS_RE, "[REDACTED_GPS]"),
		(PRICE_RE, "[REDACTED_PRICE]"),
		(CUSTOMER_ID_RE, "[REDACTED_CUSTOMER_ID]"),
	):
		redacted, pattern_count = pattern.subn(repl, redacted)
		count += pattern_count
	return redacted, count


def _normalize_task(task: str) -> str:
	return (task or "").strip().lower()


def _choose_template_id(task: str, template_id: str | None) -> str:
	if template_id:
		if template_id not in PROMPT_TEMPLATES:
			raise HTTPException(status_code=400, detail=f"Unsupported template_id '{template_id}'")
		return template_id

	task_key = _normalize_task(task)
	if task_key == "compliance-check":
		return "lot_compliance"
	if task_key == "capa-draft":
		return "capa_draft"
	if task_key == "evidence-summary":
		return "evidence_summary"
	if task_key == "risk-audit":
		return "risk_audit"
	return "general_assistant"


def _resolve_model(model_override: str | None) -> str:
	if not model_override:
		return DEFAULT_MODEL
	candidate = model_override.strip()
	if not candidate:
		return DEFAULT_MODEL
	if candidate not in ALLOWED_MODEL_SET:
		allowed = ", ".join(sorted(ALLOWED_MODEL_SET))
		raise HTTPException(status_code=400, detail=f"Model '{candidate}' is not allowed. Allowed: {allowed}")
	return candidate


def _governance_preamble() -> str:
	return (
		"You are an assistive-only compliance copilot for YAM Agri.\n"
		"Rules:\n"
		"- Return suggestion text only.\n"
		"- Do not execute actions, call APIs, or claim autonomous authority.\n"
		"- Do not provide instructions to write/submit/update records directly.\n"
		"- Prefer concise, auditable recommendations with explicit assumptions.\n"
		"- End with 'Decision required by authorized staff.'\n"
	)


def _template_metadata() -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = []
	for template_id, template_def in PROMPT_TEMPLATES.items():
		items.append(
			{
				"template_id": template_id,
				"name": template_def["name"],
				"description": template_def["description"],
				"required_vars": template_def["required_vars"],
				"tags": template_def["tags"],
			}
		)
	return items


def _render_template(
	template_id: str,
	task: str,
	site: str,
	record_type: str,
	record_name: str,
	message: str,
	context: str,
	user: str,
	filters_redacted_json: str,
	history_redacted_json: str,
	template_vars: dict[str, Any],
) -> str:
	template_def = PROMPT_TEMPLATES[template_id]
	template_body = str(template_def["template"])
	render_vars: dict[str, Any] = {
		"task": task,
		"site": site,
		"record_type": record_type,
		"record_name": record_name,
		"message": message,
		"context": context,
		"user": user,
		"filters": filters_redacted_json,
		"chat_history": history_redacted_json,
	}
	render_vars.update(template_vars or {})

	missing = [name for name in template_def["required_vars"] if name not in render_vars]
	if missing:
		raise HTTPException(status_code=400, detail=f"Missing template vars: {', '.join(missing)}")

	try:
		return template_body.format(**render_vars)
	except KeyError as exc:
		raise HTTPException(status_code=400, detail=f"Missing template variable: {exc}") from exc


def _rule_based_suggestion(task: str, redacted_context: str, payload: SuggestRequest) -> str:
	if task == "compliance-check":
		return (
			"Compliance suggestion: review missing QC tests, expired certificates, and open nonconformance records "
			f"for {payload.record_type} {payload.record_name}. Prioritize unresolved risks first. Context: {redacted_context[:300]}"
		)
	if task == "capa-draft":
		return (
			"CAPA draft suggestion: define root cause hypothesis, immediate containment, corrective action owner, due date, "
			f"and verification method for {payload.record_type} {payload.record_name}. Context: {redacted_context[:300]}"
		)
	if task == "risk-audit":
		return (
			"Risk audit suggestion: identify high-impact failure points, confirm preventive controls, and verify "
			f"traceability evidence completeness for {payload.record_type} {payload.record_name}. Context: {redacted_context[:300]}"
		)
	return (
		"Evidence summary suggestion: create concise chronology of checks, certificates, observations, deviations, "
		f"and approvals for {payload.record_type} {payload.record_name}. Context: {redacted_context[:300]}"
	)


async def _ollama_generate(prompt: str, model: str, max_tokens: int) -> str:
	request_payload = {
		"model": model,
		"prompt": prompt,
		"stream": False,
		"options": {"num_predict": min(max_tokens, 900)},
	}
	async with httpx.AsyncClient(timeout=25) as client:
		response = await client.post(OLLAMA_URL, json=request_payload)
		response.raise_for_status()
		result = response.json()
		return str(result.get("response") or "").strip()


def _safe_chat_fallback(task: str, payload: ChatRequest, redacted_context: str, template_id: str) -> str:
	task_key = _normalize_task(task)
	if task_key == "compliance-check" or template_id == "lot_compliance":
		return (
			f"Suggested compliance review for {payload.record_type} {payload.record_name} at {payload.site}: "
			"verify site linkage, certificate validity, latest QC pass/fail results, and unresolved nonconformances. "
			f"Context excerpt: {redacted_context[:240]}. Decision required by authorized staff."
		)
	if task_key == "capa-draft" or template_id == "capa_draft":
		return (
			f"Suggested CAPA draft for {payload.record_type} {payload.record_name}: define root cause hypothesis, "
			"containment action, corrective owner, preventive control, due dates, and verification criteria. "
			f"Context excerpt: {redacted_context[:240]}. Decision required by authorized staff."
		)
	if task_key == "evidence-summary" or template_id == "evidence_summary":
		return (
			f"Suggested evidence summary for {payload.record_type} {payload.record_name}: compile timeline of checks, "
			"test outcomes, approvals, and deviations with dates and responsible roles. "
			f"Context excerpt: {redacted_context[:240]}. Decision required by authorized staff."
		)
	if task_key == "risk-audit" or template_id == "risk_audit":
		return (
			f"Suggested risk audit focus for site {payload.site}: prioritize high-likelihood/high-impact risks, "
			"identify missing controls, and define verification checkpoints. "
			f"Context excerpt: {redacted_context[:240]}. Decision required by authorized staff."
		)
	return (
		"Suggested next step: summarize the issue, list assumptions and uncertainties, and propose 2-3 assistive options "
		"with verification checks. Decision required by authorized staff."
	)


def _append_recent(task: str, site: str, provider: str) -> None:
	_STATE["recent_tasks"].append({"task": task, "site": site, "at": _utc_now_iso(), "provider": provider})
	_STATE["recent_tasks"] = _STATE["recent_tasks"][-100:]


@app.get("/health")
def health() -> dict[str, Any]:
	return {
		"status": "ok",
		"service": "ai-gateway",
		"provider_mode": "ollama" if ENABLE_OLLAMA else "rules",
		"ollama_url": OLLAMA_URL if ENABLE_OLLAMA else "",
	}


@app.get("/status")
def status() -> dict[str, Any]:
	return {
		"status": "ok",
		"requests_total": _STATE["requests_total"],
		"requests_redacted": _STATE["requests_redacted"],
		"provider_last": _STATE["provider_last"],
		"last_error": _STATE["last_error"],
		"recent_tasks": _STATE["recent_tasks"][-20:],
	}


@app.get("/prompt-templates")
def prompt_templates() -> dict[str, Any]:
	return {
		"status": "ok",
		"count": len(PROMPT_TEMPLATES),
		"templates": _template_metadata(),
	}


@app.get("/models")
async def models() -> dict[str, Any]:
	if not ENABLE_OLLAMA:
		return {
			"status": "ok",
			"provider": "rules",
			"source": "allowlist",
			"default_model": DEFAULT_MODEL,
			"allowed_models": ALLOWED_MODEL_LIST,
			"models": ALLOWED_MODEL_LIST,
		}

	try:
		async with httpx.AsyncClient(timeout=12) as client:
			response = await client.get(OLLAMA_TAGS_URL)
			response.raise_for_status()
			payload = response.json()
	except Exception as exc:  # pylint: disable=broad-except
		_STATE["last_error"] = str(exc)
		return {
			"status": "ok",
			"provider": "ollama",
			"source": "fallback_allowlist",
			"default_model": DEFAULT_MODEL,
			"allowed_models": ALLOWED_MODEL_LIST,
			"models": ALLOWED_MODEL_LIST,
		}

	raw_models = payload.get("models") or []
	available = [
		str(item.get("name", "")).strip() for item in raw_models if str(item.get("name", "")).strip()
	]
	filtered = [name for name in available if name in ALLOWED_MODEL_SET]
	models_out = filtered or ALLOWED_MODEL_LIST

	return {
		"status": "ok",
		"provider": "ollama",
		"source": "ollama_tags",
		"default_model": DEFAULT_MODEL,
		"allowed_models": ALLOWED_MODEL_LIST,
		"models": models_out,
	}


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(payload: SuggestRequest) -> SuggestResponse:
	task = _normalize_task(payload.task)
	if task not in ALLOWED_TASKS:
		allowed = ", ".join(sorted(ALLOWED_TASKS))
		raise HTTPException(status_code=400, detail=f"Unsupported task '{task}'. Allowed: {allowed}")

	template_id = _choose_template_id(task=task, template_id=payload.template_id)
	model = _resolve_model(payload.model)

	redacted_context, context_redactions = _redact_text(payload.context or "")
	redacted_filters_json, filter_redactions = _redact_text(_safe_json_dumps(payload.filters or {}))
	redacted_history_json, history_redactions = _redact_text(_safe_json_dumps(payload.chat_history or []))
	redaction_count = context_redactions + filter_redactions + history_redactions

	template_text = _render_template(
		template_id=template_id,
		task=task,
		site=payload.site,
		record_type=payload.record_type,
		record_name=payload.record_name,
		message="",
		context=redacted_context,
		user=payload.user,
		filters_redacted_json=redacted_filters_json,
		history_redacted_json=redacted_history_json,
		template_vars=payload.template_vars,
	)

	full_prompt = (
		f"{_governance_preamble()}\n"
		f"Template ID: {template_id}\n"
		f"User: {payload.user or 'unknown'}\n"
		f"{template_text}\n"
		"Return concise suggestion text only. Do not include code blocks.\n"
	)

	prompt_material = f"task={task}|site={payload.site}|record={payload.record_type}:{payload.record_name}|context={redacted_context}"
	prompt_hash = _sha256_text(prompt_material)

	provider = "rules"
	suggestion_text = ""
	try:
		if ENABLE_OLLAMA:
			provider = "ollama"
			suggestion_text = await _ollama_generate(
				prompt=full_prompt, model=model, max_tokens=payload.max_tokens
			)
		if not suggestion_text:
			provider = "rules"
			suggestion_text = _rule_based_suggestion(task, redacted_context, payload)
	except Exception as exc:  # pylint: disable=broad-except
		_STATE["last_error"] = str(exc)
		provider = "rules"
		suggestion_text = _rule_based_suggestion(task, redacted_context, payload)

	suggestion_text = _clean_assistant_prefix(suggestion_text)
	response_hash = _sha256_text(suggestion_text)
	_STATE["requests_total"] = int(_STATE["requests_total"]) + 1
	if redaction_count > 0:
		_STATE["requests_redacted"] = int(_STATE["requests_redacted"]) + 1
	_STATE["provider_last"] = provider
	_append_recent(task=task, site=payload.site, provider=provider)

	return SuggestResponse(
		ok=True,
		task=task,
		suggestion=suggestion_text,
		provider=provider,
		assistive_only=True,
		redaction_applied=redaction_count > 0,
		redaction_count=redaction_count,
		prompt_hash=prompt_hash,
		response_hash=response_hash,
		decision_required=True,
		timestamp=_utc_now_iso(),
	)


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
	task = _normalize_task(payload.task)
	template_id = _choose_template_id(task=task, template_id=payload.template_id)
	model = _resolve_model(payload.model)

	redacted_message, message_redactions = _redact_text(payload.message or "")
	redacted_context, context_redactions = _redact_text(payload.context or "")
	redacted_filters_json, filter_redactions = _redact_text(_safe_json_dumps(payload.filters or {}))
	history_payload = [{"role": turn.role, "content": turn.content} for turn in payload.chat_history]
	redacted_history_json, history_redactions = _redact_text(_safe_json_dumps(history_payload))
	redaction_count = message_redactions + context_redactions + filter_redactions + history_redactions

	template_text = _render_template(
		template_id=template_id,
		task=task,
		site=payload.site,
		record_type=payload.record_type,
		record_name=payload.record_name,
		message=redacted_message,
		context=redacted_context,
		user=payload.user,
		filters_redacted_json=redacted_filters_json,
		history_redacted_json=redacted_history_json,
		template_vars=payload.template_vars,
	)

	full_prompt = (
		f"{_governance_preamble()}\n"
		f"Template ID: {template_id}\n"
		f"User: {payload.user or 'unknown'}\n"
		f"{template_text}\n"
		"Return concise suggestion text only. Do not include code blocks.\n"
	)

	provider = "rules"
	reply = ""
	try:
		if ENABLE_OLLAMA:
			provider = "ollama"
			reply = await _ollama_generate(prompt=full_prompt, model=model, max_tokens=payload.max_tokens)
		if not reply:
			provider = "rules"
			reply = _safe_chat_fallback(
				task=task, payload=payload, redacted_context=redacted_context, template_id=template_id
			)
	except Exception as exc:  # pylint: disable=broad-except
		_STATE["last_error"] = str(exc)
		provider = "rules"
		reply = _safe_chat_fallback(
			task=task, payload=payload, redacted_context=redacted_context, template_id=template_id
		)

	reply = _clean_assistant_prefix(reply)
	prompt_hash = _sha256_text(full_prompt)
	response_hash = _sha256_text(reply)

	_STATE["requests_total"] = int(_STATE["requests_total"]) + 1
	if redaction_count > 0:
		_STATE["requests_redacted"] = int(_STATE["requests_redacted"]) + 1
	_STATE["provider_last"] = provider
	_append_recent(task=task, site=payload.site, provider=provider)

	return ChatResponse(
		ok=True,
		task=task,
		reply=reply,
		provider=provider,
		model=model,
		template_id=template_id,
		assistive_only=True,
		decision_required=True,
		redaction_applied=redaction_count > 0,
		redaction_count=redaction_count,
		prompt_hash=prompt_hash,
		response_hash=response_hash,
		timestamp=_utc_now_iso(),
	)
