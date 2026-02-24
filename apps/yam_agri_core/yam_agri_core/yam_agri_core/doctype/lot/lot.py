import frappe
from frappe import _, utils
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access

DISPATCH_STATUSES = {"for dispatch", "ready for dispatch", "dispatch"}


def check_certificates_for_dispatch(lot_name, status):
    """Helper used by tests and controllers: ensure no expired Certificate blocks dispatch.

    Raises: frappe.ValidationError when an expired certificate exists for the lot and
    the lot is being moved to a dispatch-like status.
    """
    if not status:
        return

    if status.lower() not in DISPATCH_STATUSES:
        return

    certs = frappe.get_all("Certificate", filters={"lot": lot_name}, fields=["name", "expiry_date"])
    for c in certs:
        expiry = c.get("expiry_date")
        if expiry:
            if utils.getdate(expiry) < utils.nowdate():
                frappe.throw(
                    _("Cannot dispatch: Certificate {0} is expired").format(c.get("name")),
                    frappe.ValidationError,
                )


class Lot(Document):
    def validate(self):
        # Non-negotiable: every record must belong to a Site
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

        assert_site_access(self.get("site"))

        crop = (self.get("crop") or "").strip()
        if crop:
            if frappe.db.exists("Crop", crop):
                self.crop = crop
            else:
                crop_name = _resolve_crop_name(crop)
                if crop_name:
                    self.crop = crop_name
                else:
                    frappe.throw(_("Crop must be a valid Crop record"), frappe.ValidationError)

        # Enforce certificate expiry check when moving to a dispatch-like status
        try:
            check_certificates_for_dispatch(self.name, self.get("status"))
        except frappe.ValidationError:
            raise

        # Enforce QA Manager approval for status transitions to Accepted/Rejected
        new_status = (self.get("status") or "").strip()
        if new_status in ("Accepted", "Rejected"):
            # determine old status from DB if present
            old_status = None
            if self.name:
                old_status = frappe.db.get_value("Lot", self.name, "status")
            if old_status != new_status:
                if not frappe.has_role("QA Manager"):
                    frappe.throw(
                        _("Only a user with role 'QA Manager' may set Lot status to {0}").format(new_status),
                        frappe.PermissionError,
                    )


def _resolve_crop_name(value: str) -> str | None:
    value = (value or "").strip()
    if not value or not frappe.db.exists("DocType", "Crop"):
        return None

    meta = frappe.get_meta("Crop")
    if meta.has_field("crop_name"):
        by_crop_name = frappe.db.get_value("Crop", {"crop_name": value}, "name")
        if by_crop_name:
            return by_crop_name

    if meta.has_field("title"):
        by_title = frappe.db.get_value("Crop", {"title": value}, "name")
        if by_title:
            return by_title

    return None
