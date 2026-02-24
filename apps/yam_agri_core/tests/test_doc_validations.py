import frappe
import pytest


def test_check_certificates_for_dispatch_raises_on_expired(monkeypatch):
    # simulate a certificate that's expired
    monkeypatch.setattr(frappe, "get_all", lambda *a, **k: [{"name": "CERT-1", "expiry_date": "2020-01-01"}])
    monkeypatch.setattr(
        frappe, "throw", lambda msg, exc=None: (_ for _ in ()).throw(exc(msg) if exc else Exception(msg))
    )

    from yam_agri_core.doctype.lot.lot import check_certificates_for_dispatch

    with pytest.raises(frappe.ValidationError):
        check_certificates_for_dispatch("LOT-1", "For Dispatch")


def test_qc_test_freshness(monkeypatch):
    from yam_agri_core.doctype.qc_test.qc_test import QCTest

    doc = QCTest()
    # no date -> not fresh
    assert doc.days_since_test() is None

    # monkeypatch utils.getdate/nowdate to simulate dates
    class utils:
        @staticmethod
        def getdate(x):
            from datetime import date

            if x == "2026-02-15":
                return date(2026, 2, 15)
            return date(2026, 2, 22)

    monkeypatch.setattr("yam_agri_core.doctype.qc_test.qc_test.utils", utils)

    doc.test_date = "2026-02-15"
    assert doc.days_since_test() == 7
    assert doc.is_fresh_for_season(7)


def test_only_qa_manager_can_accept_lot(monkeypatch):
    from yam_agri_core.doctype.lot.lot import Lot

    # simulate old status = Draft in DB
    class DB:
        @staticmethod
        def get_value(doctype, name, field):
            return "Draft"

    monkeypatch.setattr("frappe.db", DB)
    # simulate user does NOT have QA Manager role
    monkeypatch.setattr("frappe.has_role", lambda role: False)

    lot = Lot()
    lot.name = "LOT-1"
    lot.site = "Site-1"
    lot.status = "Accepted"

    with pytest.raises(frappe.PermissionError):
        lot.validate()
