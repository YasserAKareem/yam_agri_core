from __future__ import annotations

from yam_agri_core.yam_agri_core.health import checks as module


def test_phase7_smoke_alias_calls_at09(monkeypatch):
	monkeypatch.setattr(module, "run_at09_automated_check", lambda: {"status": "pass", "evidence": {"k": 1}})

	result = module.run_phase7_smoke()

	assert result["status"] == "pass"
	assert result["evidence"]["k"] == 1


def test_at09_returns_blocked_when_readiness_not_ready(monkeypatch):
	monkeypatch.setattr(module, "get_at10_readiness", lambda: {"status": "blocked", "why": "missing"})

	result = module.run_at09_automated_check()

	assert result["status"] == "blocked"
	assert "AT-10 readiness" in result["reason"]
