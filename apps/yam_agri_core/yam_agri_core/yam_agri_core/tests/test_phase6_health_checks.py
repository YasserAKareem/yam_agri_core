from __future__ import annotations

from yam_agri_core.yam_agri_core.health import checks as module


def test_phase6_governance_bundle_pass(monkeypatch):
	monkeypatch.setattr(module, "run_at11_automated_check", lambda: {"status": "pass", "evidence": {"k": 1}})
	monkeypatch.setattr(module, "run_at12_automated_check", lambda: {"status": "pass", "evidence": {"k": 2}})

	result = module.run_phase6_governance_automated_check()

	assert result["status"] == "pass"
	assert result["checks"]["at11"] == "pass"
	assert result["checks"]["at12"] == "pass"


def test_phase6_governance_bundle_blocked(monkeypatch):
	monkeypatch.setattr(module, "run_at11_automated_check", lambda: {"status": "pass", "evidence": {}})
	monkeypatch.setattr(module, "run_at12_automated_check", lambda: {"status": "blocked", "evidence": {}})

	result = module.run_phase6_governance_automated_check()

	assert result["status"] == "blocked"
	assert result["checks"]["at11"] == "pass"
	assert result["checks"]["at12"] == "blocked"


def test_phase6_governance_bundle_fail_wins(monkeypatch):
	monkeypatch.setattr(module, "run_at11_automated_check", lambda: {"status": "fail", "evidence": {}})
	monkeypatch.setattr(module, "run_at12_automated_check", lambda: {"status": "blocked", "evidence": {}})

	result = module.run_phase6_governance_automated_check()

	assert result["status"] == "fail"
	assert result["checks"]["at11"] == "fail"
