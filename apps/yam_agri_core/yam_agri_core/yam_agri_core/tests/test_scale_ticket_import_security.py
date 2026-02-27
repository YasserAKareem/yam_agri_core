from __future__ import annotations

from pathlib import Path

import pytest

import frappe

from yam_agri_core.yam_agri_core.api import scale_ticket_import as module


def _raise_from_throw(msg, exc=None):
	raise exc(msg) if exc else Exception(msg)


def test_resolve_output_path_rejects_absolute(monkeypatch):
	monkeypatch.setattr(module, "_resolve_repo_root", lambda: Path("D:/repo"))
	monkeypatch.setattr(frappe, "throw", _raise_from_throw)

	with pytest.raises(frappe.ValidationError):
		module._resolve_output_path("C:/temp/output.json")


def test_resolve_output_path_rejects_path_traversal(monkeypatch):
	monkeypatch.setattr(module, "_resolve_repo_root", lambda: Path("D:/repo"))
	monkeypatch.setattr(frappe, "throw", _raise_from_throw)

	with pytest.raises(frappe.ValidationError):
		module._resolve_output_path("../outside.json")


def test_resolve_output_path_accepts_artifacts_json(monkeypatch):
	monkeypatch.setattr(module, "_resolve_repo_root", lambda: Path("D:/repo"))

	path = module._resolve_output_path("artifacts/evidence/out.json")
	assert path == Path("D:/repo/artifacts/evidence/out.json")


def test_import_requires_role_gate(monkeypatch):
	monkeypatch.setattr(module, "resolve_site", lambda _site: "SITE-1")
	monkeypatch.setattr(module, "assert_site_access", lambda _site: None)
	monkeypatch.setattr(
		module,
		"_assert_role_gate",
		lambda **_kwargs: (_ for _ in ()).throw(frappe.PermissionError("forbidden")),
	)

	with pytest.raises(frappe.PermissionError):
		module.import_scale_tickets_csv(site="SITE-1", csv_content="")


def test_close_nonconformance_enforces_site_access(monkeypatch):
	class DummyNC:
		def __init__(self):
			self.site = "SITE-1"
			self.status = "Open"
			self.name = "NC-1"
			self.saved = False

		def get(self, key):
			return getattr(self, key, None)

		def save(self):
			self.saved = True

	nc_doc = DummyNC()
	site_access_called = {"site": ""}

	monkeypatch.setattr(module, "_assert_role_gate", lambda **_kwargs: None)
	monkeypatch.setattr(module, "assert_site_access", lambda site: site_access_called.__setitem__("site", site))
	monkeypatch.setattr(frappe, "get_doc", lambda _doctype, _name: nc_doc)

	result = module.close_nonconformance_with_qa("NC-1")

	assert site_access_called["site"] == "SITE-1"
	assert nc_doc.status == "Closed"
	assert nc_doc.saved is True
	assert result["new_status"] == "Closed"
