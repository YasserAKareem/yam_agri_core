import frappe
from frappe import _
from frappe.model.document import Document


class Nonconformance(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

    def on_update(self):
        # Ensure status is set to Open when created if not provided
        if not self.get("status"):
            self.status = "Open"
