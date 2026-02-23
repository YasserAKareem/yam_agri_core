import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class YAMCropVariety(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

        assert_site_access(self.get("site"))

        if not self.get("crop"):
            frappe.throw(_("Crop is required"), frappe.ValidationError)

        if not (self.get("variety_name") or "").strip():
            frappe.throw(_("Variety Name is required"), frappe.ValidationError)

        drought = self.get("drought_tolerance")
        if drought is not None and drought != "":
            try:
                drought_f = float(drought)
            except (TypeError, ValueError):
                drought_f = None
            if drought_f is not None and (drought_f < 0 or drought_f > 5):
                frappe.throw(_("Drought Tolerance must be between 0 and 5"), frappe.ValidationError)
