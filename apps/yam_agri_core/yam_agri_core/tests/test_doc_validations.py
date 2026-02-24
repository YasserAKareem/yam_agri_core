import unittest

import frappe


class TestDocValidations(unittest.TestCase):
    def test_check_certificates_for_dispatch_raises_on_expired(self):
        original_get_all = frappe.get_all
        original_throw = frappe.throw
        try:
            frappe.get_all = lambda *a, **k: [{"name": "CERT-1", "expiry_date": "2020-01-01"}]
            frappe.throw = lambda msg, exc=None: (_ for _ in ()).throw(exc(msg) if exc else Exception(msg))

            from yam_agri_core.yam_agri_core.doctype.lot.lot import check_certificates_for_dispatch

            with self.assertRaises(Exception):
                check_certificates_for_dispatch("LOT-1", "For Dispatch")
        finally:
            frappe.get_all = original_get_all
            frappe.throw = original_throw

    def test_qc_test_freshness(self):
        from yam_agri_core.yam_agri_core.doctype.qc_test.qc_test import QCTest

        doc = object.__new__(QCTest)
        doc.test_date = None
        self.assertIsNone(doc.days_since_test())

        class utils:
            @staticmethod
            def getdate(x):
                from datetime import date

                if x == "2026-02-15":
                    return date(2026, 2, 15)
                return date(2026, 2, 22)

            @staticmethod
            def nowdate():
                return "2026-02-22"

        from yam_agri_core.yam_agri_core.doctype.qc_test import qc_test as qc_test_module

        original_utils = qc_test_module.utils
        qc_test_module.utils = utils
        doc.test_date = "2026-02-15"
        try:
            self.assertEqual(doc.days_since_test(), 7)
            self.assertTrue(doc.is_fresh_for_season(7))
        finally:
            qc_test_module.utils = original_utils

    def test_only_qa_manager_can_accept_lot(self):
        from yam_agri_core.yam_agri_core.doctype.lot.lot import Lot

        lot = frappe.new_doc("Lot")
        lot.name = "LOT-1"
        lot.site = "Site-1"
        lot.status = "Accepted"

        original_get_value = frappe.db.get_value
        original_has_role = getattr(frappe, "has_role", None)

        def patched_get_value(doctype, *args, **kwargs):
            if doctype == "Lot":
                return "Draft"
            return original_get_value(doctype, *args, **kwargs)

        frappe.db.get_value = patched_get_value
        frappe.has_role = lambda role: False

        try:
            with self.assertRaises(Exception):
                lot.validate()
        finally:
            frappe.db.get_value = original_get_value
            if original_has_role is not None:
                frappe.has_role = original_has_role
            elif hasattr(frappe, "has_role"):
                delattr(frappe, "has_role")
