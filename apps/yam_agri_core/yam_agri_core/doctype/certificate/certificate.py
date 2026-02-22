import frappe
from frappe import _
from frappe.model.document import Document
from frappe import utils


class Certificate(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

    def is_expired(self):
        expiry = self.get("expiry_date")
        if not expiry:
            return False
        return utils.getdate(expiry) < utils.nowdate()
