# Copyright (c) 2026, YAM Agri Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from yam_agri_core.yam_agri_core.site_permissions import assert_site_access


class InvestmentOpportunity(Document):
	"""Investment Opportunity tracking with GTD methodology integration."""

	def before_insert(self):
		"""Set defaults for new opportunities."""
		if not self.get("gtd_status"):
			self.gtd_status = "Captured"
		if not self.get("stage"):
			self.stage = "Lead"
		if not self.get("priority"):
			self.priority = "Medium"
		if not self.get("risk_level"):
			self.risk_level = "Medium"

	def validate(self):
		"""Validate investment opportunity data."""
		# 1. Non-negotiable site check
		if not self.get("site"):
			frappe.throw(_("Every opportunity must belong to a Site"), frappe.ValidationError)
		assert_site_access(self.get("site"))

		# 2. Validate investment size
		if self.get("investment_size") and self.investment_size < 0:
			frappe.throw(_("Investment size cannot be negative"), frappe.ValidationError)

		# 3. Validate timeline
		if self.get("timeline_months") and self.timeline_months < 0:
			frappe.throw(_("Timeline cannot be negative"), frappe.ValidationError)

		# 4. Validate expected jobs
		if self.get("expected_jobs") and self.expected_jobs < 0:
			frappe.throw(_("Expected jobs cannot be negative"), frappe.ValidationError)

		# 5. GTD Next Action validation
		if self.gtd_status in ["Next Action", "Project"]:
			if not self.get("next_action"):
				frappe.throw(
					_("Next Action is required when GTD status is '{0}'").format(self.gtd_status),
					frappe.ValidationError,
				)
			if not self.get("next_action_owner"):
				frappe.throw(
					_("Next Action Owner is required when GTD status is '{0}'").format(self.gtd_status),
					frappe.ValidationError,
				)

		# 6. Auto-calculate priority based on investment size and jobs
		if self.get("investment_size") or self.get("expected_jobs"):
			self._auto_calculate_priority()

	def _auto_calculate_priority(self):
		"""Auto-calculate priority based on investment size and job creation."""
		# Thresholds from environment or defaults
		high_investment = frappe.conf.get("GTD_HIGH_PRIORITY_THRESHOLD", 5000000)  # $5M
		high_jobs = frappe.conf.get("GTD_JOB_CREATION_THRESHOLD", 100)  # 100 jobs

		investment = self.get("investment_size") or 0
		jobs = self.get("expected_jobs") or 0

		# Don't override manually set High priority
		if self.priority == "High":
			return

		# Auto-set to High if meets thresholds
		if investment >= high_investment or jobs >= high_jobs:
			self.priority = "High"
		elif investment >= (high_investment / 5) or jobs >= (high_jobs / 5):
			# Medium threshold: 20% of high threshold
			self.priority = "Medium"
		else:
			self.priority = "Low"

	def on_update(self):
		"""Update tracking fields on save."""
		import datetime

		self.db_set("modified_date", datetime.date.today(), update_modified=False)

	@frappe.whitelist()
	def get_ai_analysis(self):
		"""Get AI analysis for this opportunity (assistive only)."""
		# Call AI Gateway for opportunity analysis
		try:
			import requests

			ai_gateway_url = frappe.conf.get("AI_GATEWAY_URL", "http://ai-gateway:8089/suggest")
			timeout = frappe.conf.get("AI_GATEWAY_TIMEOUT", 20)

			payload = {
				"task": "opportunity-analysis",
				"site": self.site,
				"record_type": "Investment Opportunity",
				"record_name": self.name,
				"template_id": "opportunity_analysis",
				"template_vars": {
					"opportunity_name": self.opportunity_name,
					"sector": self.sector or "Unspecified",
					"investment_size": f"${self.investment_size:,.0f}" if self.investment_size else "TBD",
					"description": self.description or "No description provided",
					"context": f"Jobs: {self.expected_jobs or 'TBD'}, Exports: {self.expected_exports or 'TBD'}, Timeline: {self.timeline_months or 'TBD'} months",
				},
			}

			response = requests.post(ai_gateway_url, json=payload, timeout=timeout)
			response.raise_for_status()

			result = response.json()
			if result.get("ok"):
				# Update AI analysis field (read-only, assistive only)
				self.db_set("ai_analysis_summary", result.get("suggestion", ""), update_modified=False)
				return {"success": True, "analysis": result.get("suggestion")}
			else:
				return {"success": False, "error": "AI analysis failed"}

		except Exception as e:
			frappe.log_error(f"AI analysis error: {str(e)}", "Investment Opportunity AI Analysis")
			return {"success": False, "error": str(e)}
