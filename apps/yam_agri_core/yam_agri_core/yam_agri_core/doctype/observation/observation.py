import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class Observation(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		# Default quality flag to OK; invalid data is quarantined explicitly
		if not self.get("quality_flag"):
			self.quality_flag = "OK"

		device = self.get("device")
		if device:
			device_site = frappe.db.get_value("Device", device, "site")
			if device_site and device_site != self.get("site"):
				frappe.throw(
					_("Device site must match Observation site"),
					frappe.ValidationError,
				)
