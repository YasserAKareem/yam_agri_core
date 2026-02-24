from __future__ import annotations

from typing import Any

import frappe
from frappe import utils

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
			frappe.throw(f"Missing DocType: {dt}")

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
		frappe.throw("Set confirm=1 to execute sample-data generation")

	if int(target_records) < 20:
		frappe.throw("target_records must be at least 20")

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
			frappe.throw(f"Missing DocType: {dt}")

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
		lot_doc = frappe.get_doc(
			lot_payload
		).insert(ignore_permissions=True)
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
