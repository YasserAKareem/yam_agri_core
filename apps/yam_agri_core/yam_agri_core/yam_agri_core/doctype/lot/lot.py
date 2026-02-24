import frappe
from frappe import _, utils
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access

DISPATCH_STATUSES = {"for dispatch", "ready for dispatch", "dispatch"}


def check_certificates_for_dispatch(lot_name, status):
	"""Helper used by tests and controllers: ensure no expired Certificate blocks dispatch.

	Raises: frappe.ValidationError when an expired certificate exists for the lot and
	the lot is being moved to a dispatch-like status.
	"""
	if not status:
		return

	if status.lower() not in DISPATCH_STATUSES:
		return

	certs = frappe.get_all("Certificate", filters={"lot": lot_name}, fields=["name", "expiry_date"])
	for c in certs:
		expiry = c.get("expiry_date")
		if expiry:
			if utils.getdate(expiry) < utils.getdate(utils.nowdate()):
				frappe.throw(
					_("Cannot dispatch: Certificate {0} is expired").format(c.get("name")),
					frappe.ValidationError,
				)


def _parse_csv_values(raw: str | None) -> list[str]:
	text = (raw or "").replace("\n", ",")
	parts = [p.strip() for p in text.split(",")]
	return [p for p in parts if p]


def _get_active_season_policy(site: str, crop: str | None) -> dict | None:
	filters = {"site": site, "active": 1}
	if crop:
		filters["crop"] = crop

	policies = frappe.get_all(
		"Season Policy",
		filters=filters,
		fields=[
			"name",
			"mandatory_test_types",
			"mandatory_certificate_types",
			"max_test_age_days",
			"enforce_dispatch_gate",
		],
		order_by="modified desc",
		limit_page_length=1,
	)
	if policies:
		return policies[0]

	if crop:
		fallback = frappe.get_all(
			"Season Policy",
			filters={"site": site, "active": 1},
			fields=[
				"name",
				"mandatory_test_types",
				"mandatory_certificate_types",
				"max_test_age_days",
				"enforce_dispatch_gate",
			],
			order_by="modified desc",
			limit_page_length=1,
		)
		if fallback:
			return fallback[0]

	return None


def _validate_season_policy_for_dispatch(lot_doc):
	status = (lot_doc.get("status") or "").strip().lower()
	if status not in DISPATCH_STATUSES:
		return

	policy = _get_active_season_policy(lot_doc.get("site"), lot_doc.get("crop"))
	if not policy:
		frappe.throw(
			_("Cannot dispatch: no active Season Policy found for this Site/Crop"), frappe.ValidationError
		)

	if not int(policy.get("enforce_dispatch_gate") or 0):
		return

	max_age_days = int(policy.get("max_test_age_days") or 7)
	required_tests = _parse_csv_values(policy.get("mandatory_test_types"))
	required_certs = _parse_csv_values(policy.get("mandatory_certificate_types"))

	missing_tests: list[str] = []
	for test_type in required_tests:
		records = frappe.get_all(
			"QCTest",
			filters={
				"lot": lot_doc.name,
				"site": lot_doc.get("site"),
				"test_type": test_type,
				"pass_fail": "Pass",
			},
			fields=["name", "test_date"],
			order_by="test_date desc",
			limit_page_length=1,
		)
		if not records:
			missing_tests.append(test_type)
			continue

		test_date = records[0].get("test_date")
		if not test_date:
			missing_tests.append(test_type)
			continue

		days_old = (utils.getdate(utils.nowdate()) - utils.getdate(test_date)).days
		if days_old > max_age_days:
			missing_tests.append(test_type)

	if missing_tests:
		frappe.throw(
			_("Cannot dispatch: missing or stale required QC tests: {0}").format(
				", ".join(sorted(set(missing_tests)))
			),
			frappe.ValidationError,
		)

	missing_certs: list[str] = []
	for cert_type in required_certs:
		records = frappe.get_all(
			"Certificate",
			filters={
				"lot": lot_doc.name,
				"site": lot_doc.get("site"),
				"cert_type": cert_type,
			},
			fields=["name", "expiry_date"],
			order_by="modified desc",
			limit_page_length=1,
		)
		if not records:
			missing_certs.append(cert_type)
			continue

		expiry = records[0].get("expiry_date")
		if expiry and utils.getdate(expiry) < utils.getdate(utils.nowdate()):
			missing_certs.append(cert_type)

	if missing_certs:
		frappe.throw(
			_("Cannot dispatch: missing or expired required certificates: {0}").format(
				", ".join(sorted(set(missing_certs)))
			),
			frappe.ValidationError,
		)


class Lot(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		crop = (self.get("crop") or "").strip()
		if crop:
			if frappe.db.exists("Crop", crop):
				self.crop = crop
			else:
				crop_name = _resolve_crop_name(crop)
				if crop_name:
					self.crop = crop_name
				else:
					frappe.throw(_("Crop must be a valid Crop record"), frappe.ValidationError)

		# Enforce certificate expiry check when moving to a dispatch-like status
		try:
			check_certificates_for_dispatch(self.name, self.get("status"))
		except frappe.ValidationError:
			raise

		# Enforce season policy gate for dispatch.
		_validate_season_policy_for_dispatch(self)

		# Enforce QA Manager approval for status transitions to Accepted/Rejected
		new_status = (self.get("status") or "").strip()
		if new_status in ("Accepted", "Rejected"):
			# determine old status from DB if present
			old_status = None
			if self.name:
				old_status = frappe.db.get_value("Lot", self.name, "status")
			if old_status != new_status:
				if not frappe.has_role("QA Manager"):
					frappe.throw(
						_("Only a user with role 'QA Manager' may set Lot status to {0}").format(new_status),
						frappe.PermissionError,
					)


def _resolve_crop_name(value: str) -> str | None:
	value = (value or "").strip()
	if not value or not frappe.db.exists("DocType", "Crop"):
		return None

	meta = frappe.get_meta("Crop")
	if meta.has_field("crop_name"):
		by_crop_name = frappe.db.get_value("Crop", {"crop_name": value}, "name")
		if by_crop_name:
			return by_crop_name

	if meta.has_field("title"):
		by_title = frappe.db.get_value("Crop", {"title": value}, "name")
		if by_title:
			return by_title

	return None
