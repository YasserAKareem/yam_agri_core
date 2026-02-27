from __future__ import annotations

from types import SimpleNamespace

from yam_agri_core.yam_agri_core.api import observation_monitoring as module


def test_summary_without_site_returns_empty_when_user_has_no_allowed_sites(monkeypatch):
	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.user@example.com"))
	monkeypatch.setattr(module, "_has_global_site_access", lambda _user: False)
	monkeypatch.setattr(module, "get_allowed_sites", lambda user=None: [])
	monkeypatch.setattr(
		module.frappe, "get_all", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError())
	)

	result = module.get_observation_executive_summary(site=None, include_quarantine=0, limit=50)

	assert result["status"] == "ok"
	assert result["row_count"] == 0
	assert result["rows"] == []


def test_summary_with_site_enforces_site_access(monkeypatch):
	observed = {"site": "", "filters": None}
	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.user@example.com"))
	monkeypatch.setattr(module, "resolve_site", lambda _site: "SITE-A")
	monkeypatch.setattr(module, "assert_site_access", lambda site: observed.__setitem__("site", site))

	def _fake_get_all(_doctype, filters, **_kwargs):
		observed["filters"] = filters
		return []

	monkeypatch.setattr(module.frappe, "get_all", _fake_get_all)

	result = module.get_observation_executive_summary(site="site-a", include_quarantine=1, limit=20)

	assert observed["site"] == "SITE-A"
	assert observed["filters"]["site"] == "SITE-A"
	assert result["row_count"] == 0


def test_summary_limit_is_capped(monkeypatch):
	observed = {"limit": 0}
	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="Administrator"))
	monkeypatch.setattr(module, "_has_global_site_access", lambda _user: True)

	def _fake_get_all(_doctype, filters, limit_page_length, **_kwargs):
		observed["limit"] = limit_page_length
		return []

	monkeypatch.setattr(module.frappe, "get_all", _fake_get_all)

	module.get_observation_executive_summary(site=None, include_quarantine=0, limit=99999)

	assert observed["limit"] == module.MAX_SUMMARY_LIMIT
