"""Frappe Skill — Automated QC Agent for YAM Agri Core.

A pure-Python static analysis tool that checks a Frappe app directory for
common bugs and deviations from Frappe best practices. No live Frappe
instance is required; the agent operates on source files only.

Usage (from repo root):
    python tools/frappe_skill_agent.py
    python tools/frappe_skill_agent.py --app-path apps/yam_agri_core/yam_agri_core/yam_agri_core
    python tools/frappe_skill_agent.py --format json

The agent checks:
  - Missing _() / __() translations on user-facing strings
  - Missing site-field required (reqd) in DocType JSONs
  - Default values placed in on_update instead of before_insert
  - Missing cross-site validation for linked Lot fields
  - Silent broad except clauses that swallow errors
  - Missing title_field or track_changes in DocType JSONs
  - Hardcoded user emails / credentials in non-test Python files
  - Missing has_permission registration when permission_query_conditions exists
  - AI code paths that call frappe write APIs (save, insert, submit)
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class QCFinding:
	severity: str  # "critical" | "high" | "medium" | "low"
	rule_id: str
	file: str
	line: int | None
	message: str
	suggestion: str


@dataclass
class QCReport:
	app_path: str
	findings: list[QCFinding] = field(default_factory=list)

	def add(self, finding: QCFinding) -> None:
		self.findings.append(finding)

	@property
	def critical(self) -> list[QCFinding]:
		return [f for f in self.findings if f.severity == "critical"]

	@property
	def high(self) -> list[QCFinding]:
		return [f for f in self.findings if f.severity == "high"]

	@property
	def medium(self) -> list[QCFinding]:
		return [f for f in self.findings if f.severity == "medium"]

	@property
	def low(self) -> list[QCFinding]:
		return [f for f in self.findings if f.severity == "low"]

	def passed(self) -> bool:
		return len(self.critical) == 0 and len(self.high) == 0

	def to_dict(self) -> dict[str, Any]:
		return {
			"app_path": self.app_path,
			"summary": {
				"total": len(self.findings),
				"critical": len(self.critical),
				"high": len(self.high),
				"medium": len(self.medium),
				"low": len(self.low),
				"passed": self.passed(),
			},
			"findings": [
				{
					"severity": f.severity,
					"rule_id": f.rule_id,
					"file": f.file,
					"line": f.line,
					"message": f.message,
					"suggestion": f.suggestion,
				}
				for f in self.findings
			],
		}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rel(path: str, base: str) -> str:
	try:
		return os.path.relpath(path, base)
	except ValueError:
		return path


def _iter_python_files(root: str) -> list[str]:
	result = []
	for dirpath, _dirs, files in os.walk(root):
		for fname in files:
			if fname.endswith(".py") and "__pycache__" not in dirpath:
				result.append(os.path.join(dirpath, fname))
	return result


def _iter_json_files(root: str) -> list[str]:
	result = []
	for dirpath, _dirs, files in os.walk(root):
		for fname in files:
			if fname.endswith(".json") and "__pycache__" not in dirpath:
				result.append(os.path.join(dirpath, fname))
	return result


def _iter_js_files(root: str) -> list[str]:
	result = []
	for dirpath, _dirs, files in os.walk(root):
		for fname in files:
			if fname.endswith(".js") and "__pycache__" not in dirpath:
				result.append(os.path.join(dirpath, fname))
	return result


def _load_json(path: str) -> dict | list | None:
	try:
		with open(path, encoding="utf-8") as fh:
			return json.load(fh)
	except (json.JSONDecodeError, OSError):
		return None


def _read_lines(path: str) -> list[str]:
	try:
		with open(path, encoding="utf-8", errors="replace") as fh:
			return fh.readlines()
	except OSError:
		return []


# ---------------------------------------------------------------------------
# Rule checks
# ---------------------------------------------------------------------------


def check_missing_translations(report: QCReport, py_file: str, base: str) -> None:
	"""FS-001: frappe.throw() called with a raw string literal not wrapped in _()."""
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)

	# Pattern: frappe.throw("..." or frappe.throw('...') without _() wrapping
	pattern = re.compile(
		r"""frappe\.throw\s*\(\s*(?!_\s*\(|frappe\._\s*\()(?:f?['"])""",
	)
	for lineno, line in enumerate(lines, 1):
		if pattern.search(line):
			report.add(
				QCFinding(
					severity="critical",
					rule_id="FS-001",
					file=rel,
					line=lineno,
					message="frappe.throw() uses a raw string — not translatable",
					suggestion='Wrap the message in _(): frappe.throw(_("…"), ExcType)',
				)
			)


def check_missing_js_translations(report: QCReport, js_file: str, base: str) -> None:
	"""FS-002: User-visible JS string not wrapped in __()."""
	lines = _read_lines(js_file)
	rel = _rel(js_file, base)

	# Heuristic: frappe.msgprint / frappe.confirm / indicator with bare string
	patterns = [
		re.compile(r"""frappe\.msgprint\s*\(\s*['"]"""),
		re.compile(r"""frappe\.confirm\s*\(\s*['"]"""),
		re.compile(r"""frappe\.show_alert\s*\(\s*\{[^}]*message\s*:\s*['"]"""),
	]
	for lineno, line in enumerate(lines, 1):
		for p in patterns:
			if p.search(line):
				report.add(
					QCFinding(
						severity="high",
						rule_id="FS-002",
						file=rel,
						line=lineno,
						message="User-facing JavaScript string not wrapped in __()",
						suggestion='Use __("…") for all user-visible strings in JavaScript',
					)
				)
				break  # one finding per line


def check_doctype_json_site_required(report: QCReport, json_file: str, base: str) -> None:
	"""FS-003: DocType JSON — site field not marked reqd:1."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	rel = _rel(json_file, base)
	fields = {f.get("fieldname"): f for f in data.get("fields", [])}
	if "site" in fields and not fields["site"].get("reqd"):
		report.add(
			QCFinding(
				severity="medium",
				rule_id="FS-003",
				file=rel,
				line=None,
				message=f"DocType '{data.get('name')}': 'site' field is not marked reqd:1",
				suggestion='Add "reqd": 1 to the site field definition in the JSON',
			)
		)


def check_doctype_json_title_field(report: QCReport, json_file: str, base: str) -> None:
	"""FS-004: DocType JSON — missing title_field."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	# Skip system doctypes without a meaningful title (e.g., very simple masters)
	if not data.get("fields"):
		return
	rel = _rel(json_file, base)
	if not data.get("title_field"):
		report.add(
			QCFinding(
				severity="low",
				rule_id="FS-004",
				file=rel,
				line=None,
				message=f"DocType '{data.get('name')}': missing 'title_field'",
				suggestion="Set title_field to the most human-readable field (e.g. lot_number, site_name)",
			)
		)


def check_doctype_json_track_changes(report: QCReport, json_file: str, base: str) -> None:
	"""FS-005: DocType JSON — missing track_changes on transaction doctypes."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	# Only flag transaction-type DocTypes (those with a naming_series field)
	fields = {f.get("fieldname") for f in data.get("fields", [])}
	if "naming_series" not in fields:
		return
	rel = _rel(json_file, base)
	if not data.get("track_changes"):
		report.add(
			QCFinding(
				severity="medium",
				rule_id="FS-005",
				file=rel,
				line=None,
				message=f"DocType '{data.get('name')}': track_changes not enabled on a transaction DocType",
				suggestion='Add "track_changes": 1 to enable audit trail for food safety compliance',
			)
		)


def check_hardcoded_emails(report: QCReport, py_file: str, base: str) -> None:
	"""FS-006: Hardcoded email addresses or credentials in non-test Python files."""
	# Skip test files
	if "test_" in os.path.basename(py_file):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	email_re = re.compile(r"""['"][a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}['"]""")
	# Allow lines that are simple constant definitions (e.g. _USER_A = "email@…")
	constant_def_re = re.compile(r"""^\s*[A-Z_][A-Z0-9_]*\s*=\s*['"]""")
	for lineno, line in enumerate(lines, 1):
		# Skip comment lines
		stripped = line.lstrip()
		if stripped.startswith("#"):
			continue
		# Skip constant definitions — these are the intentional named values
		if constant_def_re.match(line):
			continue
		if email_re.search(line):
			report.add(
				QCFinding(
					severity="high",
					rule_id="FS-006",
					file=rel,
					line=lineno,
					message="Hardcoded email address in non-test source file",
					suggestion="Extract to a named constant or configuration value",
				)
			)


def check_default_in_validate_not_before_insert(report: QCReport, py_file: str, base: str) -> None:
	"""FS-007: Default field values set in validate() but not in before_insert()."""
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	content = "".join(lines)

	# If file has before_insert, assume developer thought about it
	has_before_insert = "def before_insert" in content
	has_validate = "def validate" in content

	if not has_validate or has_before_insert:
		return

	# Heuristic: self.<field> = "<default_value>" inside validate
	default_in_validate = re.compile(
		r"def validate\s*\(self[^)]*\).*?(?=def |\Z)", re.DOTALL
	)
	match = default_in_validate.search(content)
	if not match:
		return

	validate_block = match.group(0)
	assignment_re = re.compile(r"self\.\w+\s*=\s*['\"](\w+)['\"]")
	assignments = assignment_re.findall(validate_block)
	if assignments:
		report.add(
			QCFinding(
				severity="medium",
				rule_id="FS-007",
				file=rel,
				line=None,
				message=f"Default value(s) for field(s) {assignments} set in validate() but no before_insert() found",
				suggestion=(
					"Move default assignments to before_insert() so they are "
					"committed on first save; keep validate() as defence-in-depth fallback"
				),
			)
		)


def check_broad_except(report: QCReport, py_file: str, base: str) -> None:
	"""FS-008: Broad 'except Exception: return []' that silences errors silently."""
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	in_except = False
	except_lineno = 0
	for lineno, line in enumerate(lines, 1):
		stripped = line.strip()
		if re.match(r"except\s+(Exception|BaseException)\s*:", stripped):
			in_except = True
			except_lineno = lineno
		elif in_except:
			if stripped and not stripped.startswith("#"):
				# Check if the only action is a return/pass without logging
				if re.match(r"(return \[\]|return None|return|pass)\s*$", stripped):
					report.add(
						QCFinding(
							severity="medium",
							rule_id="FS-008",
							file=rel,
							line=except_lineno,
							message="Broad except clause silently swallows all errors",
							suggestion=(
								"Log the exception before returning: "
								"frappe.log_error(title='…', message=frappe.get_traceback())"
							),
						)
					)
				in_except = False
			elif stripped:
				in_except = False


def check_missing_cross_site_lot_validation(report: QCReport, py_file: str, base: str) -> None:
	"""FS-009: DocType with a 'lot' field but no cross-site lot.site validation."""
	# Only check files inside doctype/ directories
	if "doctype" not in py_file:
		return
	# Skip lot.py itself
	if os.path.basename(py_file) == "lot.py":
		return

	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	content = "".join(lines)

	has_lot_field_access = bool(
		re.search(r"""self\.get\s*\(\s*['"]lot['"]\s*\)""", content)
		or re.search(r"""self\.lot\b""", content)
	)
	if not has_lot_field_access:
		return

	has_lot_site_check = bool(
		re.search(r"""frappe\.db\.get_value\s*\(\s*['"]Lot['"]""", content)
	)
	if not has_lot_site_check:
		report.add(
			QCFinding(
				severity="high",
				rule_id="FS-009",
				file=rel,
				line=None,
				message="DocType accesses self.lot but has no cross-site lot.site consistency check",
				suggestion=(
					"Add: lot_site = frappe.db.get_value('Lot', self.lot, 'site'); "
					"if lot_site and lot_site != self.site: frappe.throw(_('Lot site must match…'))"
				),
			)
		)


def check_ai_writes_frappe(report: QCReport, py_file: str, base: str) -> None:
	"""FS-010: AI module code calls Frappe write APIs (violates AI-is-assistive-only rule)."""
	# Only check files inside ai/ directory
	if "ai" + os.sep not in py_file and "/ai/" not in py_file:
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	forbidden = re.compile(
		r"""(frappe\.get_doc|frappe\.new_doc|\.save\s*\(|\.insert\s*\(|\.submit\s*\(|\.db\.set_value)"""
	)
	for lineno, line in enumerate(lines, 1):
		if forbidden.search(line):
			report.add(
				QCFinding(
					severity="critical",
					rule_id="FS-010",
					file=rel,
					line=lineno,
					message="AI module calls a Frappe write API — violates AI-is-assistive-only rule",
					suggestion=(
						"AI modules must be pure-Python with no Frappe imports. "
						"Move write operations to the API wrapper (api/ directory)."
					),
				)
			)


def check_perm_query_has_permission_parity(hooks_file: str, report: QCReport, base: str) -> None:
	"""FS-011: DocType registered in permission_query_conditions but not in has_permission (or vice-versa)."""
	if not os.path.exists(hooks_file):
		return
	content = "".join(_read_lines(hooks_file))
	rel = _rel(hooks_file, base)

	# Extract keys from permission_query_conditions dict (more precise block-based extraction below)
	# Check which dict each key belongs to
	pqc_block = re.search(
		r"permission_query_conditions\s*=\s*\{(.*?)\}",
		content,
		re.DOTALL,
	)
	hp_block = re.search(
		r"has_permission\s*=\s*\{(.*?)\}",
		content,
		re.DOTALL,
	)

	if not pqc_block or not hp_block:
		return

	pqc_doctypes = set(re.findall(r"""["']([^"']+)["']\s*:""", pqc_block.group(1)))
	hp_doctypes = set(re.findall(r"""["']([^"']+)["']\s*:""", hp_block.group(1)))

	only_pqc = pqc_doctypes - hp_doctypes
	only_hp = hp_doctypes - pqc_doctypes

	for dt in sorted(only_pqc):
		report.add(
			QCFinding(
				severity="critical",
				rule_id="FS-011",
				file=rel,
				line=None,
				message=f"DocType '{dt}' in permission_query_conditions but NOT in has_permission",
				suggestion=(
					"Register both permission_query_conditions AND has_permission for every "
					"site-isolated DocType (Non-Negotiable Rule #2)"
				),
			)
		)
	for dt in sorted(only_hp):
		report.add(
			QCFinding(
				severity="critical",
				rule_id="FS-011",
				file=rel,
				line=None,
				message=f"DocType '{dt}' in has_permission but NOT in permission_query_conditions",
				suggestion=(
					"Register both permission_query_conditions AND has_permission for every "
					"site-isolated DocType (Non-Negotiable Rule #2)"
				),
			)
		)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_qc(app_path: str) -> QCReport:
	"""Run all QC checks on the given app path and return a QCReport."""
	report = QCReport(app_path=app_path)
	base = app_path

	py_files = _iter_python_files(app_path)
	json_files = _iter_json_files(app_path)
	js_files = _iter_js_files(app_path)

	for py_file in py_files:
		check_missing_translations(report, py_file, base)
		check_hardcoded_emails(report, py_file, base)
		check_default_in_validate_not_before_insert(report, py_file, base)
		check_broad_except(report, py_file, base)
		check_missing_cross_site_lot_validation(report, py_file, base)
		check_ai_writes_frappe(report, py_file, base)

	for js_file in js_files:
		check_missing_js_translations(report, js_file, base)

	for json_file in json_files:
		check_doctype_json_site_required(report, json_file, base)
		check_doctype_json_title_field(report, json_file, base)
		check_doctype_json_track_changes(report, json_file, base)

	# Hooks-level parity check
	hooks_candidates = [
		os.path.join(app_path, "hooks.py"),
		os.path.join(app_path, "..", "hooks.py"),
	]
	for hf in hooks_candidates:
		if os.path.exists(hf):
			check_perm_query_has_permission_parity(hf, report, base)
			break

	# Sort: critical first, then high, medium, low
	order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
	report.findings.sort(key=lambda f: (order.get(f.severity, 99), f.file, f.line or 0))
	return report


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def print_text_report(report: QCReport) -> None:
	s = report.to_dict()["summary"]
	print(f"\n{'='*70}")
	print("  Frappe Skill QC Agent — Report")
	print(f"  App path : {report.app_path}")
	print(f"  Result   : {'✅ PASSED' if report.passed() else '❌ FAILED'}")
	print(
		f"  Findings : {s['total']} total  "
		f"(critical:{s['critical']}  high:{s['high']}  "
		f"medium:{s['medium']}  low:{s['low']})"
	)
	print(f"{'='*70}\n")

	if not report.findings:
		print("No issues found.\n")
		return

	for f in report.findings:
		loc = f"{f.file}:{f.line}" if f.line else f.file
		sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(f.severity, "⚪")
		print(f"{sev_icon} [{f.rule_id}] {f.severity.upper()}  {loc}")
		print(f"   {f.message}")
		print(f"   → {f.suggestion}")
		print()


def print_json_report(report: QCReport) -> None:
	print(json.dumps(report.to_dict(), indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
	import argparse

	parser = argparse.ArgumentParser(
		description="Frappe Skill QC Agent — automated code quality checks for Frappe apps",
		epilog="Exit code 0 = passed (no critical/high); 1 = failed.",
	)
	parser.add_argument(
		"--app-path",
		default=os.path.join(
			os.path.dirname(__file__),
			"..",
			"apps",
			"yam_agri_core",
			"yam_agri_core",
			"yam_agri_core",
		),
		help="Path to the inner yam_agri_core Python package (default: auto-detected)",
	)
	parser.add_argument(
		"--format",
		choices=["text", "json"],
		default="text",
		help="Output format (default: text)",
	)
	args = parser.parse_args()

	app_path = os.path.realpath(args.app_path)
	if not os.path.isdir(app_path):
		print(f"Error: app-path does not exist: {app_path}", file=sys.stderr)
		return 2

	report = run_qc(app_path)

	if args.format == "json":
		print_json_report(report)
	else:
		print_text_report(report)

	return 0 if report.passed() else 1


if __name__ == "__main__":
	sys.exit(main())
