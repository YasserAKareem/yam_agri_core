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
