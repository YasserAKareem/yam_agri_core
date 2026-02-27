from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access

FINAL_DECISIONS = {"Accepted", "Rejected"}
VALID_DECISIONS = {"Pending", *FINAL_DECISIONS}
MUTABLE_FIELDS = {"decision", "decided_by", "decided_at"}


class AIInteractionLog(Document):
	def before_insert(self):
		if not self.get("timestamp"):
			self.timestamp = frappe.utils.now_datetime()

		if not self.get("decision"):
			self.decision = "Pending"

		if not self.get("requested_by"):
			self.requested_by = frappe.session.user

	def validate(self):
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))
		self._normalize_decision()

		if not self.is_new():
			self._enforce_append_only()

	def on_trash(self):
		frappe.throw(_("AI Interaction Log is append-only. Deleting records is not permitted."), frappe.PermissionError)

	def _normalize_decision(self):
		decision = (self.get("decision") or "Pending").strip().title()
		if decision not in VALID_DECISIONS:
			frappe.throw(
				_("Decision must be one of: Pending, Accepted, Rejected"),
				frappe.ValidationError,
			)
		self.decision = decision

		if decision == "Pending":
			self.decided_by = ""
			self.decided_at = None
			return

		if not self.get("decided_by"):
			self.decided_by = frappe.session.user
		if not self.get("decided_at"):
			self.decided_at = frappe.utils.now_datetime()

	def _enforce_append_only(self):
		previous = frappe.get_doc(self.doctype, self.name)
		previous_decision = str(previous.get("decision") or "Pending")
		current_decision = str(self.get("decision") or "Pending")

		if previous_decision in FINAL_DECISIONS and current_decision != previous_decision:
			frappe.throw(
				_("Decision is final and cannot be changed after it is set."),
				frappe.PermissionError,
			)

		changed_immutable_fields: list[str] = []
		for field in self.meta.fields:
			fieldname = field.fieldname
			if fieldname in MUTABLE_FIELDS:
				continue

			if previous.get(fieldname) != self.get(fieldname):
				changed_immutable_fields.append(fieldname)

		if changed_immutable_fields:
			frappe.throw(
				_("AI Interaction Log is append-only. Immutable fields cannot be modified: {0}").format(
					", ".join(sorted(changed_immutable_fields))
				),
				frappe.PermissionError,
			)
