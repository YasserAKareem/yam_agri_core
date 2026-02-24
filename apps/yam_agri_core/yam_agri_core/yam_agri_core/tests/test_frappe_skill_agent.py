"""Tests for the Frappe Skill QC Agent — taxonomy and planned response features.

These are pure-Python tests that do NOT require a live Frappe instance.
Run via:
    pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_frappe_skill_agent.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

# Make the tools/ directory importable so we can import frappe_skill_agent directly.
_TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "tools"))
if _TOOLS_DIR not in sys.path:
	sys.path.insert(0, _TOOLS_DIR)

from frappe_skill_agent import (
	TAXONOMY,
	BugDefinition,
	LearnedRule,
	QCFinding,
	QCReport,
	TrainingDataset,
	_compute_coverage,
	_finding,
	_td,
	check_ai_writes_frappe,
	check_auto_learn_patterns,
	check_broad_except,
	check_hardcoded_business_logic,
	check_hardcoded_cloud_config,
	check_hardcoded_credentials,
	check_hardcoded_db_config,
	check_hardcoded_emails,
	check_hardcoded_feature_flags,
	check_hardcoded_server_config,
	check_master_doctype_audit_trail,
	check_master_doctype_required_fields,
	check_missing_cross_site_lot_validation,
	check_missing_translations,
	check_perm_query_has_permission_parity,
	coverage_stats,
	load_taxonomy_from_file,
	print_text_report,
	propose_bug_type,
	register_bug_type,
	run_qc,
	save_learned_rules,
)


class TestTaxonomyRegistry(unittest.TestCase):
	"""Verify the bug taxonomy is correctly populated."""

	def test_taxonomy_has_all_mapped_codes(self):
		# Codes referenced by the FS rules must exist in the registry
		required = [
			"1.1.1",  # FS-003 site reqd
			"1.1.2",  # FS-007 default in validate
			"2.2.4",  # FS-008 broad except
			"2.3.3",  # FS-005 track_changes
			"5.2.2",  # FS-010 AI writes
			"5.2.3",  # FS-011 perm parity
			"5.2.4",  # FS-009 cross-site lot
			"5.3.3",  # FS-006 hardcoded email
			"6.1.4",  # FS-004 title_field
			"6.3.1",  # FS-001/002 translations
			"10.1.1",  # FS-011 reverse parity
			# New v3 codes
			"11.1.1",  # FS-012 passwords
			"11.1.2",  # FS-012 API keys
			"11.1.3",  # FS-012 tokens
			"11.2.1",  # FS-014 DB config
			"11.2.2",  # FS-013 server config
			"11.2.3",  # FS-016 cloud config
			"11.3.1",  # FS-015 business logic
			"11.3.2",  # hardcoded UI strings
			"11.3.3",  # FS-019 feature flags
			"12.1.1",  # missing master records
			"12.1.2",  # FS-018 incomplete attributes
			"12.1.3",  # orphan records
			"12.2.1",  # incorrect values
			"12.2.3",  # outdated data
			"12.3.1",  # cross-system inconsistency
			"12.3.3",  # duplication
			"12.4.1",  # broken links
			"12.4.3",  # FK violations
			"12.5.1",  # policy violations
			"12.5.2",  # FS-017 audit failures
			"12.5.3",  # master data security
		]
		for code in required:
			self.assertIn(code, TAXONOMY, f"Taxonomy code {code} missing from TAXONOMY registry")

	def test_every_definition_has_planned_response(self):
		for code, defn in TAXONOMY.items():
			self.assertTrue(
				len(defn.planned_response) >= 2,
				f"Bug definition {code} has fewer than 2 planned_response steps",
			)

	def test_every_planned_response_starts_with_step(self):
		for code, defn in TAXONOMY.items():
			for step in defn.planned_response:
				self.assertTrue(
					step.startswith("Step"),
					f"Bug {code}: planned_response step does not start with 'Step': {step!r}",
				)

	def test_register_custom_bug_type(self):
		custom = BugDefinition(
			code="99.1.1",
			category="Custom Test Category",
			subcategory="Test Sub",
			bug_type="Test Bug",
			predefined_message="Test predefined message",
			planned_response=("Step 1: Test step one", "Step 2: Test step two"),
		)
		register_bug_type(custom)
		self.assertIn("99.1.1", TAXONOMY)
		self.assertEqual(TAXONOMY["99.1.1"].category, "Custom Test Category")
		# Cleanup
		del TAXONOMY["99.1.1"]

	def test_register_overwrites_existing(self):
		original = TAXONOMY.get("1.1.1")
		if original is None:
			self.skipTest("1.1.1 not in TAXONOMY")
		overwrite = BugDefinition(
			code="1.1.1",
			category="Overwritten Category",
			subcategory="Overwritten Sub",
			bug_type="Overwritten Type",
			predefined_message="Overwritten message",
			planned_response=("Step 1: Overwritten step",),
		)
		register_bug_type(overwrite)
		self.assertEqual(TAXONOMY["1.1.1"].category, "Overwritten Category")
		# Restore
		TAXONOMY["1.1.1"] = original


class TestFindingFactory(unittest.TestCase):
	"""Verify _finding() picks up taxonomy metadata correctly."""

	def test_known_code_populates_category(self):
		f = _finding(
			severity="critical",
			rule_id="FS-001",
			bug_code="6.3.1",
			file="test.py",
			line=1,
			message="test message",
		)
		self.assertEqual(f.category, "UI/UX Bugs")
		self.assertEqual(f.subcategory, "Interaction")
		self.assertIsInstance(f.planned_response, tuple)
		self.assertTrue(len(f.planned_response) >= 2)

	def test_unknown_code_falls_back_gracefully(self):
		f = _finding(
			severity="low",
			rule_id="FS-XX",
			bug_code="0.0.0",
			file="test.py",
			line=None,
			message="unknown",
		)
		self.assertEqual(f.category, "Unknown")
		self.assertEqual(len(f.planned_response), 2)
		self.assertTrue(f.planned_response[0].startswith("Step"))

	def test_custom_planned_response_overrides_taxonomy(self):
		f = _finding(
			severity="medium",
			rule_id="FS-001",
			bug_code="6.3.1",
			file="test.py",
			line=5,
			message="test",
			planned_response=["Step 1: Custom step"],
		)
		self.assertEqual(f.planned_response, ("Step 1: Custom step",))


class TestChecks(unittest.TestCase):
	"""Smoke-test each check function using temporary files."""

	def _write_tmp(self, content: str, suffix: str = ".py") -> str:
		"""Write content to a temp file and return its path."""
		fd, path = tempfile.mkstemp(suffix=suffix)
		os.close(fd)
		with open(path, "w", encoding="utf-8") as fh:
			fh.write(content)
		return path

	# ── FS-001 ────────────────────────────────────────────────────────────

	def test_fs001_detects_raw_throw(self):
		path = self._write_tmp('frappe.throw("bad message")\n')
		report = QCReport(app_path="/tmp")
		check_missing_translations(report, path, "/tmp")
		self.assertEqual(len(report.critical), 1)
		f = report.critical[0]
		self.assertEqual(f.rule_id, "FS-001")
		self.assertEqual(f.bug_code, "6.3.1")
		self.assertIn("Step", f.planned_response[0])
		os.unlink(path)

	def test_fs001_ignores_translated_throw(self):
		path = self._write_tmp('frappe.throw(_("good message"), frappe.ValidationError)\n')
		report = QCReport(app_path="/tmp")
		check_missing_translations(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	# ── FS-006 ────────────────────────────────────────────────────────────

	def test_fs006_detects_inline_email(self):
		path = self._write_tmp('some_func("user@example.com")\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_emails(report, path, "/tmp")
		self.assertEqual(len(report.high), 1)
		f = report.high[0]
		self.assertEqual(f.bug_code, "5.3.3")
		os.unlink(path)

	def test_fs006_ignores_constant_definition(self):
		path = self._write_tmp('_USER_A = "user@example.com"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_emails(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	# ── FS-008 ────────────────────────────────────────────────────────────

	def test_fs008_detects_broad_except(self):
		path = self._write_tmp("try:\n\tdo_something()\nexcept Exception:\n\treturn []\n")
		report = QCReport(app_path="/tmp")
		check_broad_except(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		f = report.medium[0]
		self.assertEqual(f.rule_id, "FS-008")
		self.assertEqual(f.bug_code, "2.2.4")
		os.unlink(path)

	def test_fs008_ignores_narrow_except(self):
		path = self._write_tmp("try:\n\tdo_something()\nexcept ValueError:\n\treturn []\n")
		report = QCReport(app_path="/tmp")
		check_broad_except(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	# ── FS-009 ────────────────────────────────────────────────────────────

	def test_fs009_detects_missing_cross_site_check(self):
		# Fake a doctype path
		tmpdir = tempfile.mkdtemp()
		dt_dir = os.path.join(tmpdir, "doctype", "mydt")
		os.makedirs(dt_dir)
		path = os.path.join(dt_dir, "mydt.py")
		with open(path, "w") as fh:
			fh.write("def validate(self):\n\t_ = self.get('lot')\n")
		report = QCReport(app_path=tmpdir)
		check_missing_cross_site_lot_validation(report, path, tmpdir)
		self.assertTrue(len(report.high) >= 1)
		f = report.high[0]
		self.assertEqual(f.bug_code, "5.2.4")
		self.assertIn("Step", f.planned_response[0])
		import shutil

		shutil.rmtree(tmpdir)

	# ── FS-010 ────────────────────────────────────────────────────────────

	def test_fs010_detects_ai_write(self):
		tmpdir = tempfile.mkdtemp()
		ai_dir = os.path.join(tmpdir, "ai")
		os.makedirs(ai_dir)
		path = os.path.join(ai_dir, "model.py")
		with open(path, "w") as fh:
			fh.write("doc = frappe.get_doc('Lot', name)\ndoc.save()\n")
		report = QCReport(app_path=tmpdir)
		check_ai_writes_frappe(report, path, tmpdir)
		self.assertTrue(len(report.critical) >= 1)
		f = report.critical[0]
		self.assertEqual(f.bug_code, "5.2.2")
		import shutil

		shutil.rmtree(tmpdir)

	# ── FS-011 ────────────────────────────────────────────────────────────

	def test_fs011_detects_pqc_without_hp(self):
		content = (
			"permission_query_conditions = {\n"
			'    "Lot": "yam.lot_qc",\n'
			'    "Site": "yam.site_qc",\n'
			"}\n"
			"has_permission = {\n"
			'    "Lot": "yam.lot_hp",\n'
			"    # Site is intentionally missing!\n"
			"}\n"
		)
		tmpdir = tempfile.mkdtemp()
		hooks_path = os.path.join(tmpdir, "hooks.py")
		with open(hooks_path, "w") as fh:
			fh.write(content)
		report = QCReport(app_path=tmpdir)
		check_perm_query_has_permission_parity(hooks_path, report, tmpdir)
		self.assertTrue(len(report.critical) >= 1)
		codes = {f.bug_code for f in report.critical}
		self.assertIn("5.2.3", codes)
		import shutil

		shutil.rmtree(tmpdir)


class TestQCReport(unittest.TestCase):
	"""Test QCReport serialisation with the new fields."""

	def test_to_dict_includes_taxonomy_fields(self):
		report = QCReport(app_path="/tmp")
		report.add(
			_finding(
				severity="high",
				rule_id="FS-009",
				bug_code="5.2.4",
				file="test.py",
				line=10,
				message="test cross-site",
			)
		)
		d = report.to_dict()
		self.assertEqual(d["summary"]["high"], 1)
		finding = d["findings"][0]
		self.assertIn("bug_code", finding)
		self.assertIn("category", finding)
		self.assertIn("subcategory", finding)
		self.assertIn("bug_type", finding)
		self.assertIn("planned_response", finding)
		self.assertIsInstance(finding["planned_response"], list)
		self.assertTrue(len(finding["planned_response"]) >= 1)

	def test_passed_only_when_no_critical_or_high(self):
		report = QCReport(app_path="/tmp")
		self.assertTrue(report.passed())
		report.add(
			_finding(
				severity="medium",
				rule_id="FS-003",
				bug_code="1.1.1",
				file="a.json",
				line=None,
				message="medium",
			)
		)
		self.assertTrue(report.passed())
		report.add(
			_finding(
				severity="high",
				rule_id="FS-009",
				bug_code="5.2.4",
				file="b.py",
				line=1,
				message="high",
			)
		)
		self.assertFalse(report.passed())


class TestPrintTextReport(unittest.TestCase):
	"""Verify print_text_report output format."""

	def test_text_report_shows_classification(self):
		import io
		from contextlib import redirect_stdout

		report = QCReport(app_path="/tmp")
		report.add(
			_finding(
				severity="high",
				rule_id="FS-001",
				bug_code="6.3.1",
				file="site_permissions.py",
				line=42,
				message="untranslated throw",
			)
		)

		buf = io.StringIO()
		with redirect_stdout(buf):
			print_text_report(report, verbose=False)

		output = buf.getvalue()
		self.assertIn("FS-001 / 6.3.1", output)
		self.assertIn("Classification", output)
		self.assertIn("UI/UX Bugs", output)
		# High severity always shows planned response (even without --verbose)
		self.assertIn("Planned Response", output)

	def test_verbose_shows_response_for_medium(self):
		import io
		from contextlib import redirect_stdout

		report = QCReport(app_path="/tmp")
		report.add(
			_finding(
				severity="medium",
				rule_id="FS-008",
				bug_code="2.2.4",
				file="api.py",
				line=10,
				message="broad except",
			)
		)

		buf_default = io.StringIO()
		with redirect_stdout(buf_default):
			print_text_report(report, verbose=False)
		self.assertNotIn("Planned Response", buf_default.getvalue())

		buf_verbose = io.StringIO()
		with redirect_stdout(buf_verbose):
			print_text_report(report, verbose=True)
		self.assertIn("Planned Response", buf_verbose.getvalue())


class TestHardcodedChecks(unittest.TestCase):
	"""Tests for the new hardcoded-bug detection checks (FS-012 to FS-019)."""

	def _write_tmp(self, content: str, suffix: str = ".py") -> str:
		fd, path = tempfile.mkstemp(suffix=suffix)
		os.close(fd)
		with open(path, "w", encoding="utf-8") as fh:
			fh.write(content)
		return path

	# ── FS-012 / 11.1.x ──────────────────────────────────────────────────

	def test_fs012_detects_hardcoded_password(self):
		path = self._write_tmp('db_password = "SuperSecret123"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_credentials(report, path, "/tmp")
		self.assertEqual(len(report.critical), 1)
		f = report.critical[0]
		self.assertEqual(f.rule_id, "FS-012")
		self.assertEqual(f.bug_code, "11.1.1")
		self.assertIn("Step", f.planned_response[0])
		os.unlink(path)

	def test_fs012_detects_hardcoded_api_key(self):
		path = self._write_tmp('api_key = "abc123def456ghi789"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_credentials(report, path, "/tmp")
		self.assertEqual(len(report.critical), 1)
		self.assertEqual(report.critical[0].bug_code, "11.1.2")
		os.unlink(path)

	def test_fs012_detects_hardcoded_token(self):
		path = self._write_tmp('auth_token = "eyJhbGciOiJIUzI1NiJ9.payload"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_credentials(report, path, "/tmp")
		self.assertEqual(len(report.critical), 1)
		self.assertEqual(report.critical[0].bug_code, "11.1.3")
		os.unlink(path)

	def test_fs012_ignores_env_var_read(self):
		path = self._write_tmp('password = os.environ.get("DB_PASSWORD")\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_credentials(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	def test_fs012_ignores_placeholder(self):
		path = self._write_tmp('password = "CHANGE_ME"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_credentials(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	# ── FS-013 / 11.2.2 ──────────────────────────────────────────────────

	def test_fs013_detects_ip_address(self):
		path = self._write_tmp('host = "192.168.1.100"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_server_config(report, path, "/tmp")
		self.assertEqual(len(report.high), 1)
		self.assertEqual(report.high[0].bug_code, "11.2.2")
		os.unlink(path)

	def test_fs013_detects_localhost(self):
		path = self._write_tmp('db_host = "localhost"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_server_config(report, path, "/tmp")
		self.assertEqual(len(report.high), 1)
		os.unlink(path)

	def test_fs013_skips_test_files(self):
		fd, path = tempfile.mkstemp(prefix="test_", suffix=".py")
		os.close(fd)
		with open(path, "w") as fh:
			fh.write('host = "192.168.1.1"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_server_config(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	# ── FS-014 / 11.2.1 ──────────────────────────────────────────────────

	def test_fs014_detects_db_url(self):
		path = self._write_tmp('conn = "mysql://root:pass@localhost/mydb"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_db_config(report, path, "/tmp")
		self.assertEqual(len(report.high), 1)
		self.assertEqual(report.high[0].bug_code, "11.2.1")
		os.unlink(path)

	def test_fs014_detects_db_host_assignment(self):
		path = self._write_tmp('db_host = "production.server.internal"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_db_config(report, path, "/tmp")
		self.assertEqual(len(report.high), 1)
		os.unlink(path)

	# ── FS-015 / 11.3.1 ──────────────────────────────────────────────────

	def test_fs015_detects_hardcoded_tax_rate(self):
		path = self._write_tmp("tax_rate = 15\n")
		report = QCReport(app_path="/tmp")
		check_hardcoded_business_logic(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		self.assertEqual(report.medium[0].bug_code, "11.3.1")
		os.unlink(path)

	def test_fs015_detects_hardcoded_discount(self):
		path = self._write_tmp("discount_pct = 10\n")
		report = QCReport(app_path="/tmp")
		check_hardcoded_business_logic(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		os.unlink(path)

	# ── FS-016 / 11.2.3 ──────────────────────────────────────────────────

	def test_fs016_detects_s3_bucket(self):
		path = self._write_tmp('s3_bucket = "my-production-bucket"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_cloud_config(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		self.assertEqual(report.medium[0].bug_code, "11.2.3")
		os.unlink(path)

	def test_fs016_detects_aws_region(self):
		path = self._write_tmp('region = "us-east-1"\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_cloud_config(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		os.unlink(path)

	# ── FS-019 / 11.3.3 ──────────────────────────────────────────────────

	def test_fs019_detects_hardcoded_feature_flag(self):
		path = self._write_tmp("is_beta = False\n")
		report = QCReport(app_path="/tmp")
		check_hardcoded_feature_flags(report, path, "/tmp")
		self.assertEqual(len(report.low), 1)
		self.assertEqual(report.low[0].bug_code, "11.3.3")
		os.unlink(path)

	def test_fs019_detects_inline_user_check(self):
		path = self._write_tmp('if frappe.session.user == "owner@company.com":\n    pass\n')
		report = QCReport(app_path="/tmp")
		check_hardcoded_feature_flags(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		self.assertEqual(report.medium[0].bug_code, "11.3.3")
		os.unlink(path)


class TestMasterDataChecks(unittest.TestCase):
	"""Tests for FS-017 (master audit trail) and FS-018 (required fields)."""

	def _write_doctype_json(self, data: dict) -> str:
		fd, path = tempfile.mkstemp(suffix=".json")
		os.close(fd)
		with open(path, "w", encoding="utf-8") as fh:
			json.dump(data, fh)
		return path

	def _base_master(self, **overrides) -> dict:
		"""Minimal master DocType JSON (no naming_series, has site field)."""
		base = {
			"doctype": "DocType",
			"name": "Test Master",
			"fields": [
				{"fieldname": "site", "fieldtype": "Link", "options": "Site"},
				{"fieldname": "master_name", "fieldtype": "Data"},
			],
		}
		base.update(overrides)
		return base

	# ── FS-017 / 12.5.2 ──────────────────────────────────────────────────

	def test_fs017_master_missing_track_changes(self):
		path = self._write_doctype_json(self._base_master())
		report = QCReport(app_path="/tmp")
		check_master_doctype_audit_trail(report, path, "/tmp")
		self.assertEqual(len(report.medium), 1)
		self.assertEqual(report.medium[0].bug_code, "12.5.2")
		self.assertEqual(report.medium[0].rule_id, "FS-017")
		os.unlink(path)

	def test_fs017_master_with_track_changes_passes(self):
		path = self._write_doctype_json(self._base_master(track_changes=1))
		report = QCReport(app_path="/tmp")
		check_master_doctype_audit_trail(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	def test_fs017_skips_transaction_doctype(self):
		"""DocTypes with naming_series are transaction DocTypes; FS-005 handles them."""
		data = self._base_master()
		data["fields"].append({"fieldname": "naming_series", "fieldtype": "Select"})
		path = self._write_doctype_json(data)
		report = QCReport(app_path="/tmp")
		check_master_doctype_audit_trail(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	# ── FS-018 / 12.1.2 ──────────────────────────────────────────────────

	def test_fs018_master_missing_status_field(self):
		path = self._write_doctype_json(self._base_master())
		report = QCReport(app_path="/tmp")
		check_master_doctype_required_fields(report, path, "/tmp")
		self.assertEqual(len(report.low), 1)
		self.assertEqual(report.low[0].bug_code, "12.1.2")
		os.unlink(path)

	def test_fs018_master_with_status_passes(self):
		data = self._base_master()
		data["fields"].append({"fieldname": "status", "fieldtype": "Select"})
		path = self._write_doctype_json(data)
		report = QCReport(app_path="/tmp")
		check_master_doctype_required_fields(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)

	def test_fs018_master_with_is_active_passes(self):
		data = self._base_master()
		data["fields"].append({"fieldname": "is_active", "fieldtype": "Check"})
		path = self._write_doctype_json(data)
		report = QCReport(app_path="/tmp")
		check_master_doctype_required_fields(report, path, "/tmp")
		self.assertEqual(len(report.findings), 0)
		os.unlink(path)


class TestAutoLearning(unittest.TestCase):
	"""Tests for the auto-learning infrastructure."""

	def test_propose_bug_type_creates_learned_rule(self):
		rule = propose_bug_type(
			observed_pattern="cors = '*'",
			file="config.py",
			line=10,
			suggested_category="Hardcoded Bugs",
			suggested_subcategory="Hardcoded Environment & Config",
			suggested_bug_type="Server",
			proposed_message="Wildcard CORS",
			proposed_planned_response=["Step 1: Fix the CORS config", "Step 2: Test"],
			confidence="high",
		)
		self.assertIsInstance(rule, LearnedRule)
		self.assertTrue(rule.suggested_code.startswith("11.99."))
		self.assertEqual(rule.suggested_category, "Hardcoded Bugs")
		self.assertEqual(rule.confidence, "high")

	def test_propose_bug_type_unknown_category(self):
		rule = propose_bug_type(
			observed_pattern="some odd pattern",
			file="x.py",
			line=1,
			suggested_category="Completely New Category",
			suggested_subcategory="Novel Sub",
			suggested_bug_type="Novel Type",
			proposed_message="A novel issue",
			proposed_planned_response=["Step 1: Investigate"],
		)
		# Unknown categories get code 99.99.N
		self.assertTrue(rule.suggested_code.startswith("99.99."))

	def test_auto_learn_produces_learned_rule_for_novel_pattern(self):
		"""threading.Thread() maps to Concurrency Bugs / Thread leaks — not in TAXONOMY."""
		tmpdir = tempfile.mkdtemp()
		path = os.path.join(tmpdir, "worker.py")
		with open(path, "w") as fh:
			fh.write("t = threading.Thread(target=my_task)\nt.start()\n")
		report = QCReport(app_path=tmpdir)
		check_auto_learn_patterns(report, path, tmpdir)
		# Should produce a LearnedRule (not a QCFinding) because Concurrency Bugs is not in TAXONOMY
		self.assertTrue(len(report.learned_rules) >= 1)
		lr = report.learned_rules[0]
		self.assertEqual(lr.suggested_category, "Concurrency Bugs")
		self.assertEqual(lr.suggested_bug_type, "Thread leaks")
		import shutil

		shutil.rmtree(tmpdir)

	def test_auto_learn_produces_finding_for_known_pattern(self):
		"""cors_origins='*' maps to Hardcoded Bugs / Server — which IS in TAXONOMY."""
		tmpdir = tempfile.mkdtemp()
		path = os.path.join(tmpdir, "settings.py")
		with open(path, "w") as fh:
			fh.write('cors_origins = "*"\n')
		report = QCReport(app_path=tmpdir)
		check_auto_learn_patterns(report, path, tmpdir)
		# Should produce a QCFinding (not a LearnedRule)
		self.assertTrue(len(report.findings) >= 1)
		self.assertEqual(len(report.learned_rules), 0)
		import shutil

		shutil.rmtree(tmpdir)

	def test_save_and_load_learned_rules(self):
		rule = propose_bug_type(
			observed_pattern="debug = True",
			file="app.py",
			line=5,
			suggested_category="Security Bugs",
			suggested_subcategory="Data Protection",
			suggested_bug_type="Debug mode active",
			proposed_message="Debug mode may expose sensitive data",
			proposed_planned_response=["Step 1: Set debug=False in production", "Step 2: Restart"],
		)
		fd, path = tempfile.mkstemp(suffix=".json")
		os.close(fd)
		registered_code = rule.suggested_code
		try:
			save_learned_rules([rule], path)
			loaded = load_taxonomy_from_file(path)
			self.assertEqual(len(loaded), 1)
			defn = loaded[0]
			self.assertEqual(defn.category, "Security Bugs")
			self.assertEqual(defn.bug_type, "Debug mode active")
			self.assertIn(defn.code, __import__("frappe_skill_agent").TAXONOMY)
		finally:
			os.unlink(path)
			# Always clean up the test-registered entry so coverage stats remain 100%
			__import__("frappe_skill_agent").TAXONOMY.pop(registered_code, None)

	def test_qc_report_learned_rules_in_to_dict(self):
		report = QCReport(app_path="/tmp")
		rule = propose_bug_type(
			observed_pattern="example pattern",
			file="x.py",
			line=1,
			suggested_category="Hardcoded Bugs",
			suggested_subcategory="Hardcoded Credentials",
			suggested_bug_type="Passwords",
			proposed_message="Test",
			proposed_planned_response=["Step 1: Fix"],
		)
		report.add_learned(rule)
		d = report.to_dict()
		self.assertEqual(d["summary"]["learned_rules_proposed"], 1)
		self.assertEqual(len(d["learned_rules"]), 1)
		lr_dict = d["learned_rules"][0]
		self.assertIn("suggested_code", lr_dict)
		self.assertIn("proposed_planned_response", lr_dict)
		self.assertIn("confidence", lr_dict)

	def test_print_text_report_shows_learned_section(self):
		import io
		from contextlib import redirect_stdout

		report = QCReport(app_path="/tmp")
		rule = propose_bug_type(
			observed_pattern="threading.Thread()",
			file="worker.py",
			line=3,
			suggested_category="Concurrency Bugs",
			suggested_subcategory="Threading",
			suggested_bug_type="Thread leaks",
			proposed_message="Unmanaged thread",
			proposed_planned_response=["Step 1: Use a thread pool", "Step 2: Add join()"],
		)
		report.add_learned(rule)
		buf = io.StringIO()
		with redirect_stdout(buf):
			print_text_report(report)
		output = buf.getvalue()
		self.assertIn("Auto-Learned", output)
		self.assertIn("PROPOSED", output)
		self.assertIn("Concurrency Bugs", output)


class TestTrainingDataFields(unittest.TestCase):
	"""Tests for the v4 training-data fields on BugDefinition."""

	def test_all_taxonomy_entries_have_training_data(self):
		"""Every entry registered via _td() must have all 6 training-data fields."""
		incomplete = []
		for code, defn in TAXONOMY.items():
			score = _compute_coverage(defn)
			if score < 1.0:
				incomplete.append((code, round(score, 2)))
		self.assertEqual(
			incomplete,
			[],
			f"Some taxonomy entries have incomplete training data (score < 1.0): {incomplete}",
		)

	def test_coverage_stats_full_coverage(self):
		stats = coverage_stats()
		self.assertEqual(stats["total"], len(TAXONOMY))
		self.assertEqual(stats["coverage_pct"], 100.0, "Expected 100% full training coverage")
		self.assertEqual(stats["avg_score"], 1.0)

	def test_compute_coverage_all_fields_present(self):
		defn = BugDefinition(
			code="99.1.1",
			category="Test",
			subcategory="Test",
			bug_type="Test",
			predefined_message="msg",
			planned_response=("Step 1",),
			cwe_id="CWE-20",
			cwe_name="Test CWE",
			negative_example="bad code",
			positive_example="good code",
			telemetry_signatures=("log pattern",),
			ast_diff="Replace X with Y",
		)
		self.assertEqual(_compute_coverage(defn), 1.0)

	def test_compute_coverage_missing_training_fields(self):
		defn = BugDefinition(
			code="99.1.2",
			category="Test",
			subcategory="Test",
			bug_type="Test",
			predefined_message="msg",
			planned_response=("Step 1",),
			# cwe_id, negative_example, positive_example, telemetry_signatures, ast_diff all missing
		)
		# Only planned_response is present -> 1/6
		self.assertAlmostEqual(_compute_coverage(defn), round(1 / 6, 2))

	def test_cwe_ids_are_well_formed(self):
		"""All non-empty CWE IDs must match 'CWE-NNN' or be the sentinel 'N/A'."""
		import re

		pattern = re.compile(r"^CWE-\d+$")
		bad = []
		for code, defn in TAXONOMY.items():
			if defn.cwe_id and defn.cwe_id != "N/A" and not pattern.match(defn.cwe_id):
				bad.append((code, defn.cwe_id))
		self.assertEqual(bad, [], f"Malformed CWE IDs: {bad}")

	def test_td_helper_registers_with_training_data(self):
		"""_td() must register a BugDefinition with all training fields populated."""
		_td(
			"99.99.1",
			"Test Cat",
			"Test Sub",
			"Test Type",
			"test message",
			["Step 1"],
			cwe_id="CWE-20",
			cwe_name="Test CWE",
			negative_example="bad()",
			positive_example="good()",
			telemetry_signatures=["log pattern"],
			ast_diff="Call[bad] -> Call[good]",
		)
		defn = TAXONOMY["99.99.1"]
		self.assertEqual(defn.cwe_id, "CWE-20")
		self.assertEqual(defn.negative_example, "bad()")
		self.assertEqual(defn.positive_example, "good()")
		self.assertEqual(defn.telemetry_signatures, ("log pattern",))
		self.assertEqual(defn.ast_diff, "Call[bad] -> Call[good]")
		self.assertEqual(_compute_coverage(defn), 1.0)
		# Clean up test entry
		del TAXONOMY["99.99.1"]

	def test_negative_and_positive_examples_differ(self):
		"""Each taxonomy entry must have distinct negative and positive examples."""
		same = []
		for code, defn in TAXONOMY.items():
			if defn.negative_example and defn.negative_example == defn.positive_example:
				same.append(code)
		self.assertEqual(same, [], f"negative_example == positive_example for: {same}")

	def test_telemetry_signatures_are_non_empty_strings(self):
		"""All telemetry signatures must be non-empty strings."""
		bad = []
		for code, defn in TAXONOMY.items():
			for sig in defn.telemetry_signatures:
				if not isinstance(sig, str) or not sig.strip():
					bad.append((code, sig))
		self.assertEqual(bad, [], f"Empty or non-string telemetry signatures: {bad}")


class TestTrainingDataset(unittest.TestCase):
	"""Tests for TrainingDataset JSON-LD export."""

	def test_to_jsonld_returns_valid_structure(self):
		data = TrainingDataset.to_jsonld()
		self.assertIn("@context", data)
		self.assertIn("@graph", data)
		self.assertIn("yam:coverageStats", data)
		self.assertEqual(data["schema:version"], "4.0")

	def test_to_jsonld_context_has_required_namespaces(self):
		ctx = TrainingDataset.to_jsonld()["@context"]
		self.assertIn("yam", ctx)
		self.assertIn("cwe", ctx)
		self.assertIn("schema", ctx)
		self.assertIn("xsd", ctx)

	def test_to_jsonld_graph_contains_all_taxonomy_entries(self):
		graph = TrainingDataset.to_jsonld()["@graph"]
		self.assertEqual(len(graph), len(TAXONOMY))

	def test_to_jsonld_node_has_required_fields(self):
		graph = TrainingDataset.to_jsonld()["@graph"]
		node = graph[0]
		for field in (
			"@type",
			"@id",
			"yam:code",
			"yam:category",
			"yam:subcategory",
			"schema:name",
			"yam:predefinedMessage",
			"yam:plannedResponse",
			"yam:negativeExample",
			"yam:positiveExample",
			"yam:telemetrySignatures",
			"yam:astDiff",
			"yam:trainingCoverage",
		):
			self.assertIn(field, node, f"Missing field '{field}' in JSON-LD node")

	def test_to_jsonld_node_coverage_value_is_decimal_1(self):
		"""All nodes must report trainingCoverage 1.0 (100% coverage)."""
		graph = TrainingDataset.to_jsonld()["@graph"]
		bad_nodes = [n["@id"] for n in graph if n.get("yam:trainingCoverage", {}).get("@value") != "1.0"]
		self.assertEqual(bad_nodes, [], f"Nodes with coverage < 1.0: {bad_nodes}")

	def test_to_jsonld_cwe_node_has_reference_link(self):
		"""Nodes with a real CWE-NNN ID must include a cwe:reference @id link."""
		import re

		cwe_pattern = re.compile(r"^CWE-\d+$")
		graph = TrainingDataset.to_jsonld()["@graph"]
		# Only nodes with a proper CWE-NNN id (not N/A) should have a reference link
		cwe_nodes = [n for n in graph if cwe_pattern.match(n.get("cwe:id", ""))]
		self.assertGreater(len(cwe_nodes), 0, "Expected at least one node with a real CWE-NNN ID")
		for node in cwe_nodes:
			self.assertIn("cwe:reference", node)
			self.assertIn("@id", node["cwe:reference"])
			self.assertIn("cwe.mitre.org", node["cwe:reference"]["@id"])

	def test_to_jsonld_subset_export(self):
		"""A subset dict produces a smaller graph with correct coverage stats."""
		subset = {k: v for k, v in TAXONOMY.items() if v.category == "Security Bugs"}
		data = TrainingDataset.to_jsonld(subset)
		self.assertEqual(len(data["@graph"]), len(subset))
		self.assertEqual(data["yam:coverageStats"]["total"], len(subset))

	def test_to_jsonld_file_round_trip(self):
		"""to_jsonld_file() writes valid JSON that can be parsed back."""
		fd, path = tempfile.mkstemp(suffix=".json")
		os.close(fd)
		try:
			stats = TrainingDataset.to_jsonld_file(path)
			self.assertIsInstance(stats, dict)
			self.assertIn("coverage_pct", stats)
			with open(path, encoding="utf-8") as fh:
				reloaded = json.load(fh)
			self.assertIn("@graph", reloaded)
			self.assertEqual(len(reloaded["@graph"]), len(TAXONOMY))
		finally:
			os.unlink(path)

	def test_coverage_stats_empty_taxonomy(self):
		"""coverage_stats() with an empty dict returns zero values gracefully."""
		stats = coverage_stats({})
		self.assertEqual(stats["total"], 0)
		self.assertEqual(stats["coverage_pct"], 0.0)
		self.assertEqual(stats["avg_score"], 0.0)

	def test_qc_report_to_dict_includes_taxonomy_coverage(self):
		"""QCReport.to_dict() summary must include taxonomy_coverage with 100% stats."""
		report = QCReport(app_path="/tmp")
		d = report.to_dict()
		cov = d["summary"].get("taxonomy_coverage")
		self.assertIsNotNone(cov, "taxonomy_coverage missing from summary")
		self.assertEqual(cov["coverage_pct"], 100.0)
		self.assertEqual(cov["avg_score"], 1.0)

	def test_qc_report_finding_includes_cwe_fields(self):
		"""Each finding dict must include cwe_id, cwe_name, and training_coverage."""
		report = QCReport(app_path="/tmp")
		report.add(
			_finding(
				severity="high",
				rule_id="FS-001",
				bug_code="6.3.1",
				file="site.py",
				line=10,
				message="untranslated",
			)
		)
		d = report.to_dict()
		finding = d["findings"][0]
		self.assertIn("cwe_id", finding)
		self.assertIn("cwe_name", finding)
		self.assertIn("training_coverage", finding)
		self.assertEqual(finding["training_coverage"], 1.0)

	def test_print_text_report_shows_training_coverage(self):
		"""Text report header must include training coverage line."""
		import io
		from contextlib import redirect_stdout

		report = QCReport(app_path="/tmp")
		buf = io.StringIO()
		with redirect_stdout(buf):
			print_text_report(report)
		output = buf.getvalue()
		self.assertIn("Training", output)
		self.assertIn("100.0%", output)

	def test_print_text_report_shows_cwe_for_high_finding(self):
		"""High-severity findings must show the CWE ID in text report."""
		import io
		from contextlib import redirect_stdout

		report = QCReport(app_path="/tmp")
		report.add(
			_finding(
				severity="high",
				rule_id="FS-009",
				bug_code="5.2.4",
				file="complaint.py",
				line=42,
				message="missing cross-site check",
			)
		)
		buf = io.StringIO()
		with redirect_stdout(buf):
			print_text_report(report)
		output = buf.getvalue()
		self.assertIn("CWE-639", output)

	def test_load_taxonomy_from_file_preserves_training_fields(self):
		"""load_taxonomy_from_file() must round-trip all training-data fields."""
		entry = {
			"code": "99.50.1",
			"category": "Test",
			"subcategory": "Sub",
			"bug_type": "Type",
			"predefined_message": "msg",
			"planned_response": ["Step 1"],
			"cwe_id": "CWE-259",
			"cwe_name": "Hardcoded Password",
			"negative_example": "password = 'abc'",
			"positive_example": "password = os.environ.get('PASS')",
			"telemetry_signatures": ["grep: password= found"],
			"ast_diff": "Replace Constant with Call[os.environ.get]",
		}
		fd, path = tempfile.mkstemp(suffix=".json")
		os.close(fd)
		try:
			with open(path, "w") as fh:
				json.dump([entry], fh)
			loaded = load_taxonomy_from_file(path)
			self.assertEqual(len(loaded), 1)
			defn = loaded[0]
			self.assertEqual(defn.cwe_id, "CWE-259")
			self.assertEqual(defn.negative_example, "password = 'abc'")
			self.assertEqual(defn.positive_example, "password = os.environ.get('PASS')")
			self.assertEqual(defn.telemetry_signatures, ("grep: password= found",))
			self.assertEqual(defn.ast_diff, "Replace Constant with Call[os.environ.get]")
			self.assertEqual(_compute_coverage(defn), 1.0)
		finally:
			os.unlink(path)
			TAXONOMY.pop("99.50.1", None)
