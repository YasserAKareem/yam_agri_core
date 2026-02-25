import json

import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class Observation(Document):
	def before_insert(self):
		# Default quality flag to OK; invalid data is quarantined explicitly
		if not self.get("quality_flag"):
			self.quality_flag = "OK"

	def validate(self):
		enforce_observation_validate(self)

	def _apply_threshold_and_alert_policy(self):
		observation_type = str(self.get("observation_type") or "").strip()
		if not observation_type:
			return

		value = self.get("value")
		if value is None:
			return

		policy = _get_active_threshold_policy(self.get("site"), observation_type)
		if not policy:
			return

		policy_band, should_quarantine, should_alert = _evaluate_threshold_band(float(value), policy)

		if should_quarantine:
			self.quality_flag = "Quarantine"

		raw_payload = _load_json_payload(self.get("raw_payload"))
		channels = ["mobile_app", "sms", "email", "whatsapp", "wechat"] if should_alert else []
		raw_payload["threshold_policy"] = {
			"policy": str(policy.get("name") or ""),
			"band": policy_band,
			"should_alert": should_alert,
			"channels": channels,
		}
		if should_alert:
			raw_payload["alert_dispatch"] = _build_alert_dispatch_payload(channels)
		self.raw_payload = json.dumps(raw_payload, ensure_ascii=False)

		if should_alert:
			frappe.publish_realtime(
				"yam_agri_observation_alert",
				{
					"site": self.get("site"),
					"device": self.get("device"),
					"observation_type": observation_type,
					"value": float(value),
					"band": policy_band,
					"quality_flag": self.get("quality_flag"),
				},
			)


def enforce_observation_validate(doc, method=None) -> None:
	if not doc.get("site"):
		frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

	assert_site_access(doc.get("site"))

	if not doc.get("quality_flag"):
		doc.quality_flag = "OK"

	device = doc.get("device")
	if device:
		device_site = frappe.db.get_value("Device", device, "site")
		if device_site and device_site != doc.get("site"):
			frappe.throw(
				_("Device site must match Observation site"),
				frappe.ValidationError,
			)

	_apply_threshold_and_alert_policy_for_doc(doc)


def _apply_threshold_and_alert_policy_for_doc(doc) -> None:
	observation_type = str(doc.get("observation_type") or "").strip()
	if not observation_type:
		return

	value = doc.get("value")
	if value is None:
		return

	policy = _get_active_threshold_policy(doc.get("site"), observation_type)
	if not policy:
		return

	policy_band, should_quarantine, should_alert = _evaluate_threshold_band(float(value), policy)

	if should_quarantine:
		doc.quality_flag = "Quarantine"

	raw_payload = _load_json_payload(doc.get("raw_payload"))
	channels = ["mobile_app", "sms", "email", "whatsapp", "wechat"] if should_alert else []
	raw_payload["threshold_policy"] = {
		"policy": str(policy.get("name") or ""),
		"band": policy_band,
		"should_alert": should_alert,
		"channels": channels,
	}
	if should_alert:
		raw_payload["alert_dispatch"] = _build_alert_dispatch_payload(channels)
	doc.raw_payload = json.dumps(raw_payload, ensure_ascii=False)

	if should_alert:
		frappe.publish_realtime(
			"yam_agri_observation_alert",
			{
				"site": doc.get("site"),
				"device": doc.get("device"),
				"observation_type": observation_type,
				"value": float(value),
				"band": policy_band,
				"quality_flag": doc.get("quality_flag"),
			},
		)


def _build_alert_dispatch_payload(channels: list[str]) -> dict:
	if not channels:
		return {"status": "not_required", "channels": []}

	return {
		"status": "queued",
		"priority": "critical",
		"channels": [{"name": channel, "state": "queued"} for channel in channels],
	}


def _load_json_payload(raw_payload) -> dict:
	if not raw_payload:
		return {}
	if isinstance(raw_payload, dict):
		return raw_payload
	try:
		parsed = json.loads(str(raw_payload))
		if isinstance(parsed, dict):
			return parsed
	except ValueError:
		return {}
	return {}


def _get_active_threshold_policy(site: str, observation_type: str) -> dict | None:
	if not frappe.db.exists("DocType", "Observation Threshold Policy"):
		return None

	rows = frappe.get_all(
		"Observation Threshold Policy",
		filters={"site": site, "active": 1},
		fields=[
			"name",
			"observation_type",
			"warning_min",
			"warning_max",
			"critical_min",
			"critical_max",
		],
		order_by="modified desc",
		limit_page_length=50,
	)

	for row in rows:
		row_type = str(row.get("observation_type") or "").strip()
		if row_type == observation_type:
			return row

	for row in rows:
		row_type = str(row.get("observation_type") or "").strip()
		if row_type == "*":
			return row

	return None


def _evaluate_threshold_band(value: float, policy: dict) -> tuple[str, bool, bool]:
	warning_min = policy.get("warning_min")
	warning_max = policy.get("warning_max")
	critical_min = policy.get("critical_min")
	critical_max = policy.get("critical_max")

	critical_hit = False
	if critical_min is not None and float(value) < float(critical_min):
		critical_hit = True
	if critical_max is not None and float(value) > float(critical_max):
		critical_hit = True

	if critical_hit:
		return "quarantine", True, True

	warning_hit = False
	if warning_min is not None and float(value) < float(warning_min):
		warning_hit = True
	if warning_max is not None and float(value) > float(warning_max):
		warning_hit = True

	if warning_hit:
		return "warning", False, True

	return "normal", False, False
