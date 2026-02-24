import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class Transfer(Document):
	def validate(self):
		# Non-negotiable: every record must belong to a Site
		if not self.get("site"):
			frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

		assert_site_access(self.get("site"))

		qty = float(self.get("qty_kg") or 0)
		if qty <= 0:
			frappe.throw(_("Quantity must be greater than zero"), frappe.ValidationError)

		from_lot = self.get("from_lot")
		to_lot = self.get("to_lot")
		if from_lot:
			from_site = frappe.db.get_value("Lot", from_lot, "site")
			if from_site and from_site != self.get("site"):
				frappe.throw(_("From Lot site must match Transfer site"), frappe.ValidationError)
		if to_lot:
			to_site = frappe.db.get_value("Lot", to_lot, "site")
			if to_site and to_site != self.get("site"):
				frappe.throw(_("To Lot site must match Transfer site"), frappe.ValidationError)

		new_status = (self.get("status") or "").strip()
		if new_status in ("Approved", "Rejected"):
			old_status = None
			if self.name:
				old_status = frappe.db.get_value("Transfer", self.name, "status")
			if old_status != new_status:
				if not frappe.has_role("QA Manager"):
					frappe.throw(
						_("Only a user with role 'QA Manager' may set Transfer status to {0}").format(
							new_status
						),
						frappe.PermissionError,
					)
