from __future__ import annotations

from typing import Any

import frappe
from frappe import utils


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
    for dt in ("Site", "Device", "Observation", "ScaleTicket", "Transfer", "EvidencePack", "Complaint"):
        if not frappe.db.exists("DocType", dt):
            frappe.throw(f"Missing DocType: {dt}")

    site = _ensure_default_site()
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
    for dt in ("Site", "Device", "Observation", "ScaleTicket", "Transfer", "EvidencePack", "Complaint"):
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
    for dt in ("Site", "Device", "Observation", "ScaleTicket", "Transfer", "EvidencePack", "Complaint"):
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
