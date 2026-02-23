import frappe
from frappe import _
from frappe.model.document import Document


class Complaint(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		lot = self.get("lot")
		if lot:
			lot_site = frappe.db.get_value("Lot", lot, "site")
			if lot_site and lot_site != self.get("site"):
				frappe.throw(_("Lot site must match Complaint site"), frappe.ValidationError)
