from __future__ import annotations

from types import SimpleNamespace

from yam_agri_core.yam_agri_core.api import evidence_pack as module


class DummyEvidencePack:
	def __init__(self, status: str = "Draft"):
		self.name = "YAM-EP-TEST-0001"
		self.site = "SITE-A"
		self.status = status
		self.generated_at = None
		self.generated_by = ""
		self.record_count = 0
		self.pdf_file = ""
		self.zip_file = ""
		self.rows = []
		self.saved = False

	def get(self, key):
		if key == "linked_documents":
			return self.rows
		return getattr(self, key, None)

	def set(self, key, value):
		if key == "linked_documents":
			self.rows = list(value)
			return
		setattr(self, key, value)

	def append(self, fieldname, row):
		if fieldname != "linked_documents":
			raise AssertionError("unexpected fieldname")
		self.rows.append(dict(row))

	def save(self):
		self.saved = True

	def check_permission(self, permission_type):
		_ = permission_type


def test_generate_evidence_pack_links_sets_ready_and_counts(monkeypatch):
	doc = DummyEvidencePack(status="Draft")
	rows = [
		{"source_doctype": "QCTest", "source_name": "QCT-1", "site": "SITE-A", "document_date": "2026-02-27"},
		{"source_doctype": "Certificate", "source_name": "CERT-1", "site": "SITE-A", "document_date": "2026-02-27"},
	]
	counts = {"QCTest": 1, "Certificate": 1}

	monkeypatch.setattr(module, "_assert_role_gate", lambda _label: None)
	monkeypatch.setattr(module, "_resolve_evidence_pack_doc", lambda _name, permission_type="write": doc)
	monkeypatch.setattr(module, "_collect_scope_rows", lambda _doc, include_quarantine=True: (rows, counts))
	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="qa.manager@example.com"))
	monkeypatch.setattr(module.frappe.utils, "now_datetime", lambda: "2026-02-27 18:00:00")

	result = module.generate_evidence_pack_links("YAM-EP-TEST-0001", rebuild=1, include_quarantine=1)

	assert result["ok"] is True
	assert result["record_count"] == 2
	assert result["counts"]["QCTest"] == 1
	assert doc.status == "Ready"
	assert doc.generated_by == "qa.manager@example.com"
	assert len(doc.rows) == 2
	assert doc.saved is True


def test_export_evidence_pack_zip_sets_zip_file(monkeypatch):
	doc = DummyEvidencePack(status="Ready")
	doc.rows = [{"source_doctype": "QCTest", "source_name": "QCT-1"}]

	monkeypatch.setattr(module, "_assert_role_gate", lambda _label: None)
	monkeypatch.setattr(module, "_resolve_evidence_pack_doc", lambda _name, permission_type="write": doc)
	monkeypatch.setattr(module, "_collect_zip_sources", lambda _doc: [])
	monkeypatch.setattr(module, "_build_zip_bytes", lambda _doc, _files, _counts: b"zip-bytes")
	monkeypatch.setattr(module, "save_file", lambda *args, **kwargs: SimpleNamespace(file_url="/private/files/ep.zip"))

	result = module.export_evidence_pack_zip("YAM-EP-TEST-0001")

	assert result["ok"] is True
	assert result["zip_file"] == "/private/files/ep.zip"
	assert doc.zip_file == "/private/files/ep.zip"
	assert doc.saved is True


def test_get_auditor_evidence_pack_stub_guest(monkeypatch):
	monkeypatch.setattr(module.frappe, "session", SimpleNamespace(user="Guest"))

	result = module.get_auditor_evidence_pack_stub()

	assert result["ok"] is True
	assert result["enabled"] is False
	assert result["records"] == []


def test_safe_zip_segment_sanitizes_path_tokens():
	assert module._safe_zip_segment("../unsafe\\path/name.txt") == "--unsafe-path-name.txt"
