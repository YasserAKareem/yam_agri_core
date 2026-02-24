import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class Nonconformance(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

        assert_site_access(self.get("site"))

    def on_update(self):
        # Ensure status is set to Open when created if not provided
        if not self.get("status"):
            self.status = "Open"
