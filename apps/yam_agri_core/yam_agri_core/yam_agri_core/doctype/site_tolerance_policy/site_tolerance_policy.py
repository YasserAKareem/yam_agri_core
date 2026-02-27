import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class SiteTolerancePolicy(Document):
	def before_insert(self):
		if self.get("active") is None:
			self.active = 1

	def validate(self):
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		if not (self.get("policy_name") or "").strip():
			frappe.throw(_("Policy Name is required"), frappe.ValidationError)

		tolerance_pct = float(self.get("tolerance_pct") or 0)
		if tolerance_pct <= 0 or tolerance_pct > 100:
			frappe.throw(
				_("Tolerance % must be greater than 0 and less than or equal to 100"), frappe.ValidationError
			)

		from_date = self.get("from_date")
		to_date = self.get("to_date")
		if from_date and to_date and from_date > to_date:
			frappe.throw(_("From Date cannot be later than To Date"), frappe.ValidationError)
