from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

import frappe
from frappe import _

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access, resolve_site

QA_MANAGER_ROLE = "QA Manager"


def _resolve_repo_root() -> Path:
	if "yam_agri_core" in set(frappe.get_installed_apps() or []):
		app_path = Path(frappe.get_app_path("yam_agri_core")).resolve()
		for parent in app_path.parents:
			if (parent / "docs").exists() and (parent / "tools").exists():
				return parent
	return Path.cwd()


def _resolve_output_path(relative_or_absolute_path: str) -> Path:
	p = Path(relative_or_absolute_path)
	if p.is_absolute():
		return p
	return _resolve_repo_root() / relative_or_absolute_path


def _safe_float(value: Any) -> float | None:
	if value in (None, ""):
		return None
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def _fetch_site_tolerance_pct(site_name: str, override_policy: str | None = None) -> float:
	if frappe.db.exists("DocType", "Site Tolerance Policy"):
		filters: dict[str, Any] = {"site": site_name, "active": 1}
		if override_policy:
			filters["name"] = override_policy
		policy_row = frappe.get_all(
			"Site Tolerance Policy",
			filters=filters,
			fields=["name", "tolerance_pct", "from_date", "to_date"],
			order_by="modified desc",
			limit_page_length=20,
		)
		today = frappe.utils.nowdate()
		for row in policy_row:
			from_date = row.get("from_date")
			to_date = row.get("to_date")
			if from_date and str(from_date) > str(today):
				continue
			if to_date and str(to_date) < str(today):
				continue
			pct = _safe_float(row.get("tolerance_pct"))
			if pct and pct > 0:
				return float(pct)

	season_policy_pct = frappe.db.get_value(
		"Season Policy", {"site": site_name, "active": 1}, "max_test_age_days"
	)
	if season_policy_pct:
		_ = season_policy_pct

	return 2.5


def _resolve_lot_for_site(site_name: str, lot_ref: str) -> str | None:
	lot_ref = (lot_ref or "").strip()
	if not lot_ref:
		return None

	lot_name = frappe.db.get_value("Lot", {"name": lot_ref, "site": site_name}, "name")
	if lot_name:
		return str(lot_name)

	lot_by_number = frappe.db.get_value("Lot", {"lot_number": lot_ref, "site": site_name}, "name")
	if lot_by_number:
		return str(lot_by_number)

	return None


def _resolve_device_for_site(site_name: str, device_ref: str | None) -> str | None:
	device_ref = (device_ref or "").strip()
	if device_ref:
		device_name = frappe.db.get_value("Device", {"name": device_ref, "site": site_name}, "name")
		if device_name:
			return str(device_name)
		by_label = frappe.db.get_value("Device", {"device_name": device_ref, "site": site_name}, "name")
		if by_label:
			return str(by_label)

	fallback = frappe.db.get_value("Device", {"site": site_name, "status": "Active"}, "name")
	if fallback:
		return str(fallback)
	return None


def _compute_mismatch_pct(declared_net_kg: float, measured_net_kg: float) -> float:
	if declared_net_kg <= 0:
		return 0.0
	return round(abs(measured_net_kg - declared_net_kg) / declared_net_kg * 100.0, 4)


def _apply_lot_mutation(lot_name: str, measured_net_kg: float) -> dict[str, Any]:
	before_qty = float(frappe.db.get_value("Lot", lot_name, "qty_kg") or 0)
	after_qty = round(max(0.0, before_qty + measured_net_kg), 3)
	frappe.db.set_value("Lot", lot_name, "qty_kg", after_qty, update_modified=False)
	return {
		"lot": lot_name,
		"before_qty_kg": before_qty,
		"delta_kg": measured_net_kg,
		"after_qty_kg": after_qty,
	}


def _ensure_nonconformance_for_mismatch(
	*,
	site_name: str,
	lot_name: str,
	ticket_number: str,
	declared_net_kg: float,
	measured_net_kg: float,
	tolerance_pct: float,
	mismatch_pct: float,
) -> str:
	description = _(
		"P5-MISMATCH ticket={0}; declared={1}; measured={2}; mismatch_pct={3}; tolerance_pct={4}"
	).format(ticket_number, declared_net_kg, measured_net_kg, mismatch_pct, tolerance_pct)

	existing = frappe.db.get_value(
		"Nonconformance",
		{
			"site": site_name,
			"lot": lot_name,
			"capa_description": ["like", f"P5-MISMATCH ticket={ticket_number}%"],
		},
		"name",
	)
	if existing:
		return str(existing)

	nc = frappe.get_doc(
		{
			"doctype": "Nonconformance",
			"site": site_name,
			"lot": lot_name,
			"status": "Open",
			"capa_description": description,
		}
	)
	nc.insert(ignore_permissions=True)
	return str(nc.name)


def _parse_csv_rows(csv_content: str) -> list[dict[str, Any]]:
	reader = csv.DictReader(io.StringIO(csv_content or ""))
	return [dict(row or {}) for row in reader]


def _write_import_artifact(
	*,
	artifact_file: str,
	site_name: str,
	tolerance_pct: float,
	summary: dict[str, Any],
	rows_result: list[dict[str, Any]],
	mutation_log: list[dict[str, Any]],
) -> str:
	artifact_path = _resolve_output_path(artifact_file)
	artifact_path.parent.mkdir(parents=True, exist_ok=True)

	payload = {
		"phase": "Phase 5",
		"generated_at": frappe.utils.now_datetime().isoformat(),
		"site": site_name,
		"tolerance_pct": tolerance_pct,
		"summary": summary,
		"rows": rows_result,
		"mutation_log": mutation_log,
	}
	artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

	csv_path = artifact_path.with_suffix(".csv")
	headers = ["row_no", "ticket_number", "result", "reason", "mismatch_pct", "nonconformance"]
	lines = [",".join(headers)]
	for row in rows_result:
		lines.append(
			",".join(
				[
					str(row.get("row_no") or ""),
					str(row.get("ticket_number") or ""),
					str(row.get("result") or ""),
					str(row.get("reason") or ""),
					str(row.get("mismatch_pct") or ""),
					str(row.get("nonconformance") or ""),
				]
			)
		)
	csv_path.write_text("\n".join(lines), encoding="utf-8")

	return str(artifact_path)


@frappe.whitelist()
def import_scale_tickets_csv(
	site: str,
	csv_content: str,
	tolerance_policy: str | None = None,
	dry_run: int = 0,
	write_artifact: int = 1,
	artifact_file: str = "artifacts/evidence/phase5_at07_at08/at07_import_log.json",
) -> dict[str, Any]:
	"""Import ScaleTicket rows from CSV content with schema validation and auto-NC on mismatch.

	Required CSV columns:
	- ticket_number
	- lot
	- gross_kg
	- tare_kg
	- declared_net_kg
	- device (optional if one active device exists at site)
	"""

	site_name = resolve_site(site)
	assert_site_access(site_name)

	tolerance_pct = _fetch_site_tolerance_pct(site_name, override_policy=tolerance_policy)
	rows = _parse_csv_rows(csv_content)

	required_columns = ["ticket_number", "lot", "gross_kg", "tare_kg", "declared_net_kg"]
	results: list[dict[str, Any]] = []
	mutation_log: list[dict[str, Any]] = []

	summary = {
		"rows_total": len(rows),
		"rows_clean": 0,
		"rows_schema_error": 0,
		"rows_mismatch_pass": 0,
		"rows_mismatch_fail": 0,
		"scale_tickets_created": 0,
		"nonconformance_created": 0,
	}

	for idx, row in enumerate(rows, start=1):
		row_no = idx
		ticket_number = (row.get("ticket_number") or "").strip()
		lot_ref = (row.get("lot") or "").strip()
		device_ref = (row.get("device") or "").strip()

		missing_cols = [col for col in required_columns if (row.get(col) or "").strip() == ""]
		if missing_cols:
			summary["rows_schema_error"] += 1
			results.append(
				{
					"row_no": row_no,
					"ticket_number": ticket_number,
					"result": "rejected",
					"reason": _("Missing required columns: {0}").format(", ".join(missing_cols)),
				}
			)
			continue

		gross = _safe_float(row.get("gross_kg"))
		tare = _safe_float(row.get("tare_kg"))
		declared = _safe_float(row.get("declared_net_kg"))
		if gross is None or tare is None or declared is None:
			summary["rows_schema_error"] += 1
			results.append(
				{
					"row_no": row_no,
					"ticket_number": ticket_number,
					"result": "rejected",
					"reason": _("gross_kg, tare_kg and declared_net_kg must be numeric"),
				}
			)
			continue

		measured = round(gross - tare, 3)
		if measured < 0:
			summary["rows_schema_error"] += 1
			results.append(
				{
					"row_no": row_no,
					"ticket_number": ticket_number,
					"result": "rejected",
					"reason": _("Measured net_kg cannot be negative"),
				}
			)
			continue

		lot_name = _resolve_lot_for_site(site_name, lot_ref)
		if not lot_name:
			summary["rows_schema_error"] += 1
			results.append(
				{
					"row_no": row_no,
					"ticket_number": ticket_number,
					"result": "rejected",
					"reason": _("Lot not found for this Site"),
				}
			)
			continue

		device_name = _resolve_device_for_site(site_name, device_ref)
		if not device_name:
			summary["rows_schema_error"] += 1
			results.append(
				{
					"row_no": row_no,
					"ticket_number": ticket_number,
					"result": "rejected",
					"reason": _("No active Device found for this Site"),
				}
			)
			continue

		existing_ticket = frappe.db.get_value(
			"ScaleTicket", {"site": site_name, "ticket_number": ticket_number}, "name"
		)
		if existing_ticket:
			results.append(
				{
					"row_no": row_no,
					"ticket_number": ticket_number,
					"result": "skipped",
					"reason": _("ScaleTicket already exists"),
				}
			)
			continue

		mismatch_pct = _compute_mismatch_pct(declared, measured)
		is_mismatch_fail = mismatch_pct > tolerance_pct
		if is_mismatch_fail:
			summary["rows_mismatch_fail"] += 1
		else:
			if mismatch_pct > 0:
				summary["rows_mismatch_pass"] += 1
			else:
				summary["rows_clean"] += 1

		nc_name = ""
		ticket_name = ""
		if int(dry_run) != 1:
			ticket = frappe.get_doc(
				{
					"doctype": "ScaleTicket",
					"ticket_number": ticket_number,
					"site": site_name,
					"device": device_name,
					"lot": lot_name,
					"ticket_datetime": row.get("ticket_datetime") or frappe.utils.now_datetime(),
					"gross_kg": gross,
					"tare_kg": tare,
					"net_kg": measured,
					"vehicle": (row.get("vehicle") or "").strip(),
					"driver": (row.get("driver") or "").strip(),
					"notes": _("AT-07 CSV import declared={0} measured={1} mismatch_pct={2}").format(
						declared, measured, mismatch_pct
					),
				}
			)
			ticket.insert(ignore_permissions=True)
			ticket_name = str(ticket.name)
			summary["scale_tickets_created"] += 1

			mutation = _apply_lot_mutation(lot_name, measured)
			mutation_log.append(
				{
					"row_no": row_no,
					"ticket": ticket_name,
					"lot": lot_name,
					"before_qty_kg": mutation.get("before_qty_kg"),
					"after_qty_kg": mutation.get("after_qty_kg"),
					"delta_kg": mutation.get("delta_kg"),
				}
			)

			if is_mismatch_fail:
				nc_name = _ensure_nonconformance_for_mismatch(
					site_name=site_name,
					lot_name=lot_name,
					ticket_number=ticket_number,
					declared_net_kg=declared,
					measured_net_kg=measured,
					tolerance_pct=tolerance_pct,
					mismatch_pct=mismatch_pct,
				)
				summary["nonconformance_created"] += 1

		results.append(
			{
				"row_no": row_no,
				"ticket_number": ticket_number,
				"result": "imported" if int(dry_run) != 1 else "dry_run",
				"reason": "",
				"mismatch_pct": mismatch_pct,
				"nonconformance": nc_name,
				"ticket": ticket_name,
			}
		)

	if int(dry_run) != 1:
		frappe.db.commit()

	artifact_path = ""
	if int(write_artifact) == 1:
		artifact_path = _write_import_artifact(
			artifact_file=artifact_file,
			site_name=site_name,
			tolerance_pct=tolerance_pct,
			summary=summary,
			rows_result=results,
			mutation_log=mutation_log,
		)

	return {
		"status": "ok",
		"site": site_name,
		"dry_run": int(dry_run),
		"tolerance_pct": tolerance_pct,
		"summary": summary,
		"artifact_file": artifact_path,
		"rows": results,
	}


@frappe.whitelist()
def close_nonconformance_with_qa(nc_name: str) -> dict[str, Any]:
	"""Close a Nonconformance with explicit server-side QA role gate."""

	if not nc_name:
		frappe.throw(_("Nonconformance name is required"), frappe.ValidationError)

	if not frappe.has_role(QA_MANAGER_ROLE):
		frappe.throw(
			_("Only a user with role '{0}' may close Nonconformance").format(QA_MANAGER_ROLE),
			frappe.PermissionError,
		)

	nc = frappe.get_doc("Nonconformance", nc_name)
	nc.status = "Closed"
	nc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "ok", "nonconformance": nc.name, "new_status": nc.status}
