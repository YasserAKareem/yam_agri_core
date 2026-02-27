import frappe
from frappe import _, utils
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access

FINAL_STATUSES = {"Sent", "Approved", "Rejected"}
CANONICAL_TRANSITIONS = {
	"Draft": {"Draft", "Ready"},
	"Ready": {"Ready", "Sent"},
	"Sent": {"Sent"},
}


class EvidencePack(Document):
	def validate(self):
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))
		self._validate_date_range()
		self._validate_status()
		self._validate_site_lot_consistency()

	def _validate_date_range(self) -> None:
		from_date = self.get("from_date")
		to_date = self.get("to_date")
		if from_date and to_date and utils.getdate(from_date) > utils.getdate(to_date):
			frappe.throw(_("From Date must be on or before To Date"), frappe.ValidationError)

	def _validate_status(self) -> None:
		new_status = (self.get("status") or "Draft").strip()
		if not new_status:
			new_status = "Draft"
		self.status = new_status

		if not self.name:
			if new_status in FINAL_STATUSES and not self._has_qa_override_role():
				frappe.throw(
					_("Only a user with role 'QA Manager' may set EvidencePack status to {0}").format(new_status),
					frappe.PermissionError,
				)
			return

		old_status = str(frappe.db.get_value("EvidencePack", self.name, "status") or "Draft").strip()
		if old_status == new_status:
			return

		if old_status in CANONICAL_TRANSITIONS and new_status in CANONICAL_TRANSITIONS:
			allowed = CANONICAL_TRANSITIONS.get(old_status) or {old_status}
			if new_status not in allowed:
				frappe.throw(
					_("Invalid EvidencePack status transition: {0} -> {1}").format(old_status, new_status),
					frappe.ValidationError,
				)

		if new_status in FINAL_STATUSES and not self._has_qa_override_role():
			frappe.throw(
				_("Only a user with role 'QA Manager' may set EvidencePack status to {0}").format(new_status),
				frappe.PermissionError,
			)

	def _validate_site_lot_consistency(self) -> None:
		lot_name = str(self.get("lot") or "").strip()
		if not lot_name:
			return

		lot_site = frappe.db.get_value("Lot", lot_name, "site")
		if not lot_site:
			frappe.throw(_("Selected Lot does not exist"), frappe.ValidationError)

		if str(lot_site) != str(self.get("site") or ""):
			frappe.throw(_("EvidencePack Lot must belong to the same Site"), frappe.ValidationError)

	def _has_qa_override_role(self) -> bool:
		roles = set(frappe.get_roles(frappe.session.user) or [])
		return bool({"QA Manager", "System Manager", "Administrator"}.intersection(roles))
