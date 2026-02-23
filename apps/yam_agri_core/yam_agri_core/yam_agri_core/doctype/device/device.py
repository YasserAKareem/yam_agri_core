import frappe
from frappe import _
from frappe.model.document import Document


class Device(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)
