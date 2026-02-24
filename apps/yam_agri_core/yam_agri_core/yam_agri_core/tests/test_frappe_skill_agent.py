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
	QCFinding,
	QCReport,
	_finding,
	check_ai_writes_frappe,
	check_broad_except,
	check_hardcoded_emails,
	check_missing_cross_site_lot_validation,
	check_missing_translations,
	check_perm_query_has_permission_parity,
	print_text_report,
	register_bug_type,
	run_qc,
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
			'permission_query_conditions = {\n'
			'    "Lot": "yam.lot_qc",\n'
			'    "Site": "yam.site_qc",\n'
			'}\n'
			'has_permission = {\n'
			'    "Lot": "yam.lot_hp",\n'
			'    # Site is intentionally missing!\n'
			'}\n'
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
		report.add(_finding(
			severity="high",
			rule_id="FS-009",
			bug_code="5.2.4",
			file="test.py",
			line=10,
			message="test cross-site",
		))
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
		report.add(_finding(
			severity="medium",
			rule_id="FS-003",
			bug_code="1.1.1",
			file="a.json",
			line=None,
			message="medium",
		))
		self.assertTrue(report.passed())
		report.add(_finding(
			severity="high",
			rule_id="FS-009",
			bug_code="5.2.4",
			file="b.py",
			line=1,
			message="high",
		))
		self.assertFalse(report.passed())


class TestPrintTextReport(unittest.TestCase):
	"""Verify print_text_report output format."""

	def test_text_report_shows_classification(self):
		import io
		from contextlib import redirect_stdout

		report = QCReport(app_path="/tmp")
		report.add(_finding(
			severity="high",
			rule_id="FS-001",
			bug_code="6.3.1",
			file="site_permissions.py",
			line=42,
			message="untranslated throw",
		))

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
		report.add(_finding(
			severity="medium",
			rule_id="FS-008",
			bug_code="2.2.4",
			file="api.py",
			line=10,
			message="broad except",
		))

		buf_default = io.StringIO()
		with redirect_stdout(buf_default):
			print_text_report(report, verbose=False)
		self.assertNotIn("Planned Response", buf_default.getvalue())

		buf_verbose = io.StringIO()
		with redirect_stdout(buf_verbose):
			print_text_report(report, verbose=True)
		self.assertIn("Planned Response", buf_verbose.getvalue())
