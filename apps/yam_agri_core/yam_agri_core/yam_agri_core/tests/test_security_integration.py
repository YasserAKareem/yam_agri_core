from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate


class TestSecurityIntegration(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.site_a = self.create_site("Security Site A")
		self.site_b = self.create_site("Security Site B")

		# Create a standard user (no QA Manager role)
		self.user_std = "std_user@example.com"
		self.create_user(self.user_std, "Standard User", ["Stock User"])

		# Reset roles to ensure no pollution from previous tests
		user_doc = frappe.get_doc("User", self.user_std)
		user_doc.roles = []
		user_doc.add_roles("Stock User")

		# Create a QA Manager user
		self.user_qa = "qa_manager@example.com"
		self.create_user(self.user_qa, "QA Manager User", ["QA Manager"])

		# Give QA Manager access to both sites
		for site in [self.site_a, self.site_b]:
			if not frappe.db.exists("User Permission", {"user": self.user_qa, "allow": "Site", "for_value": site}):
				frappe.get_doc({
					"doctype": "User Permission",
					"user": self.user_qa,
					"allow": "Site",
					"for_value": site
				}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def create_site(self, name):
		if not frappe.db.exists("Site", {"site_name": name}):
			doc = frappe.get_doc({"doctype": "Site", "site_name": name})
			doc.insert(ignore_permissions=True)
			return doc.name
		return frappe.db.get_value("Site", {"site_name": name}, "name")

	def create_user(self, email, first_name, roles=None):
		if not frappe.db.exists("User", email):
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = first_name
			user.enabled = 1
			user.insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", email)

		if roles:
			user.add_roles(*roles)
		return user

	def test_transfer_approval_requires_qa_role(self):
		frappe.set_user("Administrator")
		lot_a_doc = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-TRF-SEC-1",
			"site": self.site_a,
			"qty_kg": 500,
			"status": "Draft"
		})
		lot_a_doc.insert(ignore_permissions=True)
		# Force status to Accepted to simulate existing accepted lot
		frappe.db.set_value("Lot", lot_a_doc.name, "status", "Accepted")

		transfer_doc = frappe.get_doc({
			"doctype": "Transfer",
			"site": self.site_a,
			"transfer_type": "Move",
			"from_lot": lot_a_doc.name,
			"qty_kg": 100,
			"status": "Draft"
		})
		transfer_doc.insert(ignore_permissions=True)
		transfer_name = transfer_doc.name

		# Standard User -> Fail
		frappe.set_user(self.user_std)
		frappe.clear_cache(user=self.user_std)
		# Re-fetch as std user to ensure permissions apply on load if checked there
		doc = frappe.get_doc("Transfer", transfer_name)
		doc.status = "Approved"

		with self.assertRaises(frappe.PermissionError):
			doc.save()

		# QA Manager -> Success
		frappe.set_user(self.user_qa)
		doc = frappe.get_doc("Transfer", transfer_name)
		doc.status = "Approved"
		doc.save()

		self.assertEqual(frappe.db.get_value("Transfer", transfer_name, "status"), "Approved")

	def test_evidence_pack_approval_requires_qa_role(self):
		frappe.set_user("Administrator")
		ep_doc = frappe.get_doc({
			"doctype": "EvidencePack",
			"title": "Audit Pack 2026",
			"site": self.site_b,
			"status": "Draft",
			"from_date": nowdate(),
			"to_date": nowdate()
		})
		ep_doc.insert(ignore_permissions=True)
		ep_name = ep_doc.name

		# Standard User -> Fail
		frappe.set_user(self.user_std)
		doc = frappe.get_doc("EvidencePack", ep_name)
		doc.status = "Approved"

		with self.assertRaises(frappe.PermissionError):
			doc.save()

		# QA Manager -> Success
		frappe.set_user(self.user_qa)
		doc = frappe.get_doc("EvidencePack", ep_name)
		doc.status = "Approved"
		doc.save()

		self.assertEqual(frappe.db.get_value("EvidencePack", ep_name, "status"), "Approved")

	def test_site_isolation_query(self):
		frappe.set_user("Administrator")

		# User Permission: Standard User -> Site A
		perm_exists = frappe.db.exists("User Permission", {
			"user": self.user_std,
			"allow": "Site",
			"for_value": self.site_a
		})
		if not perm_exists:
			frappe.get_doc({
				"doctype": "User Permission",
				"user": self.user_std,
				"allow": "Site",
				"for_value": self.site_a
			}).insert(ignore_permissions=True)

		# Data
		lot_a = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-ISO-A",
			"site": self.site_a,
			"qty_kg": 100
		}).insert(ignore_permissions=True).name

		lot_b = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-ISO-B",
			"site": self.site_b,
			"qty_kg": 100
		}).insert(ignore_permissions=True).name

		# Test
		# Use a user with read access to Lot (e.g. QA Manager) but restrict via User Permission

		# Give Standard User the QA Manager role just for this test so they can read Lot
		user_doc = frappe.get_doc("User", self.user_std)
		user_doc.add_roles("QA Manager")

		frappe.set_user(self.user_std)
		frappe.clear_cache(user=self.user_std)

		lots = frappe.get_list("Lot", pluck="name")

		self.assertIn(lot_a, lots)
		self.assertNotIn(lot_b, lots)

	def test_site_isolation_direct_read(self):
		frappe.set_user("Administrator")

		# Reuse permission logic (idempotent check)
		perm_exists = frappe.db.exists("User Permission", {
			"user": self.user_std,
			"allow": "Site",
			"for_value": self.site_a
		})
		if not perm_exists:
			frappe.get_doc({
				"doctype": "User Permission",
				"user": self.user_std,
				"allow": "Site",
				"for_value": self.site_a
			}).insert(ignore_permissions=True)

		lot_b = frappe.get_doc({
			"doctype": "Lot",
			"lot_number": "LOT-ISO-READ-B",
			"site": self.site_b,
			"qty_kg": 100
		}).insert(ignore_permissions=True).name

		# Test
		# Give Standard User the QA Manager role just for this test so they can read Lot
		user_doc = frappe.get_doc("User", self.user_std)
		user_doc.add_roles("QA Manager")

		frappe.set_user(self.user_std)
		frappe.clear_cache(user=self.user_std)

		# Should raise PermissionError because user only has access to Site A
		with self.assertRaises(frappe.PermissionError):
			doc = frappe.get_doc("Lot", lot_b)
			doc.check_permission("read")
