from __future__ import annotations

from types import SimpleNamespace

from yam_agri_core.yam_agri_core.api import ai_assist as module


class DummyLot:
	def __init__(self):
		self.name = "LOT-001"
		self.site = "SITE-A"
		self.crop = "Wheat"
		self.status = "Draft"
		self.save_called = False

	def get(self, key):
		return getattr(self, key, None)

	def save(self, *args, **kwargs):
		self.save_called = True
		raise AssertionError("AI assist endpoint must not save Lot records")


class DummyAIInteraction:
	def __init__(self):
		self.name = "AIL-0001"
		self.site = "SITE-A"
		self.decision = "Pending"
		self.decided_by = ""
		self.decided_at = None
		self.checked_permission = ""
		self.saved = False

	def get(self, key):
		return getattr(self, key, None)

	def check_permission(self, permission_type):
		self.checked_permission = permission_type

	def save(self):
		self.saved = True


class DummyNonconformance:
	def __init__(self):
		self.name = "NC-001"
		self.site = "SITE-A"
		self.lot = "LOT-001"
		self.status = "Open"
		self.capa_description = "Moisture out of range"

	def get(self, key):
		return getattr(self, key, None)


class DummyEvidencePack:
	def __init__(self):
		self.name = "YAM-EP-0001"
		self.site = "SITE-A"
		self.title = "Site A Evidence"
		self.from_date = "2026-02-01"
		self.to_date = "2026-02-28"
		self.status = "Draft"
		self.notes = "Monthly QA review"

	def get(self, key):
		return getattr(self, key, None)


def test_set_ai_interaction_decision_returns_not_supported_when_doctype_missing(monkeypatch):
	monkeypatch.setattr(module, "_ai_log_supported", lambda: False)

	result = module.set_ai_interaction_decision("AIL-0001", "accepted")

	assert result["ok"] is False
	assert result["status"] == "not-supported"
	assert result["interaction_log"] == "AIL-0001"


def test_set_ai_interaction_decision_updates_decision_fields(monkeypatch):
	doc = DummyAIInteraction()
	observed = {"site": "", "now": ""}

	monkeypatch.setattr(module, "_ai_log_supported", lambda: True)
	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.manager@example.com"))
	monkeypatch.setattr(module, "assert_site_access", lambda site: observed.__setitem__("site", site))
	monkeypatch.setattr(module.frappe, "get_doc", lambda _doctype, _name: doc)
	monkeypatch.setattr(
		module.frappe.utils,
		"now_datetime",
		lambda: observed.__setitem__("now", "2026-02-27 12:00:00") or "2026-02-27 12:00:00",
	)

	result = module.set_ai_interaction_decision("AIL-0001", "accepted")

	assert observed["site"] == "SITE-A"
	assert doc.checked_permission == "write"
	assert doc.saved is True
	assert result["ok"] is True
	assert result["decision"] == "Accepted"
	assert result["interaction_log"] == "AIL-0001"
	assert result["decided_by"] == "qa.manager@example.com"
	assert observed["now"] == "2026-02-27 12:00:00"


def test_get_lot_compliance_suggestion_is_assistive_only_and_logs(monkeypatch):
	dummy_lot = DummyLot()
	observed = {"site": "", "endpoint": "", "payload_task": ""}

	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.user@example.com"))
	monkeypatch.setattr(module.frappe, "get_doc", lambda _doctype, _name: dummy_lot)
	monkeypatch.setattr(module, "assert_site_access", lambda site: observed.__setitem__("site", site))
	monkeypatch.setattr(
		module,
		"_collect_lot_compliance_findings",
		lambda _lot_doc, filters=None: {
			"counts": {
				"missing_or_stale_tests": 1,
				"missing_or_expired_required_certificates": 1,
				"expired_certificates": 0,
				"open_nonconformance": 2,
			}
		},
	)

	def _fake_gateway(payload, endpoint_path="/suggest"):
		observed["endpoint"] = endpoint_path
		observed["payload_task"] = payload.get("task")
		return {
			"suggestion": "Review certificates and close open NCs.",
			"provider": "rules",
			"prompt_hash": "prompt-hash",
			"response_hash": "response-hash",
			"redaction_applied": True,
			"redaction_count": 2,
			"tokens_used": 123,
			"template_id": "lot_compliance",
			"model": "llama3.2:3b",
		}

	monkeypatch.setattr(module, "_call_ai_gateway", _fake_gateway)
	monkeypatch.setattr(module, "_create_ai_interaction_log", lambda **_kwargs: "AIL-0001")

	result = module.get_lot_compliance_suggestion("LOT-001")

	assert observed["site"] == "SITE-A"
	assert observed["endpoint"] == "/suggest"
	assert observed["payload_task"] == "compliance-check"
	assert result["ok"] is True
	assert result["assistive_only"] is True
	assert result["decision_required"] is True
	assert result["interaction_log"] == "AIL-0001"
	assert result["gateway"]["redaction_applied"] is True
	assert result["gateway"]["redaction_count"] == 2
	assert result["gateway"]["tokens_used"] == 123
	assert dummy_lot.save_called is False


def test_chat_with_lot_assistant_returns_redaction_and_interaction_log(monkeypatch):
	dummy_lot = DummyLot()
	observed = {"site": "", "endpoint": "", "payload_task": ""}

	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.user@example.com"))
	monkeypatch.setattr(module.frappe, "get_doc", lambda _doctype, _name: dummy_lot)
	monkeypatch.setattr(module, "assert_site_access", lambda site: observed.__setitem__("site", site))
	monkeypatch.setattr(
		module,
		"_collect_lot_compliance_findings",
		lambda _lot_doc, filters=None: {"counts": {"missing_or_stale_tests": 0}},
	)

	def _fake_gateway(payload, endpoint_path="/chat"):
		observed["endpoint"] = endpoint_path
		observed["payload_task"] = payload.get("task")
		return {
			"reply": "Check assumptions and verify latest records.",
			"provider": "rules",
			"prompt_hash": "prompt-chat",
			"response_hash": "response-chat",
			"redaction_applied": True,
			"redaction_count": 3,
			"tokens_used": 211,
			"template_id": "general_assistant",
			"model": "llama3.2:3b",
		}

	monkeypatch.setattr(module, "_call_ai_gateway", _fake_gateway)
	monkeypatch.setattr(module, "_create_ai_interaction_log", lambda **_kwargs: "AIL-CHAT-0001")

	result = module.chat_with_lot_assistant(
		lot="LOT-001",
		message="Summarize compliance risk.",
		model="llama3.2:3b",
		template_id="general_assistant",
		filters_json="{}",
		history_json="[]",
	)

	assert observed["site"] == "SITE-A"
	assert observed["endpoint"] == "/chat"
	assert observed["payload_task"] == "chat"
	assert result["ok"] is True
	assert result["assistive_only"] is True
	assert result["decision_required"] is True
	assert result["interaction_log"] == "AIL-CHAT-0001"
	assert result["gateway"]["redaction_applied"] is True
	assert result["gateway"]["redaction_count"] == 3
	assert result["gateway"]["tokens_used"] == 211
	assert dummy_lot.save_called is False


def test_get_nonconformance_capa_suggestion_logs_and_stays_assistive(monkeypatch):
	dummy_nc = DummyNonconformance()
	dummy_lot = DummyLot()
	observed = {"site": "", "endpoint": "", "payload_task": ""}

	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.user@example.com"))
	monkeypatch.setattr(
		module.frappe,
		"get_doc",
		lambda doctype, _name: dummy_nc if doctype == "Nonconformance" else dummy_lot,
	)
	monkeypatch.setattr(
		module,
		"_db_exists",
		lambda doctype, name=None: True if doctype == "Lot" and name == "LOT-001" else None,
	)
	monkeypatch.setattr(module, "assert_site_access", lambda site: observed.__setitem__("site", site))
	monkeypatch.setattr(
		module,
		"_collect_lot_compliance_findings",
		lambda _lot_doc, filters=None: {"counts": {"open_nonconformance": 2}},
	)

	def _fake_gateway(payload, endpoint_path="/suggest"):
		observed["endpoint"] = endpoint_path
		observed["payload_task"] = payload.get("task")
		return {
			"suggestion": "Contain lot and assign CAPA owner.",
			"provider": "rules",
			"prompt_hash": "prompt-capa",
			"response_hash": "response-capa",
			"redaction_applied": True,
			"redaction_count": 1,
			"tokens_used": 170,
			"template_id": "capa_draft",
			"model": "llama3.2:3b",
		}

	monkeypatch.setattr(module, "_call_ai_gateway", _fake_gateway)
	monkeypatch.setattr(module, "_create_ai_interaction_log", lambda **_kwargs: "AIL-NC-0001")

	result = module.get_nonconformance_capa_suggestion("NC-001")

	assert observed["site"] == "SITE-A"
	assert observed["endpoint"] == "/suggest"
	assert observed["payload_task"] == "capa-draft"
	assert result["ok"] is True
	assert result["assistive_only"] is True
	assert result["decision_required"] is True
	assert result["interaction_log"] == "AIL-NC-0001"
	assert result["gateway"]["redaction_applied"] is True
	assert result["gateway"]["redaction_count"] == 1
	assert result["gateway"]["tokens_used"] == 170


def test_get_evidence_pack_summary_suggestion_logs_and_stays_assistive(monkeypatch):
	dummy_ep = DummyEvidencePack()
	observed = {"site": "", "endpoint": "", "payload_task": ""}

	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.user@example.com"))
	monkeypatch.setattr(module.frappe, "get_doc", lambda _doctype, _name: dummy_ep)
	monkeypatch.setattr(module, "assert_site_access", lambda site: observed.__setitem__("site", site))
	monkeypatch.setattr(
		module,
		"_collect_evidence_pack_context",
		lambda _evidence_doc: {
			"counts": {"lots": 2, "qc_tests": 4, "certificates": 3, "nonconformance": 1},
			"recent": {},
		},
	)

	def _fake_gateway(payload, endpoint_path="/suggest"):
		observed["endpoint"] = endpoint_path
		observed["payload_task"] = payload.get("task")
		return {
			"suggestion": "Use timeline of QC and certificate renewals.",
			"provider": "rules",
			"prompt_hash": "prompt-ep",
			"response_hash": "response-ep",
			"redaction_applied": True,
			"redaction_count": 2,
			"tokens_used": 190,
			"template_id": "evidence_summary",
			"model": "llama3.2:3b",
		}

	monkeypatch.setattr(module, "_call_ai_gateway", _fake_gateway)
	monkeypatch.setattr(module, "_create_ai_interaction_log", lambda **_kwargs: "AIL-EP-0001")

	result = module.get_evidence_pack_summary_suggestion("YAM-EP-0001")

	assert observed["site"] == "SITE-A"
	assert observed["endpoint"] == "/suggest"
	assert observed["payload_task"] == "evidence-summary"
	assert result["ok"] is True
	assert result["assistive_only"] is True
	assert result["decision_required"] is True
	assert result["interaction_log"] == "AIL-EP-0001"
	assert result["gateway"]["redaction_applied"] is True
	assert result["gateway"]["redaction_count"] == 2
	assert result["gateway"]["tokens_used"] == 190
