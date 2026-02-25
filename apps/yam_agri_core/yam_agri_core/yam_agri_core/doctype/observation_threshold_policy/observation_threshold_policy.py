import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class ObservationThresholdPolicy(Document):
	def before_insert(self):
		if self.get("active") is None:
			self.active = 1

	def validate(self):
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		if not (self.get("policy_name") or "").strip():
			frappe.throw(_("Policy Name is required"), frappe.ValidationError)

		observation_type = (self.get("observation_type") or "").strip()
		if not observation_type:
			frappe.throw(_("Observation Type is required"), frappe.ValidationError)

		warning_min = self.get("warning_min")
		warning_max = self.get("warning_max")
		critical_min = self.get("critical_min")
		critical_max = self.get("critical_max")

		if warning_min is not None and warning_max is not None and float(warning_min) > float(warning_max):
			frappe.throw(_("Warning Min cannot be greater than Warning Max"), frappe.ValidationError)

		if critical_min is not None and critical_max is not None and float(critical_min) > float(critical_max):
			frappe.throw(_("Critical Min cannot be greater than Critical Max"), frappe.ValidationError)

		if warning_min is not None and critical_min is not None and float(critical_min) > float(warning_min):
			frappe.throw(_("Critical Min should be less than or equal to Warning Min"), frappe.ValidationError)

		if warning_max is not None and critical_max is not None and float(critical_max) < float(warning_max):
			frappe.throw(_("Critical Max should be greater than or equal to Warning Max"), frappe.ValidationError)
