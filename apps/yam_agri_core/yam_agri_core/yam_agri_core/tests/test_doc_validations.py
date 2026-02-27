import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from yam_agri_core.yam_agri_core.doctype.lot.lot import check_certificates_for_dispatch
from yam_agri_core.yam_agri_core.doctype.qc_test.qc_test import QCTest
from yam_agri_core.yam_agri_core.site_permissions import enforce_qc_test_site_consistency


class TestDocValidations(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	def test_check_certificates_for_dispatch_raises_on_expired(self):
		site_doc = frappe.get_doc({"doctype": "Site", "site_name": "Test Site Checks"}).insert(ignore_permissions=True)
		site = site_doc.name

		lot_doc = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-EXP-1",
			"site": site,
			"qty_kg": 100
		}).insert(ignore_permissions=True)
		lot_name = lot_doc.name

		# Create expired certificate
		frappe.get_doc({
			"doctype": "Certificate",
			"cert_type": "Organic",
			"site": site,
			"expiry_date": "2020-01-01",
			"lot": lot_name
		}).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			check_certificates_for_dispatch(lot_name, "For Dispatch")

	def test_qc_test_freshness(self):
		doc = frappe.new_doc("QCTest")
		if not hasattr(doc, "days_since_test"):
			doc.days_since_test = QCTest.days_since_test.__get__(doc, type(doc))
			doc.is_fresh_for_season = QCTest.is_fresh_for_season.__get__(doc, type(doc))

		self.assertIsNone(doc.days_since_test())

		doc.test_date = add_days(nowdate(), -7)
		self.assertEqual(doc.days_since_test(), 7)
		self.assertTrue(doc.is_fresh_for_season(7))
		self.assertFalse(doc.is_fresh_for_season(6))

	def test_only_qa_manager_can_accept_lot(self):
		site_doc = frappe.get_doc({"doctype": "Site", "site_name": "Test Site Perms"}).insert(ignore_permissions=True)
		site = site_doc.name

		lot = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-PERMS-1",
			"site": site,
			"qty_kg": 100,
			"status": "Draft"
		}).insert(ignore_permissions=True)

		user = "test_no_qa@example.com"
		if not frappe.db.exists("User", user):
			user_doc = frappe.new_doc("User")
			user_doc.email = user
			user_doc.first_name = "Test No QA"
			user_doc.save(ignore_permissions=True)

		frappe.set_user(user)

		lot.status = "Accepted"
		with self.assertRaises(frappe.PermissionError):
			lot.save()

	def test_enforce_qc_site_consistency_blocks_cross_site(self):
		site_a_doc = frappe.get_doc({"doctype": "Site", "site_name": "Site A"}).insert(ignore_permissions=True)
		site_a = site_a_doc.name

		site_b_doc = frappe.get_doc({"doctype": "Site", "site_name": "Site B"}).insert(ignore_permissions=True)
		site_b = site_b_doc.name

		lot_doc = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-SITE-A",
			"site": site_a,
			"qty_kg": 100
		}).insert(ignore_permissions=True)
		lot_name = lot_doc.name

		doc_dict = {"lot": lot_name, "site": site_b}

		with self.assertRaises(frappe.ValidationError):
			enforce_qc_test_site_consistency(doc_dict)

	def test_enforce_qc_site_consistency_allows_same_site(self):
		site_a_doc = frappe.get_doc({"doctype": "Site", "site_name": "Site A"}).insert(ignore_permissions=True)
		site_a = site_a_doc.name

		lot_doc = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-SITE-A-OK",
			"site": site_a,
			"qty_kg": 100
		}).insert(ignore_permissions=True)
		lot_name = lot_doc.name

		# Should not raise
		enforce_qc_test_site_consistency({"lot": lot_name, "site": site_a})
