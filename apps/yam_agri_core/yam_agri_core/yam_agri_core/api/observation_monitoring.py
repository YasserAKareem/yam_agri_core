from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access, resolve_site


@frappe.whitelist()
def get_observation_executive_summary(
	site: str | None = None,
	include_quarantine: int = 0,
	limit: int = 200,
) -> dict[str, Any]:
	"""Return observation summary for executive views.

	Default behavior excludes quarantine rows to keep dashboards focused on clean signal.
	Set include_quarantine=1 to include all rows.
	"""

	filters: dict[str, Any] = {}
	if site:
		site_name = resolve_site(site)
		assert_site_access(site_name)
		filters["site"] = site_name

	if int(include_quarantine) != 1:
		filters["quality_flag"] = ["!=", "Quarantine"]

	rows = frappe.get_all(
		"Observation",
		filters=filters,
		fields=["name", "site", "device", "observation_type", "value", "unit", "quality_flag", "raw_payload"],
		order_by="modified desc",
		limit_page_length=max(1, int(limit)),
	)

	by_quality: dict[str, int] = {}
	alert_candidates = 0
	for row in rows:
		quality_flag = str(row.get("quality_flag") or "")
		by_quality[quality_flag] = by_quality.get(quality_flag, 0) + 1

		raw_payload = str(row.get("raw_payload") or "")
		try:
			parsed = json.loads(raw_payload) if raw_payload else {}
		except ValueError:
			parsed = {}

		threshold_policy = parsed.get("threshold_policy") if isinstance(parsed, dict) else {}
		if isinstance(threshold_policy, dict) and int(threshold_policy.get("should_alert") or 0) == 1:
			alert_candidates += 1

	return {
		"status": "ok",
		"include_quarantine": int(include_quarantine),
		"row_count": len(rows),
		"quality_distribution": dict(sorted(by_quality.items())),
		"alert_candidates": alert_candidates,
		"rows": rows,
	}


@frappe.whitelist()
def get_observation_alert_channels() -> dict[str, Any]:
	"""Return Phase 5 configured alert channels for operator visibility."""

	channels = [
		{"channel": "mobile_app", "status": "enabled"},
		{"channel": "sms", "status": "enabled"},
		{"channel": "email", "status": "enabled"},
		{"channel": "whatsapp", "status": "enabled"},
		{"channel": "wechat", "status": "enabled"},
	]

	return {
		"status": "ok",
		"message": _("Phase 5 alert channels configured"),
		"channels": channels,
	}
