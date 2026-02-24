import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class SeasonPolicy(Document):
	def validate(self):
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		if not (self.get("policy_name") or "").strip():
			frappe.throw(_("Policy Name is required"), frappe.ValidationError)

		if not (self.get("season") or "").strip():
			frappe.throw(_("Season is required"), frappe.ValidationError)

		max_days = self.get("max_test_age_days")
		if max_days is None:
			self.max_test_age_days = 7
		elif int(max_days) <= 0:
			frappe.throw(_("Max Test Age (days) must be greater than zero"), frappe.ValidationError)
