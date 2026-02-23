import frappe
from frappe import _
from frappe.model.document import Document


class Observation(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		device = self.get("device")
		if device:
			device_site = frappe.db.get_value("Device", device, "site")
			if device_site and device_site != self.get("site"):
				frappe.throw(
					_("Device site must match Observation site"),
					frappe.ValidationError,
				)
