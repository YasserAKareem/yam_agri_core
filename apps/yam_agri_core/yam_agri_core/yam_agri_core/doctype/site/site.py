import frappe
from frappe import _
from frappe.model.document import Document


class Site(Document):
	def validate(self):
		if not (self.get("site_name") or "").strip():
			frappe.throw(_("Site Name is required"), frappe.ValidationError)
