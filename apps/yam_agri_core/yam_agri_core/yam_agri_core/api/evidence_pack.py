from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import frappe
from frappe import _
from frappe.utils.file_manager import save_file
from frappe.utils.pdf import get_pdf

from yam_agri_core.yam_agri_core.site_permissions import (
	assert_site_access,
	get_allowed_sites,
	resolve_site,
)

_ALLOWED_ROLES = {"QA Manager", "System Manager", "Administrator"}
_MAX_ROWS_PER_SOURCE = 1000
_MAX_PORTAL_ROWS = 200


def _safe_int(value: Any, default: int = 0) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _has_global_site_access(user: str) -> bool:
	if user == "Administrator":
		return True
	return "System Manager" in set(frappe.get_roles(user) or [])


def _assert_role_gate(action_label: str) -> None:
	current_roles = set(frappe.get_roles(frappe.session.user) or [])
	if current_roles.intersection(_ALLOWED_ROLES):
		return
	frappe.throw(
		_("Only users with role(s) {0} may {1}.").format(
			", ".join(sorted(_ALLOWED_ROLES)), action_label
		),
		frappe.PermissionError,
	)


def _safe_zip_segment(value: str) -> str:
	text = (value or "").strip().replace("\\", "-").replace("/", "-")
	text = text.replace("..", "-").replace(":", "-")
	if not text:
		return "unnamed"
	return text


def _as_date_range(from_date: str | None, to_date: str | None) -> tuple[str, str]:
	from_raw = (from_date or "").strip() or frappe.utils.nowdate()
	to_raw = (to_date or "").strip() or frappe.utils.nowdate()
	from_value = str(frappe.utils.getdate(from_raw))
	to_value = str(frappe.utils.getdate(to_raw))
	if from_value > to_value:
		frappe.throw(_("From Date must be on or before To Date"), frappe.ValidationError)
	return from_value, to_value


def _date_filter(fieldname: str, from_date: str, to_date: str, include_time: bool = False) -> dict[str, Any]:
	if include_time:
		return {fieldname: ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]]}
	return {fieldname: ["between", [from_date, to_date]]}


def _resolve_evidence_pack_doc(evidence_pack: str, permission_type: str = "write") -> Any:
	evidence_name = (evidence_pack or "").strip()
	if not evidence_name:
		frappe.throw(_("EvidencePack is required"), frappe.ValidationError)

	evidence_doc = frappe.get_doc("EvidencePack", evidence_name)
	site = str(evidence_doc.get("site") or "")
	if not site:
		frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
	assert_site_access(site)
	evidence_doc.check_permission(permission_type)
	return evidence_doc


def _source_configs(include_quarantine: bool) -> list[dict[str, Any]]:
	observation_filters: dict[str, Any] = {}
	if not include_quarantine:
		observation_filters["quality_flag"] = ["!=", "Quarantine"]

	return [
		{
			"doctype": "QCTest",
			"date_field": "test_date",
			"fields": ["name", "site", "lot", "test_type", "pass_fail", "test_date"],
			"status_field": "pass_fail",
			"summary_builder": lambda row: "{0} ({1})".format(
				str(row.get("test_type") or "Test").strip() or "Test",
				str(row.get("pass_fail") or "Unknown").strip() or "Unknown",
			),
			"extra_filters": {},
			"datetime_field": False,
		},
		{
			"doctype": "Certificate",
			"date_field": "expiry_date",
			"fields": ["name", "site", "lot", "cert_type", "expiry_date"],
			"status_field": "cert_type",
			"summary_builder": lambda row: "{0} (expiry {1})".format(
				str(row.get("cert_type") or "Certificate").strip() or "Certificate",
				str(row.get("expiry_date") or "N/A").strip() or "N/A",
			),
			"extra_filters": {},
			"datetime_field": False,
		},
		{
			"doctype": "ScaleTicket",
			"date_field": "ticket_datetime",
			"fields": ["name", "site", "lot", "ticket_number", "ticket_datetime", "net_kg"],
			"status_field": "ticket_number",
			"summary_builder": lambda row: "{0} (net {1} kg)".format(
				str(row.get("ticket_number") or row.get("name") or "ScaleTicket").strip() or "ScaleTicket",
				str(row.get("net_kg") or 0),
			),
			"extra_filters": {},
			"datetime_field": True,
		},
		{
			"doctype": "Observation",
			"date_field": "observed_at",
			"fields": ["name", "site", "observation_type", "quality_flag", "observed_at", "unit", "value"],
			"status_field": "quality_flag",
			"summary_builder": lambda row: "{0}: {1} {2} ({3})".format(
				str(row.get("observation_type") or "Observation").strip() or "Observation",
				str(row.get("value") or ""),
				str(row.get("unit") or "").strip(),
				str(row.get("quality_flag") or "Unknown").strip() or "Unknown",
			),
			"extra_filters": observation_filters,
			"datetime_field": True,
		},
		{
			"doctype": "Nonconformance",
			"date_field": "modified",
			"fields": ["name", "site", "lot", "status", "modified", "capa_description"],
			"status_field": "status",
			"summary_builder": lambda row: str(row.get("capa_description") or "Nonconformance")[:240],
			"extra_filters": {},
			"datetime_field": True,
		},
	]


def _collect_scope_rows(evidence_doc: Any, include_quarantine: bool = True) -> tuple[list[dict[str, Any]], dict[str, int]]:
	site = str(evidence_doc.get("site") or "")
	lot_name = str(evidence_doc.get("lot") or "").strip()
	from_date, to_date = _as_date_range(
		str(evidence_doc.get("from_date") or ""),
		str(evidence_doc.get("to_date") or ""),
	)

	rows: list[dict[str, Any]] = []
	counts: dict[str, int] = {}
	for config in _source_configs(include_quarantine=bool(include_quarantine)):
		doctype = config["doctype"]
		date_field = config["date_field"]
		filters: dict[str, Any] = {
			"site": site,
			**config.get("extra_filters", {}),
			**_date_filter(date_field, from_date, to_date, include_time=bool(config.get("datetime_field"))),
		}
		if lot_name and frappe.get_meta(doctype).has_field("lot"):
			filters["lot"] = lot_name

		doctype_rows = frappe.get_all(
			doctype,
			filters=filters,
			fields=config["fields"],
			order_by=f"{date_field} desc",
			limit=_MAX_ROWS_PER_SOURCE,
		)
		counts[doctype] = len(doctype_rows)

		for row in doctype_rows:
			doc_name = str(row.get("name") or "")
			attachment_count = _safe_int(
				frappe.db.count(
					"File", {"attached_to_doctype": doctype, "attached_to_name": doc_name}
				),
				0,
			)
			rows.append(
				{
					"source_doctype": doctype,
					"source_name": doc_name,
					"site": str(row.get("site") or site),
					"document_date": row.get(date_field),
					"status": str(row.get(config["status_field"]) or "").strip(),
					"attachment_count": attachment_count,
					"summary": str(config["summary_builder"](row) or "").strip(),
				}
			)

	rows.sort(key=lambda row: str(row.get("document_date") or ""), reverse=True)
	return rows, counts


def _accepted_ai_narrative(evidence_doc: Any) -> str:
	narrative = str(evidence_doc.get("approved_ai_narrative") or "").strip()
	if not narrative:
		return ""

	if not frappe.db.exists("DocType", "AI Interaction Log"):
		return narrative

	accepted = frappe.db.exists(
		"AI Interaction Log",
		{
			"source_doctype": "EvidencePack",
			"source_name": evidence_doc.name,
			"task": "evidence-summary",
			"decision": "Accepted",
		},
	)
	if not accepted:
		return ""
	return narrative


def _render_pdf_html(evidence_doc: Any, linked_rows: list[dict[str, Any]], counts: dict[str, int]) -> str:
	template_path = Path(
		frappe.get_app_path(
			"yam_agri_core",
			"yam_agri_core",
			"templates",
			"includes",
			"evidence_pack_pdf.html",
		)
	)
	template_text = template_path.read_text(encoding="utf-8")
	context = {
		"doc": evidence_doc,
		"linked_documents": linked_rows,
		"counts": counts,
		"generated_on": frappe.utils.now_datetime(),
		"narrative": _accepted_ai_narrative(evidence_doc),
	}
	return frappe.render_template(template_text, context)


def _collect_zip_sources(evidence_doc: Any) -> list[dict[str, Any]]:
	files: list[dict[str, Any]] = []
	seen: set[str] = set()
	for row in evidence_doc.get("linked_documents") or []:
		doctype = str(row.get("source_doctype") or "").strip()
		docname = str(row.get("source_name") or "").strip()
		if not doctype or not docname:
			continue
		for file_row in frappe.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": docname},
			fields=["name", "file_name", "file_url", "attached_to_doctype", "attached_to_name"],
			limit=500,
		):
			file_name = str(file_row.get("name") or "")
			if file_name in seen:
				continue
			seen.add(file_name)
			files.append(file_row)

	for file_row in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "EvidencePack", "attached_to_name": evidence_doc.name},
		fields=["name", "file_name", "file_url", "attached_to_doctype", "attached_to_name"],
		limit=200,
	):
		file_name = str(file_row.get("name") or "")
		if file_name in seen:
			continue
		seen.add(file_name)
		files.append(file_row)

	return files


def _build_zip_bytes(evidence_doc: Any, files: list[dict[str, Any]], counts: dict[str, int]) -> bytes:
	buffer = io.BytesIO()
	written_names: set[str] = set()

	with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
		manifest = {
			"evidence_pack": evidence_doc.name,
			"site": evidence_doc.get("site"),
			"from_date": evidence_doc.get("from_date"),
			"to_date": evidence_doc.get("to_date"),
			"generated_at": frappe.utils.now_datetime().isoformat(),
			"record_count": _safe_int(evidence_doc.get("record_count"), 0),
			"source_counts": counts,
			"file_count": len(files),
		}
		bundle.writestr(
			"manifest.json",
			json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
		)

		for file_row in files:
			file_name = str(file_row.get("name") or "").strip()
			if not file_name:
				continue
			try:
				file_doc = frappe.get_doc("File", file_name)
				content = file_doc.get_content()
			except Exception:
				continue

			if content is None:
				continue
			if isinstance(content, str):
				content = content.encode("utf-8")

			doctype_segment = _safe_zip_segment(str(file_row.get("attached_to_doctype") or "Record"))
			docname_segment = _safe_zip_segment(str(file_row.get("attached_to_name") or "Item"))
			base_name = _safe_zip_segment(str(file_row.get("file_name") or file_row.get("file_url") or file_name))
			zip_name = f"records/{doctype_segment}/{docname_segment}/{base_name}"

			suffix = 1
			candidate = zip_name
			while candidate in written_names:
				suffix += 1
				candidate = f"records/{doctype_segment}/{docname_segment}/{suffix}_{base_name}"
			zip_name = candidate
			written_names.add(zip_name)
			bundle.writestr(zip_name, content)

		if not files:
			bundle.writestr(
				"README.txt",
				"No linked file attachments were found. Generate/upload files on linked records and re-export.",
			)

	return buffer.getvalue()


@frappe.whitelist()
def generate_evidence_pack_links(
	evidence_pack: str,
	rebuild: int = 1,
	include_quarantine: int = 1,
) -> dict[str, Any]:
	"""Build EvidencePack linked-document rows for scoped records."""
	_assert_role_gate(_("generate evidence packs"))
	evidence_doc = _resolve_evidence_pack_doc(evidence_pack, permission_type="write")

	rows, counts = _collect_scope_rows(
		evidence_doc,
		include_quarantine=bool(_safe_int(include_quarantine, 1)),
	)
	if _safe_int(rebuild, 1) == 1:
		evidence_doc.set("linked_documents", [])

	for row in rows:
		evidence_doc.append("linked_documents", row)

	evidence_doc.generated_at = frappe.utils.now_datetime()
	evidence_doc.generated_by = frappe.session.user
	evidence_doc.record_count = len(rows)
	if str(evidence_doc.get("status") or "").strip() in {"Draft", "Prepared"}:
		evidence_doc.status = "Ready"
	evidence_doc.save()

	return {
		"ok": True,
		"evidence_pack": evidence_doc.name,
		"site": evidence_doc.site,
		"status": evidence_doc.status,
		"record_count": len(rows),
		"counts": counts,
	}


@frappe.whitelist()
def export_evidence_pack_pdf(evidence_pack: str) -> dict[str, Any]:
	"""Render and attach a PDF export for the EvidencePack."""
	_assert_role_gate(_("export EvidencePack PDF"))
	evidence_doc = _resolve_evidence_pack_doc(evidence_pack, permission_type="write")

	linked_rows = []
	for row in evidence_doc.get("linked_documents") or []:
		linked_rows.append(
			{
				"source_doctype": row.get("source_doctype"),
				"source_name": row.get("source_name"),
				"site": row.get("site"),
				"document_date": row.get("document_date"),
				"status": row.get("status"),
				"attachment_count": row.get("attachment_count"),
				"summary": row.get("summary"),
			}
		)
	counts: dict[str, int] = {}
	for row in linked_rows:
		doctype = str(row.get("source_doctype") or "")
		if doctype:
			counts[doctype] = counts.get(doctype, 0) + 1

	html = _render_pdf_html(evidence_doc, linked_rows, counts)
	pdf_content = get_pdf(html)
	if isinstance(pdf_content, str):
		pdf_content = pdf_content.encode("utf-8")

	file_doc = save_file(
		f"{evidence_doc.name}-evidence-pack.pdf",
		pdf_content,
		"EvidencePack",
		evidence_doc.name,
		is_private=1,
	)
	evidence_doc.pdf_file = str(file_doc.file_url or "")
	if str(evidence_doc.get("status") or "").strip() in {"Draft", "Prepared"}:
		evidence_doc.status = "Ready"
	evidence_doc.save()

	return {
		"ok": True,
		"evidence_pack": evidence_doc.name,
		"status": evidence_doc.status,
		"pdf_file": evidence_doc.pdf_file,
		"narrative_included": bool(_accepted_ai_narrative(evidence_doc)),
	}


@frappe.whitelist()
def export_evidence_pack_zip(evidence_pack: str) -> dict[str, Any]:
	"""Bundle linked file attachments into a ZIP and attach it to EvidencePack."""
	_assert_role_gate(_("export EvidencePack ZIP"))
	evidence_doc = _resolve_evidence_pack_doc(evidence_pack, permission_type="write")

	counts: dict[str, int] = {}
	for row in evidence_doc.get("linked_documents") or []:
		doctype = str(row.get("source_doctype") or "")
		if doctype:
			counts[doctype] = counts.get(doctype, 0) + 1

	files = _collect_zip_sources(evidence_doc)
	zip_bytes = _build_zip_bytes(evidence_doc, files, counts)
	file_doc = save_file(
		f"{evidence_doc.name}-evidence-pack.zip",
		zip_bytes,
		"EvidencePack",
		evidence_doc.name,
		is_private=1,
	)
	evidence_doc.zip_file = str(file_doc.file_url or "")
	if str(evidence_doc.get("status") or "").strip() in {"Draft", "Prepared"}:
		evidence_doc.status = "Ready"
	evidence_doc.save()

	return {
		"ok": True,
		"evidence_pack": evidence_doc.name,
		"status": evidence_doc.status,
		"zip_file": evidence_doc.zip_file,
		"file_count": len(files),
	}


@frappe.whitelist()
def mark_evidence_pack_sent(evidence_pack: str) -> dict[str, Any]:
	"""Set EvidencePack status to Sent using server-side role gates."""
	_assert_role_gate(_("send EvidencePack"))
	evidence_doc = _resolve_evidence_pack_doc(evidence_pack, permission_type="write")
	evidence_doc.status = "Sent"
	evidence_doc.save()
	return {
		"ok": True,
		"evidence_pack": evidence_doc.name,
		"status": evidence_doc.status,
	}


@frappe.whitelist(allow_guest=True)
def get_auditor_evidence_pack_stub(
	site: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 50,
) -> dict[str, Any]:
	"""Read-only EvidencePack list stub for V1.2 auditor portal flow."""
	if frappe.session.user == "Guest":
		return {
			"ok": True,
			"enabled": False,
			"portal": "stub",
			"message": _(
				"Auditor guest portal token access is planned for V1.2. Sign in for internal read-only preview."
			),
			"records": [],
		}

	filters: dict[str, Any] = {
		"status": ["in", ["Ready", "Sent", "Approved"]],
	}
	if site:
		site_name = resolve_site(site)
		assert_site_access(site_name)
		filters["site"] = site_name
	else:
		user = frappe.session.user
		if not _has_global_site_access(user):
			allowed_sites = get_allowed_sites(user=user)
			if not allowed_sites:
				return {
					"ok": True,
					"enabled": True,
					"portal": "stub",
					"message": _("No EvidencePacks are visible for your Site permissions."),
					"records": [],
				}
			filters["site"] = ["in", allowed_sites]

	from_value = (from_date or "").strip()
	to_value = (to_date or "").strip()
	if from_value and to_value:
		filters["from_date"] = ["<=", to_value]
		filters["to_date"] = [">=", from_value]
	elif from_value:
		filters["to_date"] = [">=", from_value]
	elif to_value:
		filters["from_date"] = ["<=", to_value]

	safe_limit = max(1, min(_safe_int(limit, 50), _MAX_PORTAL_ROWS))
	rows = frappe.get_all(
		"EvidencePack",
		filters=filters,
		fields=[
			"name",
			"title",
			"site",
			"lot",
			"from_date",
			"to_date",
			"status",
			"record_count",
			"pdf_file",
			"zip_file",
			"modified",
		],
		order_by="modified desc",
		limit=safe_limit,
	)

	return {
		"ok": True,
		"enabled": True,
		"portal": "stub",
		"message": _(
			"Read-only auditor portal stub is active for internal users. Tokenized external access is planned for V1.2."
		),
		"records": rows,
	}
