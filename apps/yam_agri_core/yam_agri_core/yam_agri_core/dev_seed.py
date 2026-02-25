from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe
from frappe import _, utils

BASELINE_DOCTYPES = (
	"Site",
	"StorageBin",
	"Lot",
	"QCTest",
	"Certificate",
	"Device",
	"Observation",
	"ScaleTicket",
	"Transfer",
	"EvidencePack",
	"Complaint",
)


def seed_dev_org_chart_if_enabled() -> None:
	"""Seed a small org chart in dev only.

	This is intentionally minimal and idempotent:
	- Creates a few Departments and Designations.
	- Does not create Users by default (avoids auth/security surprises).
	"""

	if not _should_seed():
		return

	for dept in [
		"YAM Agri",
		"Operations",
		"Quality Assurance",
		"Warehouse",
		"Procurement",
		"Sales",
		"Finance",
		"IT",
	]:
		_ensure_department(dept)

	for desg in [
		"General Manager",
		"Operations Manager",
		"QA Manager",
		"QC Technician",
		"Warehouse Supervisor",
		"Warehouse Operator",
		"Procurement Officer",
		"Sales Executive",
		"Accountant",
		"System Administrator",
	]:
		_ensure_designation(desg)

	frappe.db.commit()


def seed_dev_baseline_demo_data_if_enabled() -> None:
	"""Seed minimal baseline demo data in dev only.

	Creates (idempotent):
	- one Site (if none exist)
	- one Device
	- one Observation
	- one ScaleTicket
	- one Transfer
	- one EvidencePack
	- one Complaint

	This is convenience-only for local development; it's guarded by developer_mode.
	"""

	if not _should_seed_baseline():
		return

	site = _ensure_default_site()
	_ensure_demo_storage_bin(site)
	lot = _ensure_demo_lot(site)
	_ensure_demo_qc_test(site, lot)
	_ensure_demo_certificate(site, lot)
	device = _ensure_demo_device(site)
	_ensure_demo_observation(site, device)
	_ensure_demo_scale_ticket(site, device)
	_ensure_demo_transfer(site)
	_ensure_demo_evidence_pack(site)
	_ensure_demo_complaint(site)

	frappe.db.commit()


def seed_baseline_demo_data_force() -> None:
	"""Force-seed baseline demo data (idempotent).

	Use via:
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_baseline_demo_data_force

	This bypasses developer_mode guards, but still only inserts minimal records
	and uses ignore_permissions=True.
	"""

	# Require our baseline DocTypes.
	for dt in BASELINE_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			frappe.throw(_("Missing DocType: {0}").format(dt))

	site = _ensure_default_site()
	_ensure_demo_storage_bin(site)
	lot = _ensure_demo_lot(site)
	_ensure_demo_qc_test(site, lot)
	_ensure_demo_certificate(site, lot)
	device = _ensure_demo_device(site)
	_ensure_demo_observation(site, device)
	_ensure_demo_scale_ticket(site, device)
	_ensure_demo_transfer(site)
	_ensure_demo_evidence_pack(site)
	_ensure_demo_complaint(site)

	frappe.db.commit()


def _should_seed() -> bool:
	# Default: only in developer mode.
	if not frappe.conf.get("developer_mode"):
		return False

	# Optional hard-disable/enable toggles.
	if frappe.conf.get("yam_agri_disable_dev_seed"):
		return False
	if frappe.conf.get("yam_agri_enable_dev_seed") is False:
		return False

	# DocTypes exist only when ERPNext HR is present.
	if not frappe.db.exists("DocType", "Department"):
		return False
	if not frappe.db.exists("DocType", "Designation"):
		return False

	return True


def _should_seed_baseline() -> bool:
	# Same guard philosophy as org-chart seed.
	if not frappe.conf.get("developer_mode"):
		return False

	if frappe.conf.get("yam_agri_disable_dev_seed"):
		return False
	if frappe.conf.get("yam_agri_enable_dev_seed") is False:
		return False

	# Require our baseline DocTypes.
	for dt in BASELINE_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			return False

	return True


def _ensure_default_site() -> str:
	# Use existing first Site if available.
	name = frappe.db.get_value("Site", {}, "name")
	if name:
		return str(name)

	# Create a minimal Site (only site_name is required by our controller).
	doc = frappe.get_doc(
		{
			"doctype": "Site",
			"site_name": "Dev Site",
			"site_type": "Warehouse",
			"description": "Auto-seeded for developer mode",
		}
	)
	doc.insert(ignore_permissions=True)
	return str(doc.name)


def _ensure_demo_storage_bin(site: str) -> str:
	bin_name = "Dev Storage Bin"
	existing = frappe.db.get_value(
		"StorageBin",
		{"site": site, "storage_bin_name": bin_name},
		"name",
	)
	if existing:
		return str(existing)

	doc = frappe.get_doc(
		{
			"doctype": "StorageBin",
			"storage_bin_name": bin_name,
			"site": site,
			"capacity_kg": 2000.0,
			"current_qty_kg": 100.0,
			"status": "Active",
			"notes": "Auto-seeded for developer mode",
		}
	)
	doc.insert(ignore_permissions=True)
	return str(doc.name)


def _ensure_demo_lot(site: str) -> str:
	lot_number = "DEV-LOT-0001"
	existing = frappe.db.get_value("Lot", {"site": site, "lot_number": lot_number}, "name")
	if existing:
		return str(existing)

	doc = frappe.get_doc(
		{
			"doctype": "Lot",
			"lot_number": lot_number,
			"site": site,
			"qty_kg": 100.0,
			"status": "Draft",
		}
	)
	doc.insert(ignore_permissions=True)
	return str(doc.name)


def _ensure_demo_qc_test(site: str, lot: str) -> str:
	test_type = "Moisture"
	existing = frappe.db.get_value(
		"QCTest",
		{"site": site, "lot": lot, "test_type": test_type, "pass_fail": "Pass"},
		"name",
	)
	if existing:
		return str(existing)

	doc = frappe.get_doc(
		{
			"doctype": "QCTest",
			"lot": lot,
			"site": site,
			"test_type": test_type,
			"test_date": utils.nowdate(),
			"result_value": 12.5,
			"pass_fail": "Pass",
		}
	)
	doc.insert(ignore_permissions=True)
	return str(doc.name)


def _ensure_demo_certificate(site: str, lot: str) -> str:
	cert_type = "Dev COA"
	existing = frappe.db.get_value(
		"Certificate",
		{"site": site, "lot": lot, "cert_type": cert_type},
		"name",
	)
	if existing:
		return str(existing)

	doc = frappe.get_doc(
		{
			"doctype": "Certificate",
			"cert_type": cert_type,
			"lot": lot,
			"site": site,
			"expiry_date": utils.add_days(utils.nowdate(), 365),
		}
	)
	doc.insert(ignore_permissions=True)
	return str(doc.name)


def _ensure_demo_device(site: str) -> str:
	device_name = "Dev Device"
	existing = frappe.db.get_value("Device", {"site": site, "device_name": device_name}, "name")
	if existing:
		return str(existing)

	doc = frappe.get_doc(
		{
			"doctype": "Device",
			"device_name": device_name,
			"site": site,
			"device_type": "Other",
			"serial_number": "DEV-0001",
			"status": "Active",
			"notes": "Auto-seeded for developer mode",
		}
	)
	doc.insert(ignore_permissions=True)
	return str(doc.name)


def _ensure_demo_observation(site: str, device: str) -> None:
	# Idempotency: allow only one seeded row.
	existing = frappe.db.get_value(
		"Observation",
		{"site": site, "device": device, "observation_type": "dev.seed"},
		"name",
	)
	if existing:
		return

	frappe.get_doc(
		{
			"doctype": "Observation",
			"site": site,
			"device": device,
			"observed_at": utils.now_datetime(),
			"observation_type": "dev.seed",
			"value": 1.0,
			"unit": "count",
			"quality_flag": "OK",
			"raw_payload": '{"seed": true}',
		}
	).insert(ignore_permissions=True)


def _ensure_demo_scale_ticket(site: str, device: str) -> None:
	existing = frappe.db.get_value(
		"ScaleTicket",
		{"site": site, "device": device, "ticket_number": "DEV-TICKET-0001"},
		"name",
	)
	if existing:
		return

	frappe.get_doc(
		{
			"doctype": "ScaleTicket",
			"ticket_number": "DEV-TICKET-0001",
			"site": site,
			"device": device,
			"ticket_datetime": utils.now_datetime(),
			"gross_kg": 100.0,
			"tare_kg": 10.0,
			"vehicle": "DEV-TRUCK",
			"driver": "Dev Driver",
			"notes": "Auto-seeded for developer mode",
		}
	).insert(ignore_permissions=True)


def _ensure_demo_transfer(site: str) -> None:
	existing = frappe.db.get_value(
		"Transfer",
		{"site": site, "transfer_type": "Move", "qty_kg": 1.0, "status": "Draft"},
		"name",
	)
	if existing:
		return

	frappe.get_doc(
		{
			"doctype": "Transfer",
			"site": site,
			"transfer_type": "Move",
			"qty_kg": 1.0,
			"transfer_datetime": utils.now_datetime(),
			"status": "Draft",
			"notes": "Auto-seeded for developer mode",
		}
	).insert(ignore_permissions=True)


def _ensure_demo_evidence_pack(site: str) -> None:
	existing = frappe.db.get_value(
		"EvidencePack",
		{"site": site, "title": "Dev Evidence Pack", "status": "Draft"},
		"name",
	)
	if existing:
		return

	frappe.get_doc(
		{
			"doctype": "EvidencePack",
			"title": "Dev Evidence Pack",
			"site": site,
			"from_date": utils.nowdate(),
			"to_date": utils.nowdate(),
			"status": "Draft",
			"notes": "Auto-seeded for developer mode",
		}
	).insert(ignore_permissions=True)


def _ensure_demo_complaint(site: str) -> None:
	existing = frappe.db.get_value(
		"Complaint",
		{"site": site, "customer_name": "Dev Customer", "status": "Open"},
		"name",
	)
	if existing:
		return

	frappe.get_doc(
		{
			"doctype": "Complaint",
			"site": site,
			"complaint_date": utils.nowdate(),
			"customer_name": "Dev Customer",
			"description": "Auto-seeded for developer mode",
			"status": "Open",
		}
	).insert(ignore_permissions=True)


def check_site_isolation_coverage() -> dict[str, Any]:
	"""Return gaps between DocTypes that have a `site` field and hook coverage.

	Use via:
	- bench execute yam_agri_core.yam_agri_core.dev_seed.check_site_isolation_coverage

	This is a diagnostic helper; it does not change data.
	"""

	# Import hooks module directly to read mapping.
	from yam_agri_core import hooks as app_hooks

	permission_map = getattr(app_hooks, "permission_query_conditions", {}) or {}
	covered_doctypes = set(permission_map.keys())

	# Focus on our module's doctypes to avoid scanning all installed apps.
	yam_doctypes = frappe.get_all(
		"DocType",
		filters={"module": "YAM Agri Core"},
		pluck="name",
	)

	needs_site_filter: list[str] = []
	missing_mapping: list[str] = []

	for dt in yam_doctypes:
		try:
			meta = frappe.get_meta(dt)
		except Exception:
			continue
		if not meta.has_field("site"):
			continue
		needs_site_filter.append(dt)
		if dt not in covered_doctypes:
			missing_mapping.append(dt)

	return {
		"yam_doctypes_with_site": sorted(needs_site_filter),
		"missing_permission_query_conditions": sorted(missing_mapping),
		"permission_query_conditions_count": len(covered_doctypes),
	}


def get_baseline_record_counts() -> dict[str, int]:
	"""Return record counts for baseline DocTypes.

	Use via:
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.get_baseline_record_counts
	"""

	counts: dict[str, int] = {}
	for dt in BASELINE_DOCTYPES:
		try:
			counts[dt] = int(frappe.db.count(dt))
		except Exception:
			counts[dt] = -1
	return counts


def _ensure_department(department_name: str) -> None:
	if frappe.db.exists("Department", department_name):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Department",
			"department_name": department_name,
			"is_group": 0,
		}
	)
	doc.insert(ignore_permissions=True)


def _ensure_designation(designation_name: str) -> None:
	if frappe.db.exists("Designation", designation_name):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Designation",
			"designation_name": designation_name,
		}
	)
	doc.insert(ignore_permissions=True)


def seed_m4_balanced_samples(confirm: int = 0, target_records: int = 140) -> dict[str, int | str]:
	"""Create balanced M4 sample data for QA/QC and season-policy gate testing.

	Use via:
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_m4_balanced_samples --kwargs '{"confirm":1, "target_records":140}'

	Behavior:
	- Requires confirm=1.
	- Ensures at least two Sites and active Season Policy per site.
	- Inserts mixed pass/fail QCTest and valid/expired Certificate scenarios.
	- Stops when selected core records total reaches target_records.
	"""

	if int(confirm) != 1:
		frappe.throw(_("Set confirm=1 to execute sample-data generation"))

	if int(target_records) < 20:
		frappe.throw(_("target_records must be at least 20"))

	for dt in (
		"Site",
		"StorageBin",
		"Device",
		"Lot",
		"QCTest",
		"Certificate",
		"Transfer",
		"ScaleTicket",
		"Season Policy",
	):
		if not frappe.db.exists("DocType", dt):
			frappe.throw(_("Missing DocType: {0}").format(dt))

	sites = frappe.get_all("Site", fields=["name"], limit_page_length=10)
	if not sites:
		sites = [{"name": _ensure_default_site()}]

	if len(sites) < 2:
		site_b = frappe.get_doc(
			{
				"doctype": "Site",
				"site_name": "M4 Site B",
				"site_type": "Warehouse",
				"description": "Auto-seeded M4 secondary site",
			}
		).insert(ignore_permissions=True)
		sites.append({"name": site_b.name})

	selected_sites = [sites[0]["name"], sites[1]["name"]]
	available_crops = frappe.get_all("Crop", pluck="name", limit_page_length=10)

	created = 0
	seed_tag = utils.now_datetime().strftime("%Y%m%d%H%M%S")

	def _core_total() -> int:
		return sum(
			[
				int(frappe.db.count("Season Policy")),
				int(frappe.db.count("Lot")),
				int(frappe.db.count("QCTest")),
				int(frappe.db.count("Certificate")),
				int(frappe.db.count("Transfer")),
				int(frappe.db.count("ScaleTicket")),
				int(frappe.db.count("Observation")),
			]
		)

	for site in selected_sites:
		policy_name = f"M4-Policy-{site[-4:]}"
		policy = frappe.db.exists("Season Policy", {"policy_name": policy_name, "site": site})
		if policy:
			policy_doc = frappe.get_doc("Season Policy", policy)
			policy_doc.season = "2026"
			policy_doc.mandatory_test_types = "Moisture,Protein"
			policy_doc.mandatory_certificate_types = "COA"
			policy_doc.max_test_age_days = 7
			policy_doc.enforce_dispatch_gate = 1
			policy_doc.active = 1
			policy_doc.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Season Policy",
					"policy_name": policy_name,
					"site": site,
					"season": "2026",
					"mandatory_test_types": "Moisture,Protein",
					"mandatory_certificate_types": "COA",
					"max_test_age_days": 7,
					"enforce_dispatch_gate": 1,
					"active": 1,
				}
			).insert(ignore_permissions=True)
			created += 1

		for i in range(1, 4):
			storage_bin_name = f"M4-BIN-{site[-4:]}-{i}"
			if not frappe.db.exists("StorageBin", {"storage_bin_name": storage_bin_name, "site": site}):
				frappe.get_doc(
					{
						"doctype": "StorageBin",
						"storage_bin_name": storage_bin_name,
						"site": site,
						"capacity_kg": 5000,
						"current_qty_kg": 0,
						"status": "Active",
					}
				).insert(ignore_permissions=True)
				created += 1

		device_name = f"M4-DEV-{site[-4:]}"
		if not frappe.db.exists("Device", {"device_name": device_name, "site": site}):
			frappe.get_doc(
				{
					"doctype": "Device",
					"device_name": device_name,
					"site": site,
					"device_type": "Scale",
					"status": "Active",
				}
			).insert(ignore_permissions=True)
			created += 1

	iteration = 1
	while _core_total() < int(target_records):
		site = selected_sites[iteration % len(selected_sites)]
		lot_number = f"M4-LOT-{seed_tag}-{iteration:03d}"
		lot_payload = {
			"doctype": "Lot",
			"lot_number": lot_number,
			"site": site,
			"qty_kg": 100 + iteration,
			"status": "Draft",
		}
		if available_crops:
			lot_payload["crop"] = available_crops[iteration % len(available_crops)]
		lot_doc = frappe.get_doc(lot_payload).insert(ignore_permissions=True)
		created += 1

		qct_pass = "Fail" if iteration % 7 == 0 else "Pass"
		test_age_days = 10 if iteration % 9 == 0 else 1
		qct_date = utils.add_days(utils.nowdate(), -test_age_days)
		frappe.get_doc(
			{
				"doctype": "QCTest",
				"lot": lot_doc.name,
				"site": site,
				"test_type": "Moisture",
				"test_date": qct_date,
				"result_value": 12.0,
				"pass_fail": qct_pass,
				"notes": f"M4-SEED-{seed_tag}",
			}
		).insert(ignore_permissions=True)
		created += 1

		frappe.get_doc(
			{
				"doctype": "QCTest",
				"lot": lot_doc.name,
				"site": site,
				"test_type": "Protein",
				"test_date": utils.nowdate(),
				"result_value": 11.0,
				"pass_fail": "Pass",
				"notes": f"M4-SEED-{seed_tag}",
			}
		).insert(ignore_permissions=True)
		created += 1

		expiry = utils.add_days(utils.nowdate(), -1 if iteration % 5 == 0 else 30)
		frappe.get_doc(
			{
				"doctype": "Certificate",
				"cert_type": "COA",
				"lot": lot_doc.name,
				"site": site,
				"expiry_date": expiry,
			}
		).insert(ignore_permissions=True)
		created += 1

		if iteration % 4 == 0:
			frappe.get_doc(
				{
					"doctype": "Certificate",
					"cert_type": "Origin",
					"lot": lot_doc.name,
					"site": site,
					"expiry_date": utils.add_days(utils.nowdate(), 45),
				}
			).insert(ignore_permissions=True)
			created += 1

		frappe.get_doc(
			{
				"doctype": "Transfer",
				"site": site,
				"transfer_type": "Move",
				"from_lot": lot_doc.name,
				"to_lot": lot_doc.name,
				"qty_kg": 1,
				"transfer_datetime": utils.now_datetime(),
				"status": "Draft",
				"notes": f"M4-SEED-{seed_tag}",
			}
		).insert(ignore_permissions=True)
		created += 1

		device_name = f"M4-DEV-{site[-4:]}"
		device_name_doc = frappe.db.get_value("Device", {"device_name": device_name, "site": site}, "name")
		if device_name_doc:
			frappe.get_doc(
				{
					"doctype": "ScaleTicket",
					"ticket_number": f"M4-ST-{seed_tag}-{iteration:03d}",
					"site": site,
					"device": device_name_doc,
					"lot": lot_doc.name,
					"ticket_datetime": utils.now_datetime(),
					"gross_kg": 120,
					"tare_kg": 20,
					"net_kg": 100,
				}
			).insert(ignore_permissions=True)
			created += 1

		if iteration % 3 == 0 and device_name_doc:
			frappe.get_doc(
				{
					"doctype": "Observation",
					"site": site,
					"device": device_name_doc,
					"observed_at": utils.now_datetime(),
					"observation_type": "temperature",
					"value": 28.0,
					"unit": "C",
					"quality_flag": "OK",
					"raw_payload": f'{{"seed":"{seed_tag}"}}',
				}
			).insert(ignore_permissions=True)
			created += 1

		iteration += 1

	frappe.db.commit()

	return {
		"status": "ok",
		"seed_tag": seed_tag,
		"target_records": int(target_records),
		"core_total": _core_total(),
		"created_records": created,
	}


def seed_phase4_yemen_dataset(
	confirm: int = 0,
	dataset_file: str = "artifacts/evidence/phase4_at02_at06/phase4_yemen_sample_data_250.json",
	limit: int = 250,
) -> dict[str, Any]:
	"""Import static Phase 4 Yemeni sample dataset into bench site DocTypes.

	Use via:
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_phase4_yemen_dataset --kwargs '{"confirm":1}'
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.seed_phase4_yemen_dataset --kwargs '{"confirm":1, "limit":250, "dataset_file":"artifacts/evidence/phase4_at02_at06/phase4_yemen_sample_data_250.json"}'
	"""

	if int(confirm) != 1:
		frappe.throw(_("Set confirm=1 to import Phase 4 dataset"))

	if int(limit) < 1:
		frappe.throw(_("limit must be at least 1"))

	for dt in (
		"Site",
		"Lot",
		"QCTest",
		"Certificate",
		"Transfer",
		"ScaleTicket",
		"Device",
		"Observation",
	):
		if not frappe.db.exists("DocType", dt):
			frappe.throw(_("Missing DocType: {0}").format(dt))

	dataset_path = _resolve_phase4_dataset_path(dataset_file)
	if not dataset_path:
		frappe.throw(_("Dataset file not found: {0}").format(dataset_file))

	try:
		payload = json.loads(dataset_path.read_text(encoding="utf-8"))
	except Exception as exc:
		frappe.throw(_("Failed to parse dataset JSON: {0}").format(str(exc)))

	records = payload.get("records") if isinstance(payload, dict) else None
	if not isinstance(records, list):
		frappe.throw(_("Dataset JSON must contain a 'records' array"))

	selected_records = records[: int(limit)]
	created = {
		"Site": 0,
		"Device": 0,
		"Lot": 0,
		"QCTest": 0,
		"Certificate": 0,
		"Transfer": 0,
		"ScaleTicket": 0,
		"Observation": 0,
	}
	skipped = 0

	for rec in selected_records:
		record_id = str(rec.get("record_id") or "").strip()
		if not record_id:
			skipped += 1
			continue

		site = _ensure_phase4_site(rec)
		if site.get("created"):
			created["Site"] += 1

		device = _ensure_phase4_device(site=site["name"], rec=rec)
		if device.get("created"):
			created["Device"] += 1

		lot = _ensure_phase4_lot(site=site["name"], rec=rec)
		if lot.get("created"):
			created["Lot"] += 1

		qct = _ensure_phase4_qctest(site=site["name"], lot=lot["name"], rec=rec)
		if qct.get("created"):
			created["QCTest"] += 1

		cert = _ensure_phase4_certificate(site=site["name"], lot=lot["name"], rec=rec)
		if cert.get("created"):
			created["Certificate"] += 1

		transfer = _ensure_phase4_transfer(site=site["name"], lot=lot["name"], rec=rec)
		if transfer.get("created"):
			created["Transfer"] += 1

		ticket = _ensure_phase4_scale_ticket(
			site=site["name"], device=device["name"], lot=lot["name"], rec=rec
		)
		if ticket.get("created"):
			created["ScaleTicket"] += 1

		observation = _ensure_phase4_observation(site=site["name"], device=device["name"], rec=rec)
		if observation.get("created"):
			created["Observation"] += 1

	frappe.db.commit()

	return {
		"status": "ok",
		"dataset_file": str(dataset_path),
		"requested_limit": int(limit),
		"records_in_file": len(records),
		"records_processed": len(selected_records),
		"records_skipped": skipped,
		"created": created,
	}


def verify_phase4_yemen_dataset(
	dataset_file: str = "artifacts/evidence/phase4_at02_at06/phase4_yemen_sample_data_250.json",
	limit: int = 250,
) -> dict[str, Any]:
	"""Verify expected vs observed records for imported Phase 4 Yemen dataset.

	Use via:
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.verify_phase4_yemen_dataset
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.verify_phase4_yemen_dataset --kwargs '{"limit":250}'
	"""

	if int(limit) < 1:
		frappe.throw(_("limit must be at least 1"))

	dataset_path = _resolve_phase4_dataset_path(dataset_file)
	if not dataset_path:
		frappe.throw(_("Dataset file not found: {0}").format(dataset_file))

	try:
		payload = json.loads(dataset_path.read_text(encoding="utf-8"))
	except Exception as exc:
		frappe.throw(_("Failed to parse dataset JSON: {0}").format(str(exc)))

	all_records = payload.get("records") if isinstance(payload, dict) else None
	if not isinstance(all_records, list):
		frappe.throw(_("Dataset JSON must contain a 'records' array"))

	records = all_records[: int(limit)]
	record_ids = [str(r.get("record_id") or "").strip() for r in records if r.get("record_id")]
	record_ids_set = set(record_ids)
	lot_numbers = [str(r.get("lot") or "").strip() for r in records if r.get("lot")]

	expected_by_site: dict[str, int] = {}
	expected_by_governorate: dict[str, int] = {}
	expected_doc_counts = {
		"QCTest": 0,
		"Certificate": 0,
		"Transfer": 0,
		"ScaleTicket": 0,
		"Observation": 0,
	}
	for rec in records:
		site = str(rec.get("site") or "").strip()
		gov = str(rec.get("governorate") or "").strip()
		if site:
			expected_by_site[site] = expected_by_site.get(site, 0) + 1
		if gov:
			expected_by_governorate[gov] = expected_by_governorate.get(gov, 0) + 1

		# Import behavior expectations from seed_phase4_yemen_dataset
		expected_doc_counts["ScaleTicket"] += 1
		expected_doc_counts["Observation"] += 1
		if str(rec.get("qc_state") or "Missing").strip() != "Missing":
			expected_doc_counts["QCTest"] += 1
		if str(rec.get("certificate_state") or "Missing").strip() != "Missing":
			expected_doc_counts["Certificate"] += 1
		if str(rec.get("transfer_type") or "None").strip() != "None":
			expected_doc_counts["Transfer"] += 1

	qct_meta = frappe.get_meta("QCTest")
	qct_fields = ["name", "site", "lot", "test_type"]
	if qct_meta.has_field("notes"):
		qct_fields.append("notes")

	if qct_meta.has_field("notes"):
		qct_rows = frappe.get_all(
			"QCTest",
			filters={"notes": ["like", "P4-YEMEN-%"]},
			fields=qct_fields,
			limit_page_length=4000,
		)
	else:
		qct_rows = frappe.get_all(
			"QCTest", filters={"test_type": "Moisture"}, fields=qct_fields, limit_page_length=4000
		)

	def _transfer_record_id(note: str) -> str:
		prefix = "P4-YEMEN-"
		if not note.startswith(prefix):
			return ""
		remainder = note[len(prefix) :]
		parts = remainder.split("-")
		if len(parts) < 3:
			return ""
		return "-".join(parts[:3])

	qct_filtered = []
	if qct_meta.has_field("notes"):
		for row in qct_rows:
			notes = str(row.get("notes") or "")
			rec_id = notes.replace("P4-YEMEN-", "", 1)
			if rec_id in record_ids_set:
				qct_filtered.append(row)
	else:
		lot_numbers_set = set(lot_numbers)
		for row in qct_rows:
			if str(row.get("lot") or "") in lot_numbers_set and str(row.get("test_type") or "") == "Moisture":
				qct_filtered.append(row)

	lot_rows = frappe.get_all(
		"Lot",
		filters={"lot_number": ["in", lot_numbers or ["__none__"]]},
		fields=["name", "site", "lot_number"],
		limit_page_length=2000,
	)
	lot_names = {str(row.get("name") or "") for row in lot_rows if row.get("name")}

	observed_by_site: dict[str, int] = {}
	site_ids = {str(row.get("site") or "") for row in lot_rows if row.get("site")}
	site_name_rows = frappe.get_all(
		"Site",
		filters={"name": ["in", list(site_ids) or ["__none__"]]},
		fields=["name", "site_name"],
		limit_page_length=500,
	)
	site_id_to_code = {
		str(row.get("name") or ""): str(row.get("site_name") or row.get("name") or "")
		for row in site_name_rows
	}
	for row in lot_rows:
		site_id = str(row.get("site") or "").strip()
		site_code = site_id_to_code.get(site_id, site_id)
		if site_code:
			observed_by_site[site_code] = observed_by_site.get(site_code, 0) + 1

	if not qct_meta.has_field("notes"):
		qct_filtered = []
		for row in qct_rows:
			if str(row.get("lot") or "") in lot_names and str(row.get("test_type") or "") == "Moisture":
				qct_filtered.append(row)

	# Map site -> governorate using dataset content
	site_to_gov = {
		str(rec.get("site") or "").strip(): str(rec.get("governorate") or "").strip() for rec in records
	}
	observed_by_governorate: dict[str, int] = {}
	for site, count in observed_by_site.items():
		gov = site_to_gov.get(site, "")
		if gov:
			observed_by_governorate[gov] = observed_by_governorate.get(gov, 0) + count

	cert_rows = frappe.get_all(
		"Certificate",
		filters={"cert_type": ["like", "P4-COA-%"]},
		fields=["name", "cert_type"],
		limit_page_length=2000,
	)
	cert_filtered = [
		row
		for row in cert_rows
		if str(row.get("cert_type") or "").replace("P4-COA-", "", 1) in record_ids_set
	]

	transfer_rows = frappe.get_all(
		"Transfer",
		filters={"notes": ["like", "P4-YEMEN-%"]},
		fields=["name", "notes"],
		limit_page_length=4000,
	)
	transfer_filtered = [
		row for row in transfer_rows if _transfer_record_id(str(row.get("notes") or "")) in record_ids_set
	]

	ticket_rows = frappe.get_all(
		"ScaleTicket",
		filters={"ticket_number": ["like", "P4-ST-%"]},
		fields=["name", "ticket_number"],
		limit_page_length=2000,
	)
	ticket_filtered = [
		row
		for row in ticket_rows
		if str(row.get("ticket_number") or "").replace("P4-ST-", "", 1) in record_ids_set
	]

	observation_rows = frappe.get_all(
		"Observation",
		filters={"observation_type": ["like", "p4.seed.%"]},
		fields=["name", "observation_type"],
		limit_page_length=2000,
	)
	observation_filtered = [
		row
		for row in observation_rows
		if str(row.get("observation_type") or "").replace("p4.seed.", "", 1) in record_ids_set
	]

	observed_doc_counts = {
		"QCTest": len(qct_filtered),
		"Certificate": len(cert_filtered),
		"Transfer": len(transfer_filtered),
		"ScaleTicket": len(ticket_filtered),
		"Observation": len(observation_filtered),
	}

	missing_sites = sorted(set(expected_by_site.keys()) - set(observed_by_site.keys()))

	return {
		"status": "ok",
		"dataset_file": str(dataset_path),
		"limit": int(limit),
		"expected_records": len(records),
		"observed_qct_records": len(qct_filtered),
		"expected_by_site": dict(sorted(expected_by_site.items())),
		"observed_by_site": dict(sorted(observed_by_site.items())),
		"expected_by_governorate": dict(sorted(expected_by_governorate.items())),
		"observed_by_governorate": dict(sorted(observed_by_governorate.items())),
		"expected_doc_counts": expected_doc_counts,
		"observed_doc_counts": observed_doc_counts,
		"missing_sites": missing_sites,
	}


def verify_phase4_yemen_dataset_gate(
	dataset_file: str = "artifacts/evidence/phase4_at02_at06/phase4_yemen_sample_data_250.json",
	limit: int = 250,
	strict: int = 1,
) -> dict[str, Any]:
	"""Return PASS/FAIL gate result for Phase 4 Yemen dataset import.

	Use via:
	- bench --site localhost execute yam_agri_core.yam_agri_core.dev_seed.verify_phase4_yemen_dataset_gate --kwargs '{"limit":250}'
	"""

	result = verify_phase4_yemen_dataset(dataset_file=dataset_file, limit=limit)

	expected_records = int(result.get("expected_records") or 0)
	observed_qct_records = int(result.get("observed_qct_records") or 0)
	expected_by_site = result.get("expected_by_site") or {}
	observed_by_site = result.get("observed_by_site") or {}
	expected_by_governorate = result.get("expected_by_governorate") or {}
	observed_by_governorate = result.get("observed_by_governorate") or {}
	expected_doc_counts = result.get("expected_doc_counts") or {}
	observed_doc_counts = result.get("observed_doc_counts") or {}

	mismatches: list[dict[str, Any]] = []

	if observed_qct_records != int(expected_doc_counts.get("QCTest") or 0):
		mismatches.append(
			{
				"scope": "QCTest total",
				"expected": int(expected_doc_counts.get("QCTest") or 0),
				"observed": observed_qct_records,
			}
		)

	for site, expected in sorted(expected_by_site.items()):
		observed = int(observed_by_site.get(site) or 0)
		if observed != int(expected):
			mismatches.append(
				{
					"scope": "Site",
					"key": site,
					"expected": int(expected),
					"observed": observed,
				}
			)

	for gov, expected in sorted(expected_by_governorate.items()):
		observed = int(observed_by_governorate.get(gov) or 0)
		if observed != int(expected):
			mismatches.append(
				{
					"scope": "Governorate",
					"key": gov,
					"expected": int(expected),
					"observed": observed,
				}
			)

	for dt in ("Certificate", "Transfer", "ScaleTicket", "Observation"):
		observed = int(observed_doc_counts.get(dt) or 0)
		expected = int(expected_doc_counts.get(dt) or 0)
		if observed != expected:
			mismatches.append(
				{
					"scope": "DocType total",
					"key": dt,
					"expected": expected,
					"observed": observed,
				}
			)

	status = "pass" if not mismatches else "fail"

	if status == "fail" and int(strict) == 1:
		frappe.throw(
			_("Phase 4 Yemen dataset gate failed with {0} mismatch(es)").format(len(mismatches)),
			frappe.ValidationError,
		)

	return {
		"status": status,
		"strict": int(strict),
		"dataset_file": result.get("dataset_file"),
		"limit": int(limit),
		"expected_records": expected_records,
		"observed_qct_records": observed_qct_records,
		"expected_doc_counts": expected_doc_counts,
		"mismatch_count": len(mismatches),
		"mismatches": mismatches,
		"observed_doc_counts": observed_doc_counts,
	}


def _resolve_phase4_dataset_path(dataset_file: str) -> Path | None:
	if not dataset_file:
		return None

	p = Path(dataset_file)
	if p.is_file():
		return p

	cwd_candidate = Path.cwd() / dataset_file
	if cwd_candidate.is_file():
		return cwd_candidate

	if "yam_agri_core" in set(frappe.get_installed_apps() or []):
		app_path = Path(frappe.get_app_path("yam_agri_core")).resolve()
		for parent in app_path.parents:
			candidate = parent / dataset_file
			if candidate.is_file():
				return candidate

	return None


def _ensure_phase4_site(rec: dict[str, Any]) -> dict[str, Any]:
	site_code = str(rec.get("site") or "").strip() or "YEM-UNKNOWN-SITE"
	governorate = str(rec.get("governorate") or "").strip()
	site_type = _normalize_site_type(str(rec.get("site_type") or "").strip())

	site_name = frappe.db.get_value("Site", {"site_name": site_code}, "name")
	if site_name:
		return {"name": str(site_name), "created": False}

	if frappe.db.exists("Site", site_code):
		return {"name": site_code, "created": False}

	description = _("Phase 4 Yemen dataset site")
	if governorate:
		description = _("Phase 4 Yemen dataset site - {0}").format(governorate)

	doc = frappe.get_doc(
		{
			"doctype": "Site",
			"site_name": site_code,
			"site_type": site_type,
			"description": description,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _normalize_site_type(site_type: str) -> str:
	allowed = {"Farm", "Silo", "Warehouse", "Store", "Market", "Office"}
	if site_type in allowed:
		return site_type

	low = (site_type or "").strip().lower()
	if "farm" in low:
		return "Farm"
	if "silo" in low:
		return "Silo"
	if "ware" in low:
		return "Warehouse"
	if "store" in low:
		return "Store"
	if "market" in low:
		return "Market"
	if "office" in low:
		return "Office"

	return "Warehouse"


def _ensure_phase4_device(*, site: str, rec: dict[str, Any]) -> dict[str, Any]:
	device_name = "P4-DEV-" + str(rec.get("site") or site)[-8:]
	device_doc = frappe.db.get_value("Device", {"site": site, "device_name": device_name}, "name")
	if device_doc:
		return {"name": str(device_doc), "created": False}

	doc = frappe.get_doc(
		{
			"doctype": "Device",
			"device_name": device_name,
			"site": site,
			"device_type": "Scale",
			"status": "Active",
			"serial_number": "P4-" + device_name,
			"notes": _("Phase 4 Yemen dataset"),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _ensure_phase4_lot(*, site: str, rec: dict[str, Any]) -> dict[str, Any]:
	lot_number = str(rec.get("lot") or rec.get("record_id") or "").strip()
	if not lot_number:
		lot_number = "P4-LOT-UNKNOWN"

	lot_doc = frappe.db.get_value("Lot", {"site": site, "lot_number": lot_number}, "name")
	if lot_doc:
		return {"name": str(lot_doc), "created": False}

	payload: dict[str, Any] = {
		"doctype": "Lot",
		"lot_number": lot_number,
		"site": site,
		"qty_kg": float(rec.get("qty_kg") or 1000),
		"status": "Draft",
	}

	crop_name = str(rec.get("crop") or "").strip()
	if crop_name and frappe.db.exists("Crop", crop_name):
		payload["crop"] = crop_name

	doc = frappe.get_doc(payload)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _ensure_phase4_qctest(*, site: str, lot: str, rec: dict[str, Any]) -> dict[str, Any]:
	qc_state = str(rec.get("qc_state") or "Missing").strip()
	if qc_state == "Missing":
		return {"name": "", "created": False}

	record_id = str(rec.get("record_id") or "").strip()
	notes = "P4-YEMEN-" + record_id
	qct_meta = frappe.get_meta("QCTest")
	qct_filters: dict[str, Any] = {"site": site, "lot": lot, "test_type": "Moisture"}
	if qct_meta.has_field("notes"):
		qct_filters["notes"] = notes

	qct_name = frappe.db.get_value("QCTest", qct_filters, "name")
	if qct_name:
		return {"name": str(qct_name), "created": False}

	test_date = utils.nowdate() if qc_state == "Fresh" else utils.add_days(utils.nowdate(), -10)
	payload: dict[str, Any] = {
		"doctype": "QCTest",
		"lot": lot,
		"site": site,
		"test_type": "Moisture",
		"test_date": test_date,
		"result_value": 12.0,
		"pass_fail": "Pass",
	}
	if qct_meta.has_field("notes"):
		payload["notes"] = notes

	doc = frappe.get_doc(payload)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _ensure_phase4_certificate(*, site: str, lot: str, rec: dict[str, Any]) -> dict[str, Any]:
	cert_state = str(rec.get("certificate_state") or "Missing").strip()
	if cert_state == "Missing":
		return {"name": "", "created": False}

	record_id = str(rec.get("record_id") or "").strip()
	cert_type = "P4-COA-" + record_id
	cert_name = frappe.db.get_value("Certificate", {"site": site, "lot": lot, "cert_type": cert_type}, "name")
	if cert_name:
		return {"name": str(cert_name), "created": False}

	expiry_date = utils.add_days(utils.nowdate(), 30)
	if cert_state == "Expired":
		expiry_date = utils.add_days(utils.nowdate(), -1)

	doc = frappe.get_doc(
		{
			"doctype": "Certificate",
			"cert_type": cert_type,
			"lot": lot,
			"site": site,
			"expiry_date": expiry_date,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _ensure_phase4_transfer(*, site: str, lot: str, rec: dict[str, Any]) -> dict[str, Any]:
	transfer_type = str(rec.get("transfer_type") or "None").strip()
	if transfer_type == "None":
		return {"name": "", "created": False}

	record_id = str(rec.get("record_id") or "").strip()
	notes = "P4-YEMEN-" + record_id + "-" + transfer_type
	transfer_name = frappe.db.get_value("Transfer", {"site": site, "notes": notes}, "name")
	if transfer_name:
		return {"name": str(transfer_name), "created": False}

	doc = frappe.get_doc(
		{
			"doctype": "Transfer",
			"site": site,
			"transfer_type": transfer_type,
			"from_lot": lot,
			"to_lot": lot,
			"qty_kg": 1,
			"transfer_datetime": utils.now_datetime(),
			"status": "Draft",
			"notes": notes,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _ensure_phase4_scale_ticket(*, site: str, device: str, lot: str, rec: dict[str, Any]) -> dict[str, Any]:
	record_id = str(rec.get("record_id") or "").strip()
	ticket_number = "P4-ST-" + record_id
	ticket_name = frappe.db.get_value("ScaleTicket", {"site": site, "ticket_number": ticket_number}, "name")
	if ticket_name:
		return {"name": str(ticket_name), "created": False}

	net_kg = float(rec.get("qty_kg") or 1000)
	tare_kg = round(max(20.0, net_kg * 0.08), 2)
	gross_kg = round(net_kg + tare_kg, 2)

	doc = frappe.get_doc(
		{
			"doctype": "ScaleTicket",
			"ticket_number": ticket_number,
			"site": site,
			"device": device,
			"lot": lot,
			"ticket_datetime": utils.now_datetime(),
			"gross_kg": gross_kg,
			"tare_kg": tare_kg,
			"net_kg": net_kg,
			"vehicle": str(rec.get("transport_mode") or "Truck"),
			"driver": _("Phase 4 Driver"),
			"notes": _("Phase 4 Yemen dataset"),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}


def _ensure_phase4_observation(*, site: str, device: str, rec: dict[str, Any]) -> dict[str, Any]:
	record_id = str(rec.get("record_id") or "").strip()
	observation_type = "p4.seed." + record_id
	obs_name = frappe.db.get_value(
		"Observation", {"site": site, "device": device, "observation_type": observation_type}, "name"
	)
	if obs_name:
		return {"name": str(obs_name), "created": False}

	power_profile = str(rec.get("power_profile") or "Stable").strip()
	temp = 28.0 if power_profile == "Stable" else (30.0 if power_profile == "Outage-2h" else 32.5)

	doc = frappe.get_doc(
		{
			"doctype": "Observation",
			"site": site,
			"device": device,
			"observed_at": utils.now_datetime(),
			"observation_type": observation_type,
			"value": temp,
			"unit": "C",
			"quality_flag": str(rec.get("quality_flag") or "OK"),
			"raw_payload": json.dumps(
				{
					"phase": "Phase 4",
					"record_id": record_id,
					"connectivity": rec.get("connectivity"),
					"power_profile": power_profile,
				},
				ensure_ascii=False,
			),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": str(doc.name), "created": True}
