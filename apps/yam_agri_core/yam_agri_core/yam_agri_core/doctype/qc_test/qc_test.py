import frappe
from frappe import _
from frappe.model.document import Document
from frappe import utils

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class QCTest(Document):
    def validate(self):
        if not self.get("site"):
            frappe.throw(_("Every record must belong to a Site"), frappe.ValidationError)

        assert_site_access(self.get("site"))

    def days_since_test(self):
        """Return integer days since the `test_date` if present, else None."""
        test_date = self.get("test_date")
        if not test_date:
            return None
        delta = utils.getdate(utils.nowdate()) - utils.getdate(test_date)
        return delta.days

    def is_fresh_for_season(self, max_days=7):
        """Season policy helper: default 7 days for critical tests like aflatoxin."""
        days = self.days_since_test()
        if days is None:
            return False
        return days <= int(max_days)
