import frappe
from frappe import _
from frappe.model.document import Document
from frappe import utils

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class EvidencePack(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		from_date = self.get("from_date")
		to_date = self.get("to_date")
		if from_date and to_date:
			if utils.getdate(from_date) > utils.getdate(to_date):
				frappe.throw(_("From Date must be on or before To Date"), frappe.ValidationError)

		new_status = (self.get("status") or "").strip()
		if new_status in ("Approved", "Rejected"):
			old_status = None
			if self.name:
				old_status = frappe.db.get_value("EvidencePack", self.name, "status")
			if old_status != new_status:
				if not frappe.has_role("QA Manager"):
					frappe.throw(
						_("Only a user with role 'QA Manager' may set EvidencePack status to {0}").format(new_status),
						frappe.PermissionError,
					)
