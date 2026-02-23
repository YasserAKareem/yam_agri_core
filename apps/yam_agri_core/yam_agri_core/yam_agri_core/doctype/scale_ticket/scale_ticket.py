import frappe
from frappe import _
from frappe.model.document import Document


class ScaleTicket(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		gross = float(self.get("gross_kg") or 0)
		tare = float(self.get("tare_kg") or 0)
		net = gross - tare
		if net < 0:
			frappe.throw(_("Net weight cannot be negative"), frappe.ValidationError)
		self.net_kg = net

		device = self.get("device")
		if device:
			device_site = frappe.db.get_value("Device", device, "site")
			if device_site and device_site != self.get("site"):
				frappe.throw(_("Device site must match ScaleTicket site"), frappe.ValidationError)

		lot = self.get("lot")
		if lot:
			lot_site = frappe.db.get_value("Lot", lot, "site")
			if lot_site and lot_site != self.get("site"):
				frappe.throw(_("Lot site must match ScaleTicket site"), frappe.ValidationError)
