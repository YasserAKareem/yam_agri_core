import frappe
from frappe import _
from frappe.model.document import Document
from frappe import utils

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

    certs = frappe.get_all(
        "Certificate", filters={"lot": lot_name}, fields=["name", "expiry_date"]
    )
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
