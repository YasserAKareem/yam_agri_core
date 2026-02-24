"""Frappe Skill — Automated QC Agent for YAM Agri Core.

A pure-Python static analysis tool that checks a Frappe app directory for
bugs and deviations from Frappe best practices.  No live Frappe instance is
required; the agent operates on source files only.

Bug classification follows a 10-category, 3-level taxonomy:

  1. Functional   2. Logical      3. Performance  4. Compatibility
  5. Security     6. UI/UX        7. Integration  8. Syntax & Build
  9. Concurrency  10. Regression

Every finding is tagged with the relevant taxonomy code (e.g. "1.1.1"),
its predefined diagnostic message, and a multi-step planned response so
developers know exactly what to do.

Usage (from repo root):
    python tools/frappe_skill_agent.py
    python tools/frappe_skill_agent.py --app-path apps/yam_agri_core/yam_agri_core/yam_agri_core
    python tools/frappe_skill_agent.py --format json

Custom bug types can be registered at runtime:

    from tools.frappe_skill_agent import register_bug_type, BugDefinition
    register_bug_type(BugDefinition(
        code="11.1.1",
        category="Custom Frappe Bugs",
        subcategory="Workflow",
        bug_type="Missing workflow state guard",
        predefined_message="Workflow state transition lacks server-side guard",
        planned_response=[
            "Step 1: Identify the workflow states involved",
            "Step 2: Add frappe.has_role() check in controller validate()",
            "Step 3: Cover the guard with a unit test",
        ],
    ))

Exit codes: 0 = passed (no critical/high); 1 = failed; 2 = config error.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Bug taxonomy registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BugDefinition:
	"""A single entry in the universal bug taxonomy.

	code            -- hierarchical dot-code, e.g. "1.1.1"
	category        -- top-level name, e.g. "Functional Bugs"
	subcategory     -- second-level name, e.g. "Input Handling"
	bug_type        -- third-level name, e.g. "Missing required field validation"
	predefined_message -- short diagnostic template shown in the report
	planned_response   -- ordered list of remediation steps
	"""

	code: str
	category: str
	subcategory: str
	bug_type: str
	predefined_message: str
	planned_response: tuple[str, ...]


# The registry maps taxonomy code → BugDefinition.
# Additional types can be added via register_bug_type().
TAXONOMY: dict[str, BugDefinition] = {}


def _def(
	code: str,
	category: str,
	subcategory: str,
	bug_type: str,
	predefined_message: str,
	planned_response: list[str],
) -> None:
	"""Helper: create and insert a BugDefinition into TAXONOMY."""
	TAXONOMY[code] = BugDefinition(
		code=code,
		category=category,
		subcategory=subcategory,
		bug_type=bug_type,
		predefined_message=predefined_message,
		planned_response=tuple(planned_response),
	)


def register_bug_type(definition: BugDefinition) -> None:
	"""Register a custom bug type (allows extending the taxonomy at runtime).

	If a definition with the same code already exists it will be overwritten.
	"""
	TAXONOMY[definition.code] = definition


# ── 1. Functional Bugs ────────────────────────────────────────────────────
_def("1.1.1", "Functional Bugs", "Input Handling", "Missing required field validation",
	 "Required field '{field}' has no server-side or JSON-level validation guard",
	 ["Step 1: Add `reqd: 1` to the field definition in the DocType JSON",
	  "Step 2: Add a Python `validate()` check: if not self.get('{field}'): frappe.throw(_('…'))",
	  "Step 3: Run `bench migrate` so the DB constraint is updated",
	  "Step 4: Add a unit test that saves a record without the field and expects ValidationError"])

_def("1.1.2", "Functional Bugs", "Input Handling", "Incorrect default values",
	 "Field default is set in validate() instead of before_insert(), so it may not persist on programmatic inserts",
	 ["Step 1: Move the default assignment from validate() to before_insert()",
	  "Step 2: Keep a fallback assignment in validate() as defence-in-depth",
	  "Step 3: Verify with bench run-tests that the field is populated on new records"])

_def("1.1.3", "Functional Bugs", "Input Handling", "Case sensitivity issues",
	 "String comparison uses raw == instead of case-insensitive .lower() / .casefold()",
	 ["Step 1: Normalise both sides with .lower() before comparison",
	  "Step 2: Update any related DB queries to use COLLATE or frappe.db filters",
	  "Step 3: Add test cases for upper-case and mixed-case inputs"])

_def("1.1.4", "Functional Bugs", "Input Handling", "Special character mishandling",
	 "Field value is used in a context that does not escape special characters",
	 ["Step 1: Use frappe.db.escape() for any value inserted into a query string",
	  "Step 2: Use frappe.utils.sanitize_html() for user-supplied HTML content",
	  "Step 3: Add test cases with apostrophes, quotes, and angle brackets"])

_def("1.1.5", "Functional Bugs", "Input Handling", "Null/empty input crashes",
	 "Code dereferences a value that may be None/empty without a guard",
	 ["Step 1: Add `if not value: return` guard before dereferencing",
	  "Step 2: Use `(self.get('field') or '').strip()` pattern",
	  "Step 3: Add a test that saves a record with each nullable field empty"])

_def("1.2.5", "Functional Bugs", "Workflow Errors", "Duplicate record creation",
	 "Record creation path lacks an idempotency check, risking duplicates",
	 ["Step 1: Add frappe.db.exists() check before frappe.get_doc().insert()",
	  "Step 2: Use a unique naming_series or unique constraint on the key field",
	  "Step 3: Wrap the insert in a try/except frappe.DuplicateEntryError block"])

_def("1.3.1", "Functional Bugs", "Feature Failures", "Search returning no results",
	 "Global search DocType registration or title_field missing, so records are not indexed",
	 ["Step 1: Add the DocType to global_search_doctypes in hooks.py",
	  "Step 2: Set title_field on the DocType JSON to the most human-readable field",
	  "Step 3: Run `bench build-search-index` to re-index existing records"])

# ── 2. Logical Bugs ───────────────────────────────────────────────────────
_def("2.1.5", "Logical Bugs", "Algorithm Errors", "Faulty recommendation logic",
	 "Recommendation score or ranking algorithm produces incorrect ordering",
	 ["Step 1: Write unit tests with known inputs and expected output rankings",
	  "Step 2: Review score formula for sign errors or missing factors",
	  "Step 3: Add a regression test that pins the expected top recommendation"])

_def("2.2.1", "Logical Bugs", "Conditional Logic", "Misplaced if/else",
	 "An if/else branch is logically inverted or unreachable",
	 ["Step 1: Trace the condition with True/False examples on paper",
	  "Step 2: Add a unit test for each branch",
	  "Step 3: Refactor to a guard-clause pattern for clarity"])

_def("2.2.4", "Logical Bugs", "Conditional Logic", "Missing default cases",
	 "A broad except clause catches all errors without logging, hiding failures",
	 ["Step 1: Replace bare `except Exception: return []` with logged handling",
	  "Step 2: Add `frappe.log_error(title='…', message=frappe.get_traceback())`",
	  "Step 3: Narrow the exception type if possible (e.g. frappe.DoesNotExistError)"])

_def("2.3.3", "Logical Bugs", "State Management", "Incorrect flag toggling",
	 "A boolean flag or DocType field that records state changes is not enabled",
	 ["Step 1: Add `track_changes: 1` to the DocType JSON",
	  "Step 2: Run `bench migrate` to activate change tracking in the DB",
	  "Step 3: Verify the Version log is populated after editing a record"])

# ── 3. Performance Bugs ───────────────────────────────────────────────────
_def("3.1.3", "Performance Bugs", "Speed Issues", "Excessive API calls",
	 "Code makes N+1 DB calls inside a loop instead of a single bulk fetch",
	 ["Step 1: Extract the loop body DB call to a single frappe.get_all() before the loop",
	  "Step 2: Build a lookup dict keyed by record name",
	  "Step 3: Profile with frappe.utils.perf.get_performance_log() to confirm improvement"])

_def("3.1.4", "Performance Bugs", "Speed Issues", "Unindexed DB queries",
	 "A frequently-filtered field has no database index defined",
	 ["Step 1: Add `search_index: 1` to the field definition in the DocType JSON",
	  "Step 2: Run `bench migrate` to create the index",
	  "Step 3: Verify with EXPLAIN SELECT that the index is used"])

# ── 4. Compatibility Bugs ─────────────────────────────────────────────────
_def("4.3.2", "Compatibility Bugs", "Versioning", "Deprecated library usage",
	 "Code uses a Frappe internal API that is deprecated or removed in the target version",
	 ["Step 1: Check frappe/CHANGELOG.md for the deprecated API",
	  "Step 2: Replace with the documented replacement",
	  "Step 3: Add a CI check that imports the module with the target Frappe version"])

# ── 5. Security Bugs ──────────────────────────────────────────────────────
_def("5.1.3", "Security Bugs", "Authentication", "Token leakage",
	 "A secret, token, or credential is hard-coded in source rather than read from config",
	 ["Step 1: Remove the credential from source immediately",
	  "Step 2: Rotate the leaked credential",
	  "Step 3: Store it in frappe.conf or os.environ; never in .py or .json files",
	  "Step 4: Add a secret-scan CI step (already in ci.yml)"])

_def("5.2.2", "Security Bugs", "Authorization", "Privilege escalation",
	 "An AI or background module calls a Frappe write API directly, bypassing authorization",
	 ["Step 1: Remove all frappe.get_doc/save/insert/submit calls from the ai/ module",
	  "Step 2: Move write operations to the api/ wrapper behind @frappe.whitelist()",
	  "Step 3: Add assert_site_access() in the API wrapper before any write",
	  "Step 4: Confirm AI module imports do not include `frappe`"])

_def("5.2.3", "Security Bugs", "Authorization", "Broken access control",
	 "A DocType with site isolation is missing permission_query_conditions or has_permission registration",
	 ["Step 1: Add the DocType to permission_query_conditions in hooks.py",
	  "Step 2: Add the DocType to has_permission in hooks.py",
	  "Step 3: Implement query-condition and has-permission functions in site_permissions.py",
	  "Step 4: Write an AT-10 style test that confirms cross-site records are not visible"])

_def("5.2.4", "Security Bugs", "Authorization", "Insecure direct object reference (IDOR)",
	 "A DocType linked to a Lot allows cross-site access because lot.site is not validated",
	 ["Step 1: Add lot_site = frappe.db.get_value('Lot', self.lot, 'site') in validate()",
	  "Step 2: Throw ValidationError if lot_site != self.site",
	  "Step 3: Add a unit test that attempts to create a cross-site linked record"])

_def("5.3.3", "Security Bugs", "Data Protection", "Insecure storage",
	 "Sensitive value (email, credential) is hard-coded inline instead of extracted to a constant or config",
	 ["Step 1: Extract the value to a named module-level constant (e.g. _USER_A = '…')",
	  "Step 2: For production secrets use frappe.conf.get() or os.environ.get()",
	  "Step 3: Review all non-test Python files for remaining inline credentials"])

# ── 6. UI/UX Bugs ─────────────────────────────────────────────────────────
_def("6.3.1", "UI/UX Bugs", "Interaction", "Unclear error messages",
	 "A user-facing error string is not wrapped in _() / __() and will not be translated",
	 ["Step 1: Add `from frappe import _` to the Python file if missing",
	  "Step 2: Wrap: frappe.throw(_('message'), ExcType)",
	  "Step 3: For JavaScript use __('message') in frappe.msgprint / frappe.confirm",
	  "Step 4: Run `bench update-translations` and verify ar.csv is updated"])

_def("6.1.4", "UI/UX Bugs", "Layout", "Non-responsive design",
	 "DocType is missing title_field, making records unidentifiable in link dropdowns",
	 ["Step 1: Add `title_field` to the DocType JSON pointing to the best human-readable field",
	  "Step 2: Run `bench migrate`",
	  "Step 3: Open a Link field that references this DocType and verify the label is readable"])

# ── 8. Syntax & Build Bugs ────────────────────────────────────────────────
_def("8.2.1", "Syntax & Build Bugs", "Runtime", "Null pointer exceptions",
	 "Code calls a method or accesses an attribute on a value that could be None",
	 ["Step 1: Add `if not value: return/raise` guard before using the value",
	  "Step 2: Use `getattr(obj, 'attr', None)` instead of direct attribute access",
	  "Step 3: Add a unit test that passes None for the nullable argument"])

# ── 10. Regression Bugs ───────────────────────────────────────────────────
_def("10.1.1", "Regression Bugs", "Feature Breakage", "Login system failure",
	 "Permission hook is registered for one dict (PQC) but missing from the other (has_permission), risking access regression",
	 ["Step 1: Diff permission_query_conditions and has_permission keys in hooks.py",
	  "Step 2: Add any missing DocType to the hook that lacks it",
	  "Step 3: Run AT-10 automated check to confirm both hooks fire correctly"])


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class QCFinding:
	"""A single issue found by the QC agent.

	severity      -- "critical" | "high" | "medium" | "low"
	rule_id       -- Frappe Skill rule, e.g. "FS-001"
	bug_code      -- taxonomy code, e.g. "6.3.1"
	category      -- top-level taxonomy category, e.g. "UI/UX Bugs"
	subcategory   -- second-level, e.g. "Interaction"
	bug_type      -- third-level, e.g. "Unclear error messages"
	file          -- relative path to source file
	line          -- line number (None for whole-file findings)
	message       -- specific diagnostic message for this occurrence
	planned_response -- ordered list of remediation steps
	"""

	severity: str
	rule_id: str
	bug_code: str
	category: str
	subcategory: str
	bug_type: str
	file: str
	line: int | None
	message: str
	planned_response: tuple[str, ...]


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
					"bug_code": f.bug_code,
					"category": f.category,
					"subcategory": f.subcategory,
					"bug_type": f.bug_type,
					"file": f.file,
					"line": f.line,
					"message": f.message,
					"planned_response": list(f.planned_response),
				}
				for f in self.findings
			],
		}


# ---------------------------------------------------------------------------
# Internal factory helper
# ---------------------------------------------------------------------------


def _finding(
	*,
	severity: str,
	rule_id: str,
	bug_code: str,
	file: str,
	line: int | None,
	message: str,
	planned_response: list[str] | None = None,
) -> QCFinding:
	"""Create a QCFinding, pulling taxonomy metadata from TAXONOMY registry."""
	defn = TAXONOMY.get(bug_code)
	if defn is None:
		category = "Unknown"
		subcategory = "Unknown"
		bug_type = "Unknown"
		default_plan: tuple[str, ...] = (
			"Step 1: Investigate the finding and identify the root cause.",
			"Step 2: Apply the appropriate fix and add a regression test.",
		)
	else:
		category = defn.category
		subcategory = defn.subcategory
		bug_type = defn.bug_type
		default_plan = defn.planned_response

	return QCFinding(
		severity=severity,
		rule_id=rule_id,
		bug_code=bug_code,
		category=category,
		subcategory=subcategory,
		bug_type=bug_type,
		file=file,
		line=line,
		message=message,
		planned_response=tuple(planned_response) if planned_response is not None else default_plan,
	)


# ---------------------------------------------------------------------------
# File helpers
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
# Rule checks — each maps to a taxonomy code
# ---------------------------------------------------------------------------


def check_missing_translations(report: QCReport, py_file: str, base: str) -> None:
	"""FS-001 / 6.3.1: frappe.throw() called with a raw string not wrapped in _()."""
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	pattern = re.compile(
		r"""frappe\.throw\s*\(\s*(?!_\s*\(|frappe\._\s*\()(?:f?['"])""",
	)
	for lineno, line in enumerate(lines, 1):
		if pattern.search(line):
			report.add(_finding(
				severity="critical",
				rule_id="FS-001",
				bug_code="6.3.1",
				file=rel,
				line=lineno,
				message=(
					"frappe.throw() uses a raw string — not translatable. "
					"Arabic/RTL users will see English error text."
				),
			))


def check_missing_js_translations(report: QCReport, js_file: str, base: str) -> None:
	"""FS-002 / 6.3.1: User-visible JS string not wrapped in __()."""
	lines = _read_lines(js_file)
	rel = _rel(js_file, base)
	patterns = [
		re.compile(r"""frappe\.msgprint\s*\(\s*['"]"""),
		re.compile(r"""frappe\.confirm\s*\(\s*['"]"""),
		re.compile(r"""frappe\.show_alert\s*\(\s*\{[^}]*message\s*:\s*['"]"""),
	]
	for lineno, line in enumerate(lines, 1):
		for p in patterns:
			if p.search(line):
				report.add(_finding(
					severity="high",
					rule_id="FS-002",
					bug_code="6.3.1",
					file=rel,
					line=lineno,
					message=(
						"User-facing JavaScript string not wrapped in __(). "
						"The string will not be translated for Arabic users."
					),
					planned_response=[
						"Step 1: Wrap the string: __('message')",
						"Step 2: Run `bench update-translations` to export the new string",
						"Step 3: Add the Arabic translation to translations/ar.csv",
					],
				))
				break


def check_doctype_json_site_required(report: QCReport, json_file: str, base: str) -> None:
	"""FS-003 / 1.1.1: DocType JSON — site field not marked reqd:1."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	rel = _rel(json_file, base)
	fields = {f.get("fieldname"): f for f in data.get("fields", [])}
	dt_name = data.get("name", json_file)
	if "site" in fields and not fields["site"].get("reqd"):
		report.add(_finding(
			severity="medium",
			rule_id="FS-003",
			bug_code="1.1.1",
			file=rel,
			line=None,
			message=(
				f"DocType '{dt_name}': 'site' field is not marked reqd:1. "
				"The form will not show a required asterisk and client-side "
				"validation will not block save before the server is reached."
			),
		))


def check_doctype_json_title_field(report: QCReport, json_file: str, base: str) -> None:
	"""FS-004 / 6.1.4: DocType JSON — missing title_field."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	if not data.get("fields"):
		return
	rel = _rel(json_file, base)
	dt_name = data.get("name", json_file)
	if not data.get("title_field"):
		report.add(_finding(
			severity="low",
			rule_id="FS-004",
			bug_code="6.1.4",
			file=rel,
			line=None,
			message=(
				f"DocType '{dt_name}': missing 'title_field'. "
				"Link dropdowns will show the auto-generated series name "
				"instead of a human-readable label."
			),
		))


def check_doctype_json_track_changes(report: QCReport, json_file: str, base: str) -> None:
	"""FS-005 / 2.3.3: DocType JSON — missing track_changes on transaction doctypes."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	field_names = {f.get("fieldname") for f in data.get("fields", [])}
	if "naming_series" not in field_names:
		return
	rel = _rel(json_file, base)
	dt_name = data.get("name", json_file)
	if not data.get("track_changes"):
		report.add(_finding(
			severity="medium",
			rule_id="FS-005",
			bug_code="2.3.3",
			file=rel,
			line=None,
			message=(
				f"DocType '{dt_name}': track_changes not enabled. "
				"Field-level changes will not be journalled — this is a "
				"HACCP/ISO 22000 audit trail requirement."
			),
		))


def check_hardcoded_emails(report: QCReport, py_file: str, base: str) -> None:
	"""FS-006 / 5.3.3: Hardcoded email / credential in non-test Python file."""
	if "test_" in os.path.basename(py_file):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	email_re = re.compile(r"""['"][a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}['"]""")
	constant_def_re = re.compile(r"""^\s*[A-Z_][A-Z0-9_]*\s*=\s*['"]""")
	for lineno, line in enumerate(lines, 1):
		stripped = line.lstrip()
		if stripped.startswith("#"):
			continue
		if constant_def_re.match(line):
			continue
		if email_re.search(line):
			report.add(_finding(
				severity="high",
				rule_id="FS-006",
				bug_code="5.3.3",
				file=rel,
				line=lineno,
				message=(
					"Hardcoded email address in non-test source. "
					"If the address needs to change, every occurrence must be "
					"updated manually — error-prone and hard to audit."
				),
			))


def check_default_in_validate_not_before_insert(report: QCReport, py_file: str, base: str) -> None:
	"""FS-007 / 1.1.2: Default values set in validate() but not before_insert()."""
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	content = "".join(lines)
	has_before_insert = "def before_insert" in content
	has_validate = "def validate" in content
	if not has_validate or has_before_insert:
		return
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
		report.add(_finding(
			severity="medium",
			rule_id="FS-007",
			bug_code="1.1.2",
			file=rel,
			line=None,
			message=(
				f"Field(s) {assignments} receive default values in validate() "
				"but there is no before_insert(). Programmatic inserts that "
				"skip validate() will save blank values to the DB."
			),
		))


def check_broad_except(report: QCReport, py_file: str, base: str) -> None:
	"""FS-008 / 2.2.4: Broad except clause that silently swallows errors."""
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
				if re.match(r"(return \[\]|return None|return|pass)\s*$", stripped):
					report.add(_finding(
						severity="medium",
						rule_id="FS-008",
						bug_code="2.2.4",
						file=rel,
						line=except_lineno,
						message=(
							"Broad 'except Exception' swallows all errors silently. "
							"DB connection failures, permission errors, and bugs will "
							"be hidden and produce incorrect empty results."
						),
					))
				in_except = False
			elif stripped:
				in_except = False


def check_missing_cross_site_lot_validation(report: QCReport, py_file: str, base: str) -> None:
	"""FS-009 / 5.2.4: DocType with lot field but no cross-site lot.site check."""
	if "doctype" not in py_file:
		return
	if os.path.basename(py_file) == "lot.py":
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	content = "".join(lines)
	has_lot = bool(
		re.search(r"""self\.get\s*\(\s*['"]lot['"]\s*\)""", content)
		or re.search(r"""self\.lot\b""", content)
	)
	if not has_lot:
		return
	has_check = bool(re.search(r"""frappe\.db\.get_value\s*\(\s*['"]Lot['"]""", content))
	if not has_check:
		report.add(_finding(
			severity="high",
			rule_id="FS-009",
			bug_code="5.2.4",
			file=rel,
			line=None,
			message=(
				"DocType accesses self.lot but has no cross-site lot.site "
				"consistency check. A record from Site A can be linked to a "
				"Lot from Site B, breaking data isolation."
			),
		))


def check_ai_writes_frappe(report: QCReport, py_file: str, base: str) -> None:
	"""FS-010 / 5.2.2: AI module calls Frappe write API."""
	if "ai" + os.sep not in py_file and "/ai/" not in py_file:
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	forbidden = re.compile(
		r"""(frappe\.get_doc|frappe\.new_doc|\.save\s*\(|\.insert\s*\(|\.submit\s*\(|\.db\.set_value)"""
	)
	for lineno, line in enumerate(lines, 1):
		if forbidden.search(line):
			report.add(_finding(
				severity="critical",
				rule_id="FS-010",
				bug_code="5.2.2",
				file=rel,
				line=lineno,
				message=(
					"AI module calls a Frappe write API. This violates the "
					"AI-is-assistive-only rule and can cause autonomous DB "
					"writes that bypass authorization checks."
				),
			))


def check_perm_query_has_permission_parity(hooks_file: str, report: QCReport, base: str) -> None:
	"""FS-011 / 5.2.3 + 10.1.1: PQC/has_permission registry out of sync."""
	if not os.path.exists(hooks_file):
		return
	content = "".join(_read_lines(hooks_file))
	rel = _rel(hooks_file, base)
	pqc_block = re.search(r"permission_query_conditions\s*=\s*\{(.*?)\}", content, re.DOTALL)
	hp_block = re.search(r"has_permission\s*=\s*\{(.*?)\}", content, re.DOTALL)
	if not pqc_block or not hp_block:
		return
	pqc_doctypes = set(re.findall(r"""["']([^"']+)["']\s*:""", pqc_block.group(1)))
	hp_doctypes = set(re.findall(r"""["']([^"']+)["']\s*:""", hp_block.group(1)))
	for dt in sorted(pqc_doctypes - hp_doctypes):
		report.add(_finding(
			severity="critical",
			rule_id="FS-011",
			bug_code="5.2.3",
			file=rel,
			line=None,
			message=(
				f"DocType '{dt}' is in permission_query_conditions but NOT "
				"in has_permission. List-view isolation works but a direct "
				"document GET by name will bypass site isolation."
			),
		))
	for dt in sorted(hp_doctypes - pqc_doctypes):
		report.add(_finding(
			severity="critical",
			rule_id="FS-011",
			bug_code="10.1.1",
			file=rel,
			line=None,
			message=(
				f"DocType '{dt}' is in has_permission but NOT in "
				"permission_query_conditions. Direct-read isolation works but "
				"list-view queries will return all records regardless of site."
			),
		))


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

	hooks_candidates = [
		os.path.join(app_path, "hooks.py"),
		os.path.join(app_path, "..", "hooks.py"),
	]
	for hf in hooks_candidates:
		if os.path.exists(hf):
			check_perm_query_has_permission_parity(hf, report, base)
			break

	order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
	report.findings.sort(key=lambda f: (order.get(f.severity, 99), f.file, f.line or 0))
	return report


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def print_text_report(report: QCReport, *, verbose: bool = False) -> None:
	s = report.to_dict()["summary"]
	print(f"\n{'='*72}")
	print("  Frappe Skill QC Agent — Report")
	print(f"  App path : {report.app_path}")
	print(f"  Result   : {'✅ PASSED' if report.passed() else '❌ FAILED'}")
	print(
		f"  Findings : {s['total']} total  "
		f"(critical:{s['critical']}  high:{s['high']}  "
		f"medium:{s['medium']}  low:{s['low']})"
	)
	print(f"{'='*72}\n")

	if not report.findings:
		print("No issues found.\n")
		return

	for f in report.findings:
		loc = f"{f.file}:{f.line}" if f.line else f.file
		sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(f.severity, "⚪")
		print(f"{sev_icon} [{f.rule_id} / {f.bug_code}] {f.severity.upper()}  {loc}")
		print(f"   Classification : {f.category} › {f.subcategory} › {f.bug_type}")
		print(f"   Finding        : {f.message}")
		if verbose or f.severity in ("critical", "high"):
			print("   📋 Planned Response:")
			for step in f.planned_response:
				print(f"      {step}")
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
		epilog="Exit code 0 = passed (no critical/high); 1 = failed; 2 = config error.",
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
	parser.add_argument(
		"--verbose",
		action="store_true",
		help="Show planned response steps for every finding (default: only for critical/high)",
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
		print_text_report(report, verbose=args.verbose)

	return 0 if report.passed() else 1


if __name__ == "__main__":
	sys.exit(main())
