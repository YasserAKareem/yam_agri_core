import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class Nonconformance(Document):
	def before_insert(self):
		# Default status to Open when a new Nonconformance is created
		if not self.get("status"):
			self.status = "Open"

	def validate(self):
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		lot = self.get("lot")
		if lot:
			lot_site = frappe.db.get_value("Lot", lot, "site")
			if lot_site and lot_site != self.get("site"):
				frappe.throw(_("Lot site must match Nonconformance site"), frappe.ValidationError)
