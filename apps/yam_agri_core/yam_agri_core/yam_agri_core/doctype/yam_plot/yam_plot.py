import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class YAMPlot(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

        assert_site_access(self.get("site"))

        if not (self.get("plot_name") or "").strip():
            frappe.throw(_("Plot Name is required"), frappe.ValidationError)

        area = self.get("area_ha")
        if area is not None and area != "":
            try:
                area_f = float(area)
            except (TypeError, ValueError):
                area_f = None
            if area_f is not None and area_f <= 0:
                frappe.throw(_("Area (ha) must be > 0"), frappe.ValidationError)
