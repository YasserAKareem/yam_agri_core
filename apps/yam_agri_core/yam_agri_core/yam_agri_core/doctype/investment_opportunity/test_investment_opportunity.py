# Copyright (c) 2026, YAM Agri Core and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestInvestmentOpportunity(FrappeTestCase):
	"""Test cases for Investment Opportunity DocType."""

	def setUp(self):
		"""Set up test data."""
		# Create test site if not exists
		if not frappe.db.exists("Site", "Test Site"):
			site = frappe.new_doc("Site")
			site.site_name = "Test Site"
			site.site_type = "Office"
			site.insert(ignore_permissions=True)

	def test_create_opportunity(self):
		"""Test creating a basic investment opportunity."""
		opp = frappe.new_doc("Investment Opportunity")
		opp.opportunity_name = "Test Manufacturing Plant"
		opp.site = "Test Site"
		opp.sector = "Manufacturing"
		opp.investment_size = 5000000
		opp.insert(ignore_permissions=True)

		self.assertEqual(opp.gtd_status, "Captured")
		self.assertEqual(opp.stage, "Lead")
		self.assertEqual(opp.priority, "High")  # Auto-set due to $5M threshold

	def test_site_required(self):
		"""Test that site is required."""
		opp = frappe.new_doc("Investment Opportunity")
		opp.opportunity_name = "Test Opportunity"
		opp.sector = "Technology"
		opp.investment_size = 1000000

		with self.assertRaises(frappe.ValidationError):
			opp.insert(ignore_permissions=True)

	def test_next_action_validation(self):
		"""Test that next action requires owner when status is Next Action."""
		opp = frappe.new_doc("Investment Opportunity")
		opp.opportunity_name = "Test Opportunity"
		opp.site = "Test Site"
		opp.sector = "Technology"
		opp.investment_size = 1000000
		opp.gtd_status = "Next Action"

		with self.assertRaises(frappe.ValidationError):
			opp.insert(ignore_permissions=True)

	def test_priority_auto_calculation(self):
		"""Test automatic priority calculation."""
		# High priority due to investment size
		opp1 = frappe.new_doc("Investment Opportunity")
		opp1.opportunity_name = "Large Investment"
		opp1.site = "Test Site"
		opp1.sector = "Energy"
		opp1.investment_size = 10000000
		opp1.insert(ignore_permissions=True)
		self.assertEqual(opp1.priority, "High")

		# High priority due to job creation
		opp2 = frappe.new_doc("Investment Opportunity")
		opp2.opportunity_name = "Job Creator"
		opp2.site = "Test Site"
		opp2.sector = "Manufacturing"
		opp2.investment_size = 500000
		opp2.expected_jobs = 150
		opp2.insert(ignore_permissions=True)
		self.assertEqual(opp2.priority, "High")

		# Low priority
		opp3 = frappe.new_doc("Investment Opportunity")
		opp3.opportunity_name = "Small Investment"
		opp3.site = "Test Site"
		opp3.sector = "Services"
		opp3.investment_size = 100000
		opp3.expected_jobs = 5
		opp3.insert(ignore_permissions=True)
		self.assertEqual(opp3.priority, "Low")
