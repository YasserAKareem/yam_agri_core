from __future__ import annotations

import frappe
from frappe.exceptions import PermissionError


def run_phase2_smoke() -> dict:
	"""Minimal post-migrate smoke for Phase 2 integration.

	Safe to run via:
	- bench --site <site> execute yam_agri_core.yam_agri_core.smoke.run_phase2_smoke
	"""

	checks: dict[str, object] = {
		"apps": {
			"agriculture": "agriculture" in (frappe.get_installed_apps() or []),
			"yam_agri_core": "yam_agri_core" in (frappe.get_installed_apps() or []),
			"yam_agri_qms_trace": "yam_agri_qms_trace" in (frappe.get_installed_apps() or []),
		},
		"doctypes": {
			"StorageBin": frappe.db.exists("DocType", "StorageBin") is not None,
			"Lot": frappe.db.exists("DocType", "Lot") is not None,
			"Crop": frappe.db.exists("DocType", "Crop") is not None,
			"Season Policy": frappe.db.exists("DocType", "Season Policy") is not None,
			"Location": frappe.db.exists("DocType", "Location") is not None,
			"Weather": frappe.db.exists("DocType", "Weather") is not None,
			"Crop Cycle": frappe.db.exists("DocType", "Crop Cycle") is not None,
		},
	}

	location_site_field = False
	if checks["doctypes"]["Location"]:
		location_site_field = frappe.get_meta("Location").has_field("site")

	checks["bridge"] = {
		"location_site_field": location_site_field,
	}

	checks["workspace"] = {
		"yam_agri": frappe.db.exists("Workspace", "YAM Agri") is not None,
		"traceability": frappe.db.exists("Workspace", "Traceability & Lots") is not None,
	}

	checks["permission_hooks"] = {
		"StorageBin": "StorageBin" in (frappe.get_hooks("permission_query_conditions") or {}),
		"Season Policy": "Season Policy" in (frappe.get_hooks("permission_query_conditions") or {}),
		"Weather": "Weather" in (frappe.get_hooks("permission_query_conditions") or {}),
		"Crop Cycle": "Crop Cycle" in (frappe.get_hooks("permission_query_conditions") or {}),
	}

	checks["status"] = (
		"ok"
		if all(
			[
				all(checks["apps"].values()),
				all(checks["doctypes"].values()),
				checks["bridge"]["location_site_field"],
				all(checks["workspace"].values()),
				all(checks["permission_hooks"].values()),
			]
		)
		else "needs_attention"
	)

	return checks


def get_at10_readiness() -> dict:
	"""Readiness report for manual AT-10 execution.

	Safe to run via:
	- bench --site <site> execute yam_agri_core.yam_agri_core.smoke.get_at10_readiness
	"""

	sites = frappe.get_all("Site", fields=["name"], limit_page_length=500)
	qa_users = ["qa_manager_a@example.com", "qa_manager_b@example.com"]

	existing_users = frappe.get_all(
		"User",
		filters={"name": ["in", qa_users]},
		fields=["name", "enabled"],
		limit_page_length=20,
	)

	has_roles = frappe.get_all(
		"Has Role",
		filters={"parent": ["in", qa_users]},
		fields=["parent", "role"],
		limit_page_length=200,
	)

	site_permissions = frappe.get_all(
		"User Permission",
		filters={"allow": "Site"},
		fields=["user", "for_value"],
		limit_page_length=500,
	)

	locations = []
	location_site_field = False
	if frappe.db.exists("DocType", "Location"):
		location_site_field = frappe.get_meta("Location").has_field("site")
		if location_site_field:
			locations = frappe.get_all("Location", fields=["name", "site"], limit_page_length=500)

	mapped_locations = [loc for loc in locations if (loc.get("site") or "").strip()]

	readiness = {
		"sites": {
			"count": len(sites),
			"names": [s["name"] for s in sites],
			"ok": len(sites) >= 2,
		},
		"qa_users": {
			"expected": qa_users,
			"existing": existing_users,
			"ok": len(existing_users) == 2,
		},
		"qa_roles": {
			"entries": has_roles,
			"ok": len(has_roles) > 0,
		},
		"site_permissions": {
			"entries": site_permissions,
			"ok": len(site_permissions) > 0,
		},
		"location_bridge": {
			"site_field_present": location_site_field,
			"mapped_locations_count": len(mapped_locations),
			"ok": location_site_field and len(mapped_locations) > 0,
		},
	}

	readiness["status"] = (
		"ready"
		if all(
			[
				readiness["sites"]["ok"],
				readiness["qa_users"]["ok"],
				readiness["qa_roles"]["ok"],
				readiness["site_permissions"]["ok"],
				readiness["location_bridge"]["ok"],
			]
		)
		else "not_ready"
	)

	return readiness


def run_at10_automated_check() -> dict:
	"""Execute automated AT-10 checks for Site isolation.

	This validates:
	- list visibility scoping by site
	- direct read permission denial for cross-site docs
	"""

	readiness = get_at10_readiness()
	if readiness.get("status") != "ready":
		return {
			"status": "blocked",
			"reason": "AT-10 readiness is not complete",
			"readiness": readiness,
		}

	site_a = None
	site_b = None
	for p in readiness["site_permissions"]["entries"]:
		if p["user"] == "qa_manager_a@example.com":
			site_a = p["for_value"]
		elif p["user"] == "qa_manager_b@example.com":
			site_b = p["for_value"]

	if not site_a or not site_b:
		return {
			"status": "blocked",
			"reason": "Could not resolve Site A/B from user permissions",
			"readiness": readiness,
		}

	original_user = frappe.session.user
	evidence = {
		"sites": {"site_a": site_a, "site_b": site_b},
		"list_checks": {},
		"direct_read_checks": {},
	}

	try:
		# Ensure test records exist on both sites.
		frappe.set_user("Administrator")

		lot_a = frappe.db.exists("Lot", {"lot_number": "AT10-LOT-A"})
		if not lot_a:
			lot_a = (
				frappe.get_doc(
					{
						"doctype": "Lot",
						"lot_number": "AT10-LOT-A",
						"site": site_a,
						"qty_kg": 100,
						"status": "Draft",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		lot_b = frappe.db.exists("Lot", {"lot_number": "AT10-LOT-B"})
		if not lot_b:
			lot_b = (
				frappe.get_doc(
					{
						"doctype": "Lot",
						"lot_number": "AT10-LOT-B",
						"site": site_b,
						"qty_kg": 100,
						"status": "Draft",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		bin_a = frappe.db.exists("StorageBin", {"storage_bin_name": "AT10-BIN-A"})
		if not bin_a:
			bin_a = (
				frappe.get_doc(
					{
						"doctype": "StorageBin",
						"storage_bin_name": "AT10-BIN-A",
						"site": site_a,
						"status": "Active",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		bin_b = frappe.db.exists("StorageBin", {"storage_bin_name": "AT10-BIN-B"})
		if not bin_b:
			bin_b = (
				frappe.get_doc(
					{
						"doctype": "StorageBin",
						"storage_bin_name": "AT10-BIN-B",
						"site": site_b,
						"status": "Active",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		# User A visibility and cross-site denial
		frappe.set_user("qa_manager_a@example.com")
		try:
			visible_lots_a = frappe.get_list("Lot", fields=["name", "site"], limit_page_length=200)
			visible_bins_a = frappe.get_list("StorageBin", fields=["name", "site"], limit_page_length=200)
			list_error_a = None
		except PermissionError as exc:
			visible_lots_a = []
			visible_bins_a = []
			list_error_a = str(exc)
		evidence["list_checks"]["qa_manager_a@example.com"] = {
			"lots_only_site_a": all((r.get("site") == site_a) for r in visible_lots_a),
			"bins_only_site_a": all((r.get("site") == site_a) for r in visible_bins_a),
			"lot_count": len(visible_lots_a),
			"bin_count": len(visible_bins_a),
			"error": list_error_a,
		}
		lot_b_doc = frappe.get_doc("Lot", lot_b)
		bin_b_doc = frappe.get_doc("StorageBin", bin_b)
		evidence["direct_read_checks"]["qa_manager_a@example.com"] = {
			"lot_b_read_allowed": bool(frappe.has_permission("Lot", "read", lot_b_doc)),
			"bin_b_read_allowed": bool(frappe.has_permission("StorageBin", "read", bin_b_doc)),
		}

		# User B visibility and cross-site denial
		frappe.set_user("qa_manager_b@example.com")
		try:
			visible_lots_b = frappe.get_list("Lot", fields=["name", "site"], limit_page_length=200)
			visible_bins_b = frappe.get_list("StorageBin", fields=["name", "site"], limit_page_length=200)
			list_error_b = None
		except PermissionError as exc:
			visible_lots_b = []
			visible_bins_b = []
			list_error_b = str(exc)
		evidence["list_checks"]["qa_manager_b@example.com"] = {
			"lots_only_site_b": all((r.get("site") == site_b) for r in visible_lots_b),
			"bins_only_site_b": all((r.get("site") == site_b) for r in visible_bins_b),
			"lot_count": len(visible_lots_b),
			"bin_count": len(visible_bins_b),
			"error": list_error_b,
		}
		lot_a_doc = frappe.get_doc("Lot", lot_a)
		bin_a_doc = frappe.get_doc("StorageBin", bin_a)
		evidence["direct_read_checks"]["qa_manager_b@example.com"] = {
			"lot_a_read_allowed": bool(frappe.has_permission("Lot", "read", lot_a_doc)),
			"bin_a_read_allowed": bool(frappe.has_permission("StorageBin", "read", bin_a_doc)),
		}

	finally:
		frappe.set_user(original_user)

	pass_checks = all(
		[
			evidence["list_checks"]["qa_manager_a@example.com"]["lots_only_site_a"],
			evidence["list_checks"]["qa_manager_a@example.com"]["bins_only_site_a"],
			evidence["list_checks"]["qa_manager_b@example.com"]["lots_only_site_b"],
			evidence["list_checks"]["qa_manager_b@example.com"]["bins_only_site_b"],
			not evidence["direct_read_checks"]["qa_manager_a@example.com"]["lot_b_read_allowed"],
			not evidence["direct_read_checks"]["qa_manager_a@example.com"]["bin_b_read_allowed"],
			not evidence["direct_read_checks"]["qa_manager_b@example.com"]["lot_a_read_allowed"],
			not evidence["direct_read_checks"]["qa_manager_b@example.com"]["bin_a_read_allowed"],
		]
	)

	return {
		"status": "pass" if pass_checks else "fail",
		"evidence": evidence,
	}


def run_at01_automated_check() -> dict:
	"""Execute automated AT-01 checks for Site -> StorageBin -> Lot flow.

	This validates:
	- baseline record creation at Site A (Device, StorageBin, Lot, Transfer, ScaleTicket)
	- cross-site invalid QCTest is blocked when lot.site != qc_test.site
	"""

	readiness = get_at10_readiness()
	if readiness.get("status") != "ready":
		return {
			"status": "blocked",
			"reason": "AT-10 readiness is not complete (required to resolve Site A/B)",
			"readiness": readiness,
		}

	site_a = None
	site_b = None
	for permission_entry in readiness["site_permissions"]["entries"]:
		if permission_entry["user"] == "qa_manager_a@example.com":
			site_a = permission_entry["for_value"]
		elif permission_entry["user"] == "qa_manager_b@example.com":
			site_b = permission_entry["for_value"]

	if not site_a or not site_b:
		return {
			"status": "blocked",
			"reason": "Could not resolve Site A/B from user permissions",
			"readiness": readiness,
		}

	original_user = frappe.session.user
	evidence = {
		"sites": {"site_a": site_a, "site_b": site_b},
		"records": {},
		"cross_site_invalid_blocked": False,
		"cross_site_error": None,
	}

	try:
		frappe.set_user("Administrator")
		from yam_agri_core.yam_agri_core.doctype.lot.lot import _validate_season_policy_for_dispatch

		device_a = frappe.db.exists("Device", {"device_name": "AT01-DEV-A", "site": site_a})
		if not device_a:
			device_a = (
				frappe.get_doc(
					{
						"doctype": "Device",
						"device_name": "AT01-DEV-A",
						"site": site_a,
						"device_type": "Scale",
						"status": "Active",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		storage_bin_a = frappe.db.exists("StorageBin", {"storage_bin_name": "AT01-BIN-A", "site": site_a})
		if not storage_bin_a:
			storage_bin_a = (
				frappe.get_doc(
					{
						"doctype": "StorageBin",
						"storage_bin_name": "AT01-BIN-A",
						"site": site_a,
						"capacity_kg": 1000,
						"current_qty_kg": 0,
						"status": "Active",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		lot_number_site_a = "AT01-LOT-A"
		lot_a = frappe.db.exists("Lot", {"lot_number": lot_number_site_a, "site": site_a})
		if not lot_a:
			lot_number_site_a = f"AT01-LOT-A-{site_a[-4:]}"
			lot_a = frappe.db.exists("Lot", {"lot_number": lot_number_site_a, "site": site_a})
		if not lot_a:
			lot_a = (
				frappe.get_doc(
					{
						"doctype": "Lot",
						"lot_number": lot_number_site_a,
						"site": site_a,
						"qty_kg": 100,
						"status": "Draft",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		transfer_a = frappe.db.exists("Transfer", {"notes": "AT01-AUTO-TRANSFER", "site": site_a})
		if not transfer_a:
			transfer_a = (
				frappe.get_doc(
					{
						"doctype": "Transfer",
						"site": site_a,
						"transfer_type": "Move",
						"from_lot": lot_a,
						"to_lot": lot_a,
						"qty_kg": 1,
						"transfer_datetime": frappe.utils.now_datetime(),
						"status": "Draft",
						"notes": "AT01-AUTO-TRANSFER",
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		ticket_a = frappe.db.exists("ScaleTicket", {"ticket_number": "AT01-ST-A", "site": site_a})
		if not ticket_a:
			ticket_a = (
				frappe.get_doc(
					{
						"doctype": "ScaleTicket",
						"ticket_number": "AT01-ST-A",
						"site": site_a,
						"device": device_a,
						"lot": lot_a,
						"ticket_datetime": frappe.utils.now_datetime(),
						"gross_kg": 110,
						"tare_kg": 10,
						"net_kg": 100,
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		evidence["records"] = {
			"device_a": device_a,
			"storage_bin_a": storage_bin_a,
			"lot_a": lot_a,
			"transfer_a": transfer_a,
			"ticket_a": ticket_a,
		}

		invalid_qc_doc = None
		invalid_certificate_doc = None
		validation_errors: list[str] = []

		try:
			invalid_qc_doc = frappe.get_doc(
				{
					"doctype": "QCTest",
					"lot": lot_a,
					"site": site_b,
					"test_type": "Moisture",
					"test_date": frappe.utils.nowdate(),
					"result_value": 12,
					"pass_fail": "Pass",
					"notes": "AT01-CROSS-SITE-INVALID-QC",
				}
			).insert(ignore_permissions=True)
		except Exception as exc:
			validation_errors.append(frappe.as_unicode(exc))

		try:
			invalid_certificate_doc = frappe.get_doc(
				{
					"doctype": "Certificate",
					"lot": lot_a,
					"site": site_b,
					"cert_type": "AT01-INVALID",
					"expiry_date": frappe.utils.add_days(frappe.utils.nowdate(), 30),
				}
			).insert(ignore_permissions=True)
		except Exception as exc:
			validation_errors.append(frappe.as_unicode(exc))

		if validation_errors:
			evidence["cross_site_error"] = " | ".join(validation_errors)
			evidence["cross_site_invalid_blocked"] = any(
				("site" in error.lower() and "match" in error.lower()) for error in validation_errors
			)

		if invalid_qc_doc:
			frappe.delete_doc("QCTest", invalid_qc_doc.name, force=True, ignore_permissions=True)
		if invalid_certificate_doc:
			frappe.delete_doc(
				"Certificate", invalid_certificate_doc.name, force=True, ignore_permissions=True
			)

	finally:
		frappe.set_user(original_user)

	pass_checks = all(
		[
			bool(evidence["records"].get("device_a")),
			bool(evidence["records"].get("storage_bin_a")),
			bool(evidence["records"].get("lot_a")),
			bool(evidence["records"].get("transfer_a")),
			bool(evidence["records"].get("ticket_a")),
			evidence["cross_site_invalid_blocked"],
		]
	)

	return {
		"status": "pass" if pass_checks else "fail",
		"evidence": evidence,
	}


def run_at02_automated_check() -> dict:
	"""Execute automated AT-02 checks for QCTest + Certificate + Season Policy gate.

	This validates:
	- dispatch is blocked when required tests/certificates are missing
	- dispatch is allowed after required QC and certificate evidence is present
	"""

	readiness = get_at10_readiness()
	if readiness.get("status") != "ready":
		return {
			"status": "blocked",
			"reason": "AT-10 readiness is not complete (required to resolve Site A)",
			"readiness": readiness,
		}

	site_a = None
	for permission_entry in readiness["site_permissions"]["entries"]:
		if permission_entry["user"] == "qa_manager_a@example.com":
			site_a = permission_entry["for_value"]
			break

	if not site_a:
		return {
			"status": "blocked",
			"reason": "Could not resolve Site A from user permissions",
			"readiness": readiness,
		}

	original_user = frappe.session.user
	evidence = {
		"site": site_a,
		"policy": None,
		"lot": None,
		"blocked_without_evidence": False,
		"blocked_error": None,
		"allowed_with_evidence": False,
		"allow_error": None,
		"qc_test": None,
		"certificate": None,
	}

	try:
		frappe.set_user("Administrator")
		from yam_agri_core.yam_agri_core.doctype.lot.lot import _validate_season_policy_for_dispatch

		policy_name = f"AT02-POLICY-{site_a[-4:]}"
		policy = frappe.db.exists("Season Policy", {"policy_name": policy_name, "site": site_a})
		if policy:
			policy_doc = frappe.get_doc("Season Policy", policy)
			policy_doc.mandatory_test_types = "AT02-MOISTURE"
			policy_doc.mandatory_certificate_types = "AT02-COA"
			policy_doc.max_test_age_days = 7
			policy_doc.enforce_dispatch_gate = 1
			policy_doc.active = 1
			policy_doc.season = "2026"
			policy_doc.save(ignore_permissions=True)
		else:
			policy_doc = frappe.get_doc(
				{
					"doctype": "Season Policy",
					"policy_name": policy_name,
					"site": site_a,
					"season": "2026",
					"mandatory_test_types": "AT02-MOISTURE",
					"mandatory_certificate_types": "AT02-COA",
					"max_test_age_days": 7,
					"enforce_dispatch_gate": 1,
					"active": 1,
				}
			).insert(ignore_permissions=True)

		evidence["policy"] = policy_doc.name

		lot_number = f"AT02-LOT-{frappe.utils.now_datetime().strftime('%H%M%S')}-{site_a[-4:]}"
		lot_doc = frappe.get_doc(
			{
				"doctype": "Lot",
				"lot_number": lot_number,
				"site": site_a,
				"qty_kg": 100,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

		evidence["lot"] = lot_doc.name

		# Remove pre-existing AT-02 QC/certs so blocked scenario is deterministic.
		for qct in frappe.get_all(
			"QCTest",
			filters={"lot": lot_doc.name, "site": site_a, "test_type": "AT02-MOISTURE"},
			fields=["name"],
		):
			frappe.delete_doc("QCTest", qct.name, force=True, ignore_permissions=True)

		for cert in frappe.get_all(
			"Certificate",
			filters={"lot": lot_doc.name, "site": site_a, "cert_type": "AT02-COA"},
			fields=["name"],
		):
			frappe.delete_doc("Certificate", cert.name, force=True, ignore_permissions=True)

		# 1) Must block without required QC/cert evidence.
		try:
			lot_doc.reload()
			lot_doc.status = "For Dispatch"
			_validate_season_policy_for_dispatch(lot_doc)
		except Exception as exc:
			evidence["blocked_error"] = frappe.as_unicode(exc)
			evidence["blocked_without_evidence"] = True

		# 2) Provide required evidence and confirm dispatch allowed.
		qc_test = frappe.get_doc(
			{
				"doctype": "QCTest",
				"lot": lot_doc.name,
				"site": site_a,
				"test_type": "AT02-MOISTURE",
				"test_date": frappe.utils.nowdate(),
				"result_value": 11.2,
				"pass_fail": "Pass",
			}
		).insert(ignore_permissions=True)
		evidence["qc_test"] = qc_test.name

		certificate = frappe.get_doc(
			{
				"doctype": "Certificate",
				"lot": lot_doc.name,
				"site": site_a,
				"cert_type": "AT02-COA",
				"expiry_date": frappe.utils.add_days(frappe.utils.nowdate(), 30),
			}
		).insert(ignore_permissions=True)
		evidence["certificate"] = certificate.name

		try:
			lot_doc.reload()
			lot_doc.status = "For Dispatch"
			_validate_season_policy_for_dispatch(lot_doc)
			evidence["allowed_with_evidence"] = True
		except Exception as exc:
			evidence["allow_error"] = frappe.as_unicode(exc)

	finally:
		frappe.set_user(original_user)

	pass_checks = all(
		[
			evidence["blocked_without_evidence"],
			evidence["allowed_with_evidence"],
			bool(evidence["policy"]),
			bool(evidence["lot"]),
			bool(evidence["qc_test"]),
			bool(evidence["certificate"]),
		]
	)

	return {
		"status": "pass" if pass_checks else "fail",
		"evidence": evidence,
	}


def run_at06_automated_check() -> dict:
	"""Execute automated AT-06 checks for stale QC + expired certificate dispatch blocking.

	This validates:
	- dispatch is blocked when QC test is stale and certificate is expired
	- dispatch is allowed after replacing with fresh QC and valid certificate
	"""

	readiness = get_at10_readiness()
	if readiness.get("status") != "ready":
		return {
			"status": "blocked",
			"reason": "AT-10 readiness is not complete (required to resolve Site A)",
			"readiness": readiness,
		}

	site_a = None
	for permission_entry in readiness["site_permissions"]["entries"]:
		if permission_entry["user"] == "qa_manager_a@example.com":
			site_a = permission_entry["for_value"]
			break

	if not site_a:
		return {
			"status": "blocked",
			"reason": "Could not resolve Site A from user permissions",
			"readiness": readiness,
		}

	original_user = frappe.session.user
	evidence = {
		"site": site_a,
		"policy": None,
		"lot": None,
		"blocked_with_stale_or_expired": False,
		"blocked_error": None,
		"allowed_after_refresh": False,
		"allow_error": None,
		"stale_qc_test": None,
		"expired_certificate": None,
		"fresh_qc_test": None,
		"valid_certificate": None,
	}

	try:
		frappe.set_user("Administrator")
		from yam_agri_core.yam_agri_core.doctype.lot.lot import _validate_season_policy_for_dispatch

		policy_name = f"AT06-POLICY-{site_a[-4:]}"
		policy = frappe.db.exists("Season Policy", {"policy_name": policy_name, "site": site_a})
		if policy:
			policy_doc = frappe.get_doc("Season Policy", policy)
			policy_doc.mandatory_test_types = "AT06-MOISTURE"
			policy_doc.mandatory_certificate_types = "AT06-COA"
			policy_doc.max_test_age_days = 3
			policy_doc.enforce_dispatch_gate = 1
			policy_doc.active = 1
			policy_doc.season = "2026"
			policy_doc.save(ignore_permissions=True)
		else:
			policy_doc = frappe.get_doc(
				{
					"doctype": "Season Policy",
					"policy_name": policy_name,
					"site": site_a,
					"season": "2026",
					"mandatory_test_types": "AT06-MOISTURE",
					"mandatory_certificate_types": "AT06-COA",
					"max_test_age_days": 3,
					"enforce_dispatch_gate": 1,
					"active": 1,
				}
			).insert(ignore_permissions=True)

		evidence["policy"] = policy_doc.name

		lot_number = f"AT06-LOT-{frappe.utils.now_datetime().strftime('%H%M%S')}-{site_a[-4:]}"
		lot_doc = frappe.get_doc(
			{
				"doctype": "Lot",
				"lot_number": lot_number,
				"site": site_a,
				"qty_kg": 100,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		evidence["lot"] = lot_doc.name

		for qct in frappe.get_all(
			"QCTest",
			filters={"lot": lot_doc.name, "site": site_a, "test_type": "AT06-MOISTURE"},
			fields=["name"],
		):
			frappe.delete_doc("QCTest", qct.name, force=True, ignore_permissions=True)

		for cert in frappe.get_all(
			"Certificate",
			filters={"lot": lot_doc.name, "site": site_a, "cert_type": "AT06-COA"},
			fields=["name"],
		):
			frappe.delete_doc("Certificate", cert.name, force=True, ignore_permissions=True)

		stale_qc_test = frappe.get_doc(
			{
				"doctype": "QCTest",
				"lot": lot_doc.name,
				"site": site_a,
				"test_type": "AT06-MOISTURE",
				"test_date": frappe.utils.add_days(frappe.utils.nowdate(), -8),
				"result_value": 11.0,
				"pass_fail": "Pass",
			}
		).insert(ignore_permissions=True)
		evidence["stale_qc_test"] = stale_qc_test.name

		expired_certificate = frappe.get_doc(
			{
				"doctype": "Certificate",
				"lot": lot_doc.name,
				"site": site_a,
				"cert_type": "AT06-COA",
				"expiry_date": frappe.utils.add_days(frappe.utils.nowdate(), -1),
			}
		).insert(ignore_permissions=True)
		evidence["expired_certificate"] = expired_certificate.name

		# 1) Must block with stale/expired evidence.
		try:
			lot_doc.reload()
			lot_doc.status = "For Dispatch"
			_validate_season_policy_for_dispatch(lot_doc)
		except Exception as exc:
			evidence["blocked_error"] = frappe.as_unicode(exc)
			evidence["blocked_with_stale_or_expired"] = True

		# 2) Refresh evidence and confirm dispatch allowed.
		frappe.delete_doc("QCTest", stale_qc_test.name, force=True, ignore_permissions=True)
		frappe.delete_doc("Certificate", expired_certificate.name, force=True, ignore_permissions=True)

		fresh_qc_test = frappe.get_doc(
			{
				"doctype": "QCTest",
				"lot": lot_doc.name,
				"site": site_a,
				"test_type": "AT06-MOISTURE",
				"test_date": frappe.utils.nowdate(),
				"result_value": 11.2,
				"pass_fail": "Pass",
			}
		).insert(ignore_permissions=True)
		evidence["fresh_qc_test"] = fresh_qc_test.name

		valid_certificate = frappe.get_doc(
			{
				"doctype": "Certificate",
				"lot": lot_doc.name,
				"site": site_a,
				"cert_type": "AT06-COA",
				"expiry_date": frappe.utils.add_days(frappe.utils.nowdate(), 30),
			}
		).insert(ignore_permissions=True)
		evidence["valid_certificate"] = valid_certificate.name

		try:
			lot_doc.reload()
			lot_doc.status = "For Dispatch"
			_validate_season_policy_for_dispatch(lot_doc)
			evidence["allowed_after_refresh"] = True
		except Exception as exc:
			evidence["allow_error"] = frappe.as_unicode(exc)

	finally:
		frappe.set_user(original_user)

	pass_checks = all(
		[
			evidence["blocked_with_stale_or_expired"],
			evidence["allowed_after_refresh"],
			bool(evidence["policy"]),
			bool(evidence["lot"]),
			bool(evidence["stale_qc_test"]),
			bool(evidence["expired_certificate"]),
			bool(evidence["fresh_qc_test"]),
			bool(evidence["valid_certificate"]),
		]
	)

	return {
		"status": "pass" if pass_checks else "fail",
		"evidence": evidence,
	}
