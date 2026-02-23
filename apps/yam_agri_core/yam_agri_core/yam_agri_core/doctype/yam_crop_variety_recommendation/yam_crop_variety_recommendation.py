import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class YAMCropVarietyRecommendation(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

        assert_site_access(self.get("site"))

        if not (self.get("season") or "").strip():
            frappe.throw(_("Season is required"), frappe.ValidationError)

        if not self.get("crop"):
            frappe.throw(_("Crop is required"), frappe.ValidationError)

        if not self.get("variety"):
            frappe.throw(_("Variety is required"), frappe.ValidationError)

        plot = self.get("plot")
        if plot:
            plot_site = frappe.db.get_value("YAM Plot", plot, "site")
            if plot_site and plot_site != self.get("site"):
                frappe.throw(_("Plot Site does not match Recommendation Site"), frappe.ValidationError)
