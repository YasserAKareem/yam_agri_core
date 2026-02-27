"""Frappe Skill — Automated QC Agent for YAM Agri Core.

A pure-Python static analysis tool that checks a Frappe app directory for
bugs and deviations from Frappe best practices.  No live Frappe instance is
required; the agent operates on source files only.

Bug classification follows a 12-category, 3-level taxonomy:

  1. Functional   2. Logical      3. Performance  4. Compatibility
  5. Security     6. UI/UX        7. Integration  8. Syntax & Build
  9. Concurrency  10. Regression  11. Hardcoded   12. Master Data

Every finding is tagged with the relevant taxonomy code (e.g. "1.1.1"),
its predefined diagnostic message, and a multi-step planned response so
developers know exactly what to do.

Usage (from repo root):
    python tools/frappe_skill_agent.py
    python tools/frappe_skill_agent.py --app-path apps/yam_agri_core/yam_agri_core/yam_agri_core
    python tools/frappe_skill_agent.py --format json
    python tools/frappe_skill_agent.py --save-learned learned.json
    python tools/frappe_skill_agent.py --load-taxonomy custom_taxonomy.json

Custom bug types can be registered at runtime:

    from tools.frappe_skill_agent import register_bug_type, BugDefinition
    register_bug_type(BugDefinition(
        code="11.4.1",
        category="Hardcoded Bugs",
        subcategory="Hardcoded Business Logic",
        bug_type="Hardcoded timeout values",
        predefined_message="Timeout value is hardcoded instead of read from config",
        planned_response=[
            "Step 1: Identify all hardcoded timeout constants",
            "Step 2: Move them to frappe.conf or a settings DocType",
            "Step 3: Update callers to read from config",
        ],
    ))

Auto-learning: the agent discovers suspicious patterns that do not match any
existing rule and proposes new BugDefinitions.  Use --save-learned to persist
these proposals and --load-taxonomy to load them on the next run.

Exit codes: 0 = passed (no critical/high); 1 = failed; 2 = config error.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
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

	Training-data fields (v4 — required for 100% agent training coverage):
	cwe_id           -- CWE identifier, e.g. "CWE-259" (empty = not applicable)
	cwe_name         -- Human-readable CWE name
	negative_example -- Minimal buggy code snippet (the "before" in the pair)
	positive_example -- Minimal fixed code snippet (the "after" in the pair)
	telemetry_signatures -- Log / trace patterns that signal this bug at runtime
	ast_diff         -- Readable description of the AST-level structural change
	"""

	code: str
	category: str
	subcategory: str
	bug_type: str
	predefined_message: str
	planned_response: tuple[str, ...]
	# ── Training-data fields ──────────────────────────────────────────────
	cwe_id: str = ""
	cwe_name: str = ""
	negative_example: str = ""
	positive_example: str = ""
	telemetry_signatures: tuple[str, ...] = ()
	ast_diff: str = ""


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
	"""Helper: create and insert a BugDefinition into TAXONOMY (no training data).

	Prefer _td() for new entries so that training coverage is 100%.
	"""
	TAXONOMY[code] = BugDefinition(
		code=code,
		category=category,
		subcategory=subcategory,
		bug_type=bug_type,
		predefined_message=predefined_message,
		planned_response=tuple(planned_response),
	)


def _td(
	code: str,
	category: str,
	subcategory: str,
	bug_type: str,
	predefined_message: str,
	planned_response: list[str],
	*,
	cwe_id: str = "",
	cwe_name: str = "",
	negative_example: str = "",
	positive_example: str = "",
	telemetry_signatures: list[str] | None = None,
	ast_diff: str = "",
) -> None:
	"""Helper: create a fully-specified BugDefinition with training data and register it.

	All keyword arguments contribute to the training coverage score (0.0 - 1.0).
	A score of 1.0 is required for the agent to learn the pattern correctly.
	"""
	TAXONOMY[code] = BugDefinition(
		code=code,
		category=category,
		subcategory=subcategory,
		bug_type=bug_type,
		predefined_message=predefined_message,
		planned_response=tuple(planned_response),
		cwe_id=cwe_id,
		cwe_name=cwe_name,
		negative_example=negative_example,
		positive_example=positive_example,
		telemetry_signatures=tuple(telemetry_signatures) if telemetry_signatures else (),
		ast_diff=ast_diff,
	)


def register_bug_type(definition: BugDefinition) -> None:
	"""Register a custom bug type (allows extending the taxonomy at runtime).

	If a definition with the same code already exists it will be overwritten.
	"""
	TAXONOMY[definition.code] = definition


def _compute_coverage(defn: BugDefinition) -> float:
	"""Return a 0.0-1.0 training-coverage score for a BugDefinition.

	Each of the six training-data fields contributes 1/6 of the score.
	A score of 1.0 means all six fields are populated (100% coverage).
	"""
	fields = [
		bool(defn.cwe_id),
		bool(defn.negative_example),
		bool(defn.positive_example),
		bool(defn.telemetry_signatures),
		bool(defn.ast_diff),
		bool(defn.planned_response),
	]
	return round(sum(fields) / len(fields), 2)


def coverage_stats(taxonomy: dict[str, BugDefinition] | None = None) -> dict:
	"""Return aggregate training-coverage statistics for the given taxonomy.

	Returns a dict with keys:
	  total          -- total bug definitions
	  full_coverage  -- count with score == 1.0
	  coverage_pct   -- percentage with full coverage (0-100)
	  avg_score      -- mean coverage score across all definitions
	"""
	if taxonomy is None:
		taxonomy = TAXONOMY
	if not taxonomy:
		return {"total": 0, "full_coverage": 0, "coverage_pct": 0.0, "avg_score": 0.0}
	scores = [_compute_coverage(d) for d in taxonomy.values()]
	full = sum(1 for s in scores if s == 1.0)
	return {
		"total": len(scores),
		"full_coverage": full,
		"coverage_pct": round(full / len(scores) * 100, 1),
		"avg_score": round(sum(scores) / len(scores), 3),
	}


# ── 1. Functional Bugs ────────────────────────────────────────────────────
_td(
	"1.1.1",
	"Functional Bugs",
	"Input Handling",
	"Missing required field validation",
	"Required field '{field}' has no server-side or JSON-level validation guard",
	[
		"Step 1: Add `reqd: 1` to the field definition in the DocType JSON",
		"Step 2: Add a Python `validate()` check: if not self.get('{field}'): frappe.throw(_('…'))",
		"Step 3: Run `bench migrate` so the DB constraint is updated",
		"Step 4: Add a unit test that saves a record without the field and expects ValidationError",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example=("class Lot(Document):\n    def validate(self):\n        pass  # no site check"),
	positive_example=(
		"class Lot(Document):\n"
		"    def validate(self):\n"
		"        if not self.get('site'):\n"
		"            frappe.throw(_('Every record must belong to a Site'), frappe.ValidationError)"
	),
	telemetry_signatures=[
		"ValidationError: site is mandatory for DocType Lot",
		"IntegrityError: Column 'site' cannot be null",
	],
	ast_diff=(
		"Add Stmt[If(not self.get('site'))] → Stmt[Call[frappe.throw](...)] inside FunctionDef[validate]"
	),
)

_td(
	"1.1.2",
	"Functional Bugs",
	"Input Handling",
	"Incorrect default values",
	"Field default is set in validate() instead of before_insert(), so it may not persist on programmatic inserts",
	[
		"Step 1: Move the default assignment from validate() to before_insert()",
		"Step 2: Keep a fallback assignment in validate() as defence-in-depth",
		"Step 3: Verify with bench run-tests that the field is populated on new records",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example=(
		"def validate(self):\n"
		"    if not self.status:\n"
		"        self.status = 'Open'  # skipped on programmatic insert"
	),
	positive_example=(
		"def before_insert(self):\n"
		"    if not self.get('status'):\n"
		"        self.status = 'Open'\n\n"
		"def validate(self):\n"
		"    if not self.get('status'):\n"
		"        self.status = 'Open'  # defence-in-depth fallback"
	),
	telemetry_signatures=[
		"AttributeError: 'NoneType' object has no attribute 'upper' on self.status",
		"INSERT INTO tabNonconformance ... status=NULL",
	],
	ast_diff=("Move Assign[self.status='Open'] from FunctionDef[validate] to new FunctionDef[before_insert]"),
)

_td(
	"1.1.3",
	"Functional Bugs",
	"Input Handling",
	"Case sensitivity issues",
	"String comparison uses raw == instead of case-insensitive .lower() / .casefold()",
	[
		"Step 1: Normalise both sides with .lower() before comparison",
		"Step 2: Update any related DB queries to use COLLATE or frappe.db filters",
		"Step 3: Add test cases for upper-case and mixed-case inputs",
	],
	cwe_id="CWE-178",
	cwe_name="Improper Handling of Case Sensitivity",
	negative_example="if crop_name == 'Wheat':  # fails for 'wheat' or 'WHEAT'",
	positive_example="if crop_name.lower() == 'wheat':  # case-insensitive",
	telemetry_signatures=[
		"Crop 'wheat' not found — check suggests 'Wheat' exists (case mismatch)",
		"KeyError: 'WHEAT' not in crop registry",
	],
	ast_diff=("Replace Compare[Name == Constant] with Compare[Call[.lower](Name) == Constant(.lower())]"),
)

_td(
	"1.1.4",
	"Functional Bugs",
	"Input Handling",
	"Special character mishandling",
	"Field value is used in a context that does not escape special characters",
	[
		"Step 1: Use frappe.db.escape() for any value inserted into a query string",
		"Step 2: Use frappe.utils.sanitize_html() for user-supplied HTML content",
		"Step 3: Add test cases with apostrophes, quotes, and angle brackets",
	],
	cwe_id="CWE-116",
	cwe_name="Improper Encoding or Escaping of Output",
	negative_example=("# SQL injection risk\nfrappe.db.sql(f\"SELECT * FROM tabLot WHERE name='{name}'\")"),
	positive_example=("# Safe parameterised ORM call\nfrappe.get_all('Lot', filters={'name': name})"),
	telemetry_signatures=[
		"ProgrammingError: You have an error in your SQL syntax near '''",
		"mariadb.OperationalError: Unmatched quotes in query",
	],
	ast_diff=(
		"Replace Call[frappe.db.sql](JoinedStr[f-string]) with Call[frappe.get_all](Constant, Dict[filters])"
	),
)

_td(
	"1.1.5",
	"Functional Bugs",
	"Input Handling",
	"Null/empty input crashes",
	"Code dereferences a value that may be None/empty without a guard",
	[
		"Step 1: Add `if not value: return` guard before dereferencing",
		"Step 2: Use `(self.get('field') or '').strip()` pattern",
		"Step 3: Add a test that saves a record with each nullable field empty",
	],
	cwe_id="CWE-476",
	cwe_name="NULL Pointer Dereference",
	negative_example="return self.site.upper()  # AttributeError if site is None",
	positive_example="return (self.get('site') or '').upper()",
	telemetry_signatures=[
		"AttributeError: 'NoneType' object has no attribute 'upper'",
		"TypeError: argument of type 'NoneType' is not iterable",
	],
	ast_diff=(
		"Wrap Attribute[.upper()] access in BoolOp[or Constant('')] "
		"to guard against None: (expr or '').upper()"
	),
)

_td(
	"1.2.5",
	"Functional Bugs",
	"Workflow Errors",
	"Duplicate record creation",
	"Record creation path lacks an idempotency check, risking duplicates",
	[
		"Step 1: Add frappe.db.exists() check before frappe.get_doc().insert()",
		"Step 2: Use a unique naming_series or unique constraint on the key field",
		"Step 3: Wrap the insert in a try/except frappe.DuplicateEntryError block",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example=(
		"doc = frappe.get_doc({'doctype': 'Lot', 'lot_number': lot_no})\ndoc.insert()  # no duplicate check"
	),
	positive_example=(
		"if not frappe.db.exists('Lot', {'lot_number': lot_no}):\n"
		"    doc = frappe.get_doc({'doctype': 'Lot', 'lot_number': lot_no})\n"
		"    doc.insert()\n"
		"else:\n"
		"    frappe.throw(_('Lot {0} already exists').format(lot_no))"
	),
	telemetry_signatures=[
		"UniqueConstraintError: Duplicate entry for lot_number",
		"IntegrityError: Duplicate entry 'YAM-LOT-2024-00001'",
	],
	ast_diff=("Wrap Call[frappe.get_doc().insert()] in If[Call[frappe.db.exists](...)]"),
)

_td(
	"1.3.1",
	"Functional Bugs",
	"Feature Failures",
	"Search returning no results",
	"Global search DocType registration or title_field missing, so records are not indexed",
	[
		"Step 1: Add the DocType to global_search_doctypes in hooks.py",
		"Step 2: Set title_field on the DocType JSON to the most human-readable field",
		"Step 3: Run `bench build-search-index` to re-index existing records",
	],
	cwe_id="N/A",
	cwe_name="Not applicable (UX/configuration issue)",
	negative_example=(
		"# hooks.py — Lot is NOT in global_search_doctypes\nglobal_search_doctypes = {'Default': []}"
	),
	positive_example=(
		"# hooks.py\nglobal_search_doctypes = {'Default': [{'doctype': 'Lot'}, {'doctype': 'Site'}]}"
	),
	telemetry_signatures=[
		"GlobalSearch returned 0 results for existing Lot name",
		"build-search-index: skipping DocType Lot — no title_field",
	],
	ast_diff=("Extend List[global_search_doctypes['Default']] with Dict{'doctype': 'Lot'}"),
)

# ── 2. Logical Bugs ───────────────────────────────────────────────────────
_td(
	"2.1.5",
	"Logical Bugs",
	"Algorithm Errors",
	"Faulty recommendation logic",
	"Recommendation score or ranking algorithm produces incorrect ordering",
	[
		"Step 1: Write unit tests with known inputs and expected output rankings",
		"Step 2: Review score formula for sign errors or missing factors",
		"Step 3: Add a regression test that pins the expected top recommendation",
	],
	cwe_id="CWE-682",
	cwe_name="Incorrect Calculation",
	negative_example=(
		"# sign error: subtracts bonus instead of adding\nscore = drought_tolerance - ph_bonus"
	),
	positive_example=("score = drought_tolerance + ph_bonus  # correct additive scoring"),
	telemetry_signatures=[
		"Top recommendation score is negative for all varieties",
		"Ranking inverted: worst variety ranked first",
	],
	ast_diff=("Replace BinOp[drought_tolerance Sub ph_bonus] with BinOp[drought_tolerance Add ph_bonus]"),
)

_td(
	"2.2.1",
	"Logical Bugs",
	"Conditional Logic",
	"Misplaced if/else",
	"An if/else branch is logically inverted or unreachable",
	[
		"Step 1: Trace the condition with True/False examples on paper",
		"Step 2: Add a unit test for each branch",
		"Step 3: Refactor to a guard-clause pattern for clarity",
	],
	cwe_id="CWE-670",
	cwe_name="Always-Incorrect Control Flow Implementation",
	negative_example=(
		"if self.site:\n"
		"    pass  # inverted — should throw when site is MISSING\n"
		"else:\n"
		"    frappe.throw(_('Site required'))"
	),
	positive_example=(
		"if not self.get('site'):\n    frappe.throw(_('Site required'), frappe.ValidationError)"
	),
	telemetry_signatures=[
		"Site-less record saved without triggering validation error",
		"frappe.throw never reached despite missing site field",
	],
	ast_diff=("Invert UnaryOp[not] in If condition: If(self.site) → If(not self.get('site'))"),
)

_td(
	"2.2.4",
	"Logical Bugs",
	"Conditional Logic",
	"Missing default cases",
	"A broad except clause catches all errors without logging, hiding failures",
	[
		"Step 1: Replace bare `except Exception: return []` with logged handling",
		"Step 2: Add `frappe.log_error(title='…', message=frappe.get_traceback())`",
		"Step 3: Narrow the exception type if possible (e.g. frappe.DoesNotExistError)",
	],
	cwe_id="CWE-390",
	cwe_name="Detection of Error Condition Without Action",
	negative_example=(
		"try:\n"
		"    return get_recommendations(site)\n"
		"except Exception:\n"
		"    return []  # silently swallows DB errors, permission errors, bugs"
	),
	positive_example=(
		"try:\n"
		"    return get_recommendations(site)\n"
		"except frappe.DoesNotExistError:\n"
		"    return []\n"
		"except Exception:\n"
		"    frappe.log_error(title='Recommendation error', message=frappe.get_traceback())\n"
		"    return []"
	),
	telemetry_signatures=[
		"Empty recommendation list returned with no preceding error log",
		"DB connection failure silently returns [] to caller",
	],
	ast_diff=(
		"Replace ExceptHandler[Exception, body=[Return([])]] with "
		"ExceptHandler[Exception, body=[Call[frappe.log_error](...), Return([])]]"
	),
)

_td(
	"2.3.3",
	"Logical Bugs",
	"State Management",
	"Incorrect flag toggling",
	"A boolean flag or DocType field that records state changes is not enabled",
	[
		"Step 1: Add `track_changes: 1` to the DocType JSON",
		"Step 2: Run `bench migrate` to activate change tracking in the DB",
		"Step 3: Verify the Version log is populated after editing a record",
	],
	cwe_id="CWE-778",
	cwe_name="Insufficient Logging",
	negative_example='{"name": "Lot", "track_changes": 0}  # no audit trail',
	positive_example='{"name": "Lot", "track_changes": 1}  # journalled',
	telemetry_signatures=[
		"Version log empty after modifying Lot status",
		"Auditor: no change history for Lot YAM-LOT-2024-00001",
	],
	ast_diff=("In DocType JSON: replace KeyValue[track_changes: 0] with KeyValue[track_changes: 1]"),
)

# ── 3. Performance Bugs ───────────────────────────────────────────────────
_td(
	"3.1.3",
	"Performance Bugs",
	"Speed Issues",
	"Excessive API calls",
	"Code makes N+1 DB calls inside a loop instead of a single bulk fetch",
	[
		"Step 1: Extract the loop body DB call to a single frappe.get_all() before the loop",
		"Step 2: Build a lookup dict keyed by record name",
		"Step 3: Profile with frappe.utils.perf.get_performance_log() to confirm improvement",
	],
	cwe_id="N/A",
	cwe_name="Not applicable (performance/scalability issue)",
	negative_example=("for lot in lots:\n    qty = frappe.db.get_value('Lot', lot.name, 'qty_kg')  # N+1"),
	positive_example=(
		"lot_names = [l.name for l in lots]\n"
		"rows = frappe.get_all('Lot', filters={'name': ['in', lot_names]}, fields=['name', 'qty_kg'])\n"
		"qty_map = {r.name: r.qty_kg for r in rows}\n"
		"for lot in lots:\n"
		"    qty = qty_map.get(lot.name)"
	),
	telemetry_signatures=[
		"slow query log: 247 identical SELECT qty_kg FROM tabLot WHERE name=? in 0.3s each",
		"frappe.performance: DB call count exceeded threshold (>50) in single request",
	],
	ast_diff=(
		"Move Call[frappe.db.get_value] out of For[lot in lots] body "
		"to a pre-loop Call[frappe.get_all] with Dict comprehension lookup"
	),
)

_td(
	"3.1.4",
	"Performance Bugs",
	"Speed Issues",
	"Unindexed DB queries",
	"A frequently-filtered field has no database index defined",
	[
		"Step 1: Add `search_index: 1` to the field definition in the DocType JSON",
		"Step 2: Run `bench migrate` to create the index",
		"Step 3: Verify with EXPLAIN SELECT that the index is used",
	],
	cwe_id="N/A",
	cwe_name="Not applicable (performance/DB tuning issue)",
	negative_example='{"fieldname": "site", "fieldtype": "Link", "search_index": 0}',
	positive_example='{"fieldname": "site", "fieldtype": "Link", "search_index": 1}',
	telemetry_signatures=[
		"EXPLAIN SELECT: type=ALL (full table scan) on tabLot for site filter",
		"slow query log: SELECT ... FROM tabLot WHERE site=? took 4.2s",
	],
	ast_diff=(
		"In DocType JSON field definition: replace KeyValue[search_index: 0] with KeyValue[search_index: 1]"
	),
)

# ── 4. Compatibility Bugs ─────────────────────────────────────────────────
_td(
	"4.3.2",
	"Compatibility Bugs",
	"Versioning",
	"Deprecated library usage",
	"Code uses a Frappe internal API that is deprecated or removed in the target version",
	[
		"Step 1: Check frappe/CHANGELOG.md for the deprecated API",
		"Step 2: Replace with the documented replacement",
		"Step 3: Add a CI check that imports the module with the target Frappe version",
	],
	cwe_id="CWE-1104",
	cwe_name="Use of Unmaintained Third Party Components",
	negative_example="frappe.call('frappe.client.get', doctype='Lot', name=name)",
	positive_example="frappe.get_doc('Lot', name)",
	telemetry_signatures=[
		"DeprecationWarning: frappe.call is deprecated in v16; use frappe.get_doc",
		"AttributeError: module 'frappe' has no attribute 'call'",
	],
	ast_diff=(
		"Replace Call[frappe.call](Constant('frappe.client.get'), ...) "
		"with Call[frappe.get_doc](Constant('Lot'), name)"
	),
)

# ── 5. Security Bugs ──────────────────────────────────────────────────────
_td(
	"5.1.3",
	"Security Bugs",
	"Authentication",
	"Token leakage",
	"A secret, token, or credential is hard-coded in source rather than read from config",
	[
		"Step 1: Remove the credential from source immediately",
		"Step 2: Rotate the leaked credential",
		"Step 3: Store it in frappe.conf or os.environ; never in .py or .json files",
		"Step 4: Add a secret-scan CI step (already in ci.yml)",
	],
	cwe_id="CWE-312",
	cwe_name="Cleartext Storage of Sensitive Information",
	negative_example='API_TOKEN = "sk-prod-abc123xyz789"  # committed to git',
	positive_example=(
		"API_TOKEN = os.environ.get('API_TOKEN') or frappe.conf.get('api_token')\n"
		"if not API_TOKEN:\n"
		"    frappe.throw(_('API_TOKEN not configured'), frappe.ConfigurationError)"
	),
	telemetry_signatures=[
		"truffleHog: high-entropy string detected in git history",
		"git-secrets: potential credential pattern matched in api/",
	],
	ast_diff=(
		"Replace Assign[Name=Constant(token_string)] with "
		"Assign[Name=Call[os.environ.get](Constant(env_key))]"
	),
)

_td(
	"5.2.2",
	"Security Bugs",
	"Authorization",
	"Privilege escalation",
	"An AI or background module calls a Frappe write API directly, bypassing authorization",
	[
		"Step 1: Remove all frappe.get_doc/save/insert/submit calls from the ai/ module",
		"Step 2: Move write operations to the api/ wrapper behind @frappe.whitelist()",
		"Step 3: Add assert_site_access() in the API wrapper before any write",
		"Step 4: Confirm AI module imports do not include `frappe`",
	],
	cwe_id="CWE-269",
	cwe_name="Improper Privilege Management",
	negative_example=(
		"# ai/agr_cereal_001.py\n"
		"import frappe\n"
		"def recommend(site):\n"
		"    doc = frappe.get_doc('Lot', lot_name)\n"
		"    doc.status = 'Accepted'\n"
		"    doc.save()  # autonomous DB write — forbidden in AI module"
	),
	positive_example=(
		"# ai/agr_cereal_001.py — pure Python, no frappe import\n"
		"def recommend(varieties, observations):\n"
		"    return {'top': sorted(varieties, key=score_fn)[0]}"
	),
	telemetry_signatures=[
		"frappe.save() called from ai/ module outside @whitelist endpoint",
		"Autonomous write detected: Lot status changed by AI process without user action",
	],
	ast_diff=(
		"Remove Import[frappe] and all Call[frappe.*] nodes from ai/ module; "
		"replace with pure-Python return Constant(dict)"
	),
)

_td(
	"5.2.3",
	"Security Bugs",
	"Authorization",
	"Broken access control",
	"A DocType with site isolation is missing permission_query_conditions or has_permission registration",
	[
		"Step 1: Add the DocType to permission_query_conditions in hooks.py",
		"Step 2: Add the DocType to has_permission in hooks.py",
		"Step 3: Implement query-condition and has-permission functions in site_permissions.py",
		"Step 4: Write an AT-10 style test that confirms cross-site records are not visible",
	],
	cwe_id="CWE-862",
	cwe_name="Missing Authorization",
	negative_example=(
		"# hooks.py — Complaint is in PQC but not has_permission\n"
		"permission_query_conditions = {'Complaint': '...'}\n"
		"has_permission = {}  # Complaint missing"
	),
	positive_example=(
		"permission_query_conditions = {'Complaint': '...complaint_query...'}\n"
		"has_permission = {'Complaint': '...complaint_has_permission...'}"
	),
	telemetry_signatures=[
		"User from Site A fetched Complaint belonging to Site B via direct GET",
		"has_permission hook not registered for Complaint — bypass possible",
	],
	ast_diff=("Add KeyValue['Complaint': '...'] to Dict[has_permission] in hooks.py"),
)

_td(
	"5.2.4",
	"Security Bugs",
	"Authorization",
	"Insecure direct object reference (IDOR)",
	"A DocType linked to a Lot allows cross-site access because lot.site is not validated",
	[
		"Step 1: Add lot_site = frappe.db.get_value('Lot', self.lot, 'site') in validate()",
		"Step 2: Throw ValidationError if lot_site != self.site",
		"Step 3: Add a unit test that attempts to create a cross-site linked record",
	],
	cwe_id="CWE-639",
	cwe_name="Authorization Bypass Through User-Controlled Key",
	negative_example=(
		"def validate(self):\n"
		"    # no cross-site lot check\n"
		"    if not self.get('site'):\n"
		"        frappe.throw(_('Site required'))"
	),
	positive_example=(
		"def validate(self):\n"
		"    if not self.get('site'):\n"
		"        frappe.throw(_('Site required'), frappe.ValidationError)\n"
		"    if self.get('lot'):\n"
		"        lot_site = frappe.db.get_value('Lot', self.lot, 'site')\n"
		"        if lot_site and lot_site != self.site:\n"
		"            frappe.throw(_('Lot site must match this record site'), frappe.ValidationError)"
	),
	telemetry_signatures=[
		"Complaint from Site A linked to Lot from Site B — data isolation breach",
		"ScaleTicket.lot site mismatch: ticket.site=Aden, lot.site=Sana'a",
	],
	ast_diff=(
		"Add If[self.get('lot')] block containing "
		"Assign[lot_site=Call[frappe.db.get_value]] and "
		"If[lot_site != self.site] → Call[frappe.throw]"
	),
)

_td(
	"5.3.3",
	"Security Bugs",
	"Data Protection",
	"Insecure storage",
	"Sensitive value (email, credential) is hard-coded inline instead of extracted to a constant or config",
	[
		"Step 1: Extract the value to a named module-level constant (e.g. _USER_A = '…')",
		"Step 2: For production secrets use frappe.conf.get() or os.environ.get()",
		"Step 3: Review all non-test Python files for remaining inline credentials",
	],
	cwe_id="CWE-312",
	cwe_name="Cleartext Storage of Sensitive Information",
	negative_example=(
		"# smoke.py\n"
		"def run_smoke_test():\n"
		"    login('admin@yam-agri.internal', 'admin')  # inline credential"
	),
	positive_example=(
		"# smoke.py\n"
		"_SMOKE_USER = os.environ.get('SMOKE_USER', 'admin@yam-agri.internal')\n"
		"_SMOKE_PASS = os.environ.get('SMOKE_PASS')\n\n"
		"def run_smoke_test():\n"
		"    login(_SMOKE_USER, _SMOKE_PASS)"
	),
	telemetry_signatures=[
		"git-blame: inline email committed in smoke.py line 42",
		"grep: literal email address found in non-test Python source",
	],
	ast_diff=(
		"Replace Constant(email_str) inside Call[login] with Name[_SMOKE_USER]; "
		"add module-level Assign[_SMOKE_USER=Call[os.environ.get]]"
	),
)

# ── 6. UI/UX Bugs ─────────────────────────────────────────────────────────
_td(
	"6.3.1",
	"UI/UX Bugs",
	"Interaction",
	"Unclear error messages",
	"A user-facing error string is not wrapped in _() / __() and will not be translated",
	[
		"Step 1: Add `from frappe import _` to the Python file if missing",
		"Step 2: Wrap: frappe.throw(_('message'), ExcType)",
		"Step 3: For JavaScript use __('message') in frappe.msgprint / frappe.confirm",
		"Step 4: Run `bench update-translations` and verify ar.csv is updated",
	],
	cwe_id="CWE-116",
	cwe_name="Improper Encoding or Escaping of Output",
	negative_example="frappe.throw('Validation failed — site is required')",
	positive_example="frappe.throw(_('Validation failed — site is required'), frappe.ValidationError)",
	telemetry_signatures=[
		"Arabic user sees English error: 'Validation failed — site is required'",
		"bench update-translations: untranslated key found in ar.csv",
	],
	ast_diff=(
		"Wrap Constant(str) arg of Call[frappe.throw] in Call[_](Constant(str)); "
		"add Attr[frappe.ValidationError] as second arg"
	),
)

_td(
	"6.1.4",
	"UI/UX Bugs",
	"Layout",
	"Non-responsive design",
	"DocType is missing title_field, making records unidentifiable in link dropdowns",
	[
		"Step 1: Add `title_field` to the DocType JSON pointing to the best human-readable field",
		"Step 2: Run `bench migrate`",
		"Step 3: Open a Link field that references this DocType and verify the label is readable",
	],
	cwe_id="N/A",
	cwe_name="Not applicable (UX/discoverability issue)",
	negative_example='{"name": "Site", "fields": [...]}  # no title_field',
	positive_example='{"name": "Site", "title_field": "site_name", "fields": [...]}',
	telemetry_signatures=[
		"Link dropdown shows 'SITE-001' instead of human-readable site name",
		"frappe.get_meta: title_field is None for DocType Site",
	],
	ast_diff=("Add KeyValue[title_field: 'site_name'] to top-level Dict in DocType JSON"),
)

# ── 8. Syntax & Build Bugs ────────────────────────────────────────────────
_td(
	"8.2.1",
	"Syntax & Build Bugs",
	"Runtime",
	"Null pointer exceptions",
	"Code calls a method or accesses an attribute on a value that could be None",
	[
		"Step 1: Add `if not value: return/raise` guard before using the value",
		"Step 2: Use `getattr(obj, 'attr', None)` instead of direct attribute access",
		"Step 3: Add a unit test that passes None for the nullable argument",
	],
	cwe_id="CWE-476",
	cwe_name="NULL Pointer Dereference",
	negative_example=(
		"site = frappe.db.get_value('Lot', lot_name, 'site')\n"
		"return site.upper()  # AttributeError if lot not found"
	),
	positive_example=("site = frappe.db.get_value('Lot', lot_name, 'site') or ''\nreturn site.upper()"),
	telemetry_signatures=[
		"AttributeError: 'NoneType' object has no attribute 'upper' in lot.py:84",
		"500 Internal Server Error: NoneType.upper() in /api/method/check_lot",
	],
	ast_diff=(
		"Replace Attribute[site.upper()] with "
		"Attribute[(site or '').upper()] — wrap in BoolOp[or Constant('')]"
	),
)

# ── 10. Regression Bugs ───────────────────────────────────────────────────
_td(
	"10.1.1",
	"Regression Bugs",
	"Feature Breakage",
	"Login system failure",
	"Permission hook is registered for one dict (PQC) but missing from the other (has_permission), risking access regression",
	[
		"Step 1: Diff permission_query_conditions and has_permission keys in hooks.py",
		"Step 2: Add any missing DocType to the hook that lacks it",
		"Step 3: Run AT-10 automated check to confirm both hooks fire correctly",
	],
	cwe_id="CWE-284",
	cwe_name="Improper Access Control",
	negative_example=(
		"permission_query_conditions = {'Lot': '...', 'Transfer': '...'}\n"
		"has_permission = {'Lot': '...'}  # Transfer missing"
	),
	positive_example=(
		"permission_query_conditions = {'Lot': '...', 'Transfer': '...'}\n"
		"has_permission = {'Lot': '...', 'Transfer': '...'}  # in sync"
	),
	telemetry_signatures=[
		"Direct GET /api/resource/Transfer/TRF-001 returns 200 for user with no site access",
		"AT-10 regression: Transfer visible across site boundary via direct URL",
	],
	ast_diff=(
		"Add KeyValue['Transfer': '...transfer_has_permission...'] to Dict[has_permission] in hooks.py"
	),
)

# ── 11. Hardcoded Bugs ────────────────────────────────────────────────────
# 11.1 Hardcoded Credentials
_td(
	"11.1.1",
	"Hardcoded Bugs",
	"Hardcoded Credentials",
	"Passwords",
	"A password or secret value is hard-coded in source instead of read from environment/config",
	[
		"Step 1: Remove the hardcoded password from source immediately",
		"Step 2: Rotate the credential — treat it as compromised",
		"Step 3: Store it in frappe.conf or os.environ; read via frappe.conf.get('key') / os.environ.get('KEY')",
		"Step 4: Add the variable name to .env.example with a placeholder value",
		"Step 5: Add a secret-scan CI step to prevent recurrence",
	],
	cwe_id="CWE-259",
	cwe_name="Use of Hard-coded Password",
	negative_example='db_password = "P@ssw0rd123!"  # committed to git',
	positive_example=(
		"db_password = frappe.conf.get('db_password') or os.environ.get('DB_PASSWORD')\n"
		"if not db_password:\n"
		"    frappe.throw(_('DB_PASSWORD not configured'), frappe.ConfigurationError)"
	),
	telemetry_signatures=[
		"git-secrets: matched pattern PASSWORD=[^$] in config.py",
		"truffleHog: high-entropy string 'P@ssw0rd123!' in git history",
	],
	ast_diff=(
		"Replace Assign[Name=Constant(password_literal)] with "
		"Assign[Name=BoolOp[Call[frappe.conf.get] or Call[os.environ.get]]]"
	),
)

_td(
	"11.1.2",
	"Hardcoded Bugs",
	"Hardcoded Credentials",
	"API Keys",
	"An API key or secret is hard-coded in source instead of read from environment/config",
	[
		"Step 1: Remove the API key from source immediately and rotate it",
		"Step 2: Add it to .env as API_KEY=<value> and to .env.example as API_KEY=",
		"Step 3: Read via os.environ.get('API_KEY') or frappe.conf.get('api_key')",
		"Step 4: Restrict key privileges to only the necessary scopes",
		"Step 5: Set up automatic key rotation if the provider supports it",
	],
	cwe_id="CWE-798",
	cwe_name="Use of Hard-coded Credentials",
	negative_example='api_key = "sk-abcdef1234567890"  # hardcoded in source',
	positive_example=(
		"api_key = os.environ.get('API_KEY') or frappe.conf.get('api_key')\n"
		"if not api_key:\n"
		"    frappe.throw(_('API_KEY not configured'), frappe.ConfigurationError)"
	),
	telemetry_signatures=[
		"git-secrets: API_KEY pattern matched in api/integrations.py",
		"CI secret-scan: high-entropy string in non-.env file",
	],
	ast_diff=(
		"Replace Assign[api_key=Constant(key_str)] with "
		"Assign[api_key=Call[os.environ.get](Constant('API_KEY'))]"
	),
)

_td(
	"11.1.3",
	"Hardcoded Bugs",
	"Hardcoded Credentials",
	"Tokens",
	"A JWT, OAuth, or refresh token is embedded in source code",
	[
		"Step 1: Invalidate the token immediately — it is compromised",
		"Step 2: Remove the token from all source files and version history",
		"Step 3: Use short-lived tokens generated at runtime; store only signing secrets in env",
		"Step 4: Set expiry on all tokens (JWT exp claim, OAuth TTL)",
		"Step 5: Implement token refresh logic that reads secrets from config",
	],
	cwe_id="CWE-798",
	cwe_name="Use of Hard-coded Credentials",
	negative_example='auth_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiJ9.XXXX"',
	positive_example=(
		"# JWT secret from env; token generated at runtime\n"
		"JWT_SECRET = os.environ.get('JWT_SECRET')\n"
		"auth_token = jwt.encode({'sub': user, 'exp': now + timedelta(hours=1)}, JWT_SECRET)"
	),
	telemetry_signatures=[
		"JWT token never expires: exp claim missing in payload",
		"truffleHog: base64 eyJ pattern (JWT) detected in source file",
	],
	ast_diff=(
		"Replace Assign[auth_token=Constant(jwt_literal)] with "
		"Assign[auth_token=Call[jwt.encode](Dict, Name[JWT_SECRET])]"
	),
)

# 11.2 Hardcoded Environment & Config
_td(
	"11.2.1",
	"Hardcoded Bugs",
	"Hardcoded Environment & Config",
	"Database",
	"A database connection string, credentials, or schema name is hardcoded in source",
	[
		"Step 1: Extract the connection string to an environment variable (DATABASE_URL)",
		"Step 2: Use frappe.db or SQLAlchemy's from-env config; never build connection strings manually",
		"Step 3: Ensure test DB credentials are never the same as production",
		"Step 4: Add DATABASE_URL to .env.example with a safe placeholder",
		"Step 5: Rotate any DB credentials that were committed to version control",
	],
	cwe_id="CWE-312",
	cwe_name="Cleartext Storage of Sensitive Information",
	negative_example='conn = "mysql://root:pass@192.168.1.5/yam_prod"  # hardcoded',
	positive_example=(
		"conn = os.environ.get('DATABASE_URL')\n"
		"if not conn:\n"
		"    frappe.throw(_('DATABASE_URL not set'), frappe.ConfigurationError)"
	),
	telemetry_signatures=[
		"grep: mysql:// pattern found in non-.env Python file",
		"CI secret-scan: connection string contains plaintext credentials",
	],
	ast_diff=(
		"Replace Assign[conn=Constant(dsn_str)] with "
		"Assign[conn=Call[os.environ.get](Constant('DATABASE_URL'))]"
	),
)

_td(
	"11.2.2",
	"Hardcoded Bugs",
	"Hardcoded Environment & Config",
	"Server",
	"A server IP address, hostname, port, or URL is hard-coded instead of read from config",
	[
		"Step 1: Extract the value to an environment variable (e.g. SERVICE_HOST, SERVICE_PORT)",
		"Step 2: Read via os.environ.get('SERVICE_HOST', 'localhost') with a safe default",
		"Step 3: Add the variable to .env.example",
		"Step 4: Update Docker Compose / k3s manifests to inject the env var",
		"Step 5: Verify all environments (dev/staging/prod) use separate values",
	],
	cwe_id="CWE-656",
	cwe_name="Reliance on Security Through Obscurity",
	negative_example='host = "192.168.1.100"  # breaks when server moves',
	positive_example='host = os.environ.get("SERVICE_HOST", "localhost")',
	telemetry_signatures=[
		"ConnectionRefusedError: [Errno 111] 192.168.1.100:8080 — server relocated",
		"Deployment failed: hardcoded staging IP used in production",
	],
	ast_diff=(
		"Replace Assign[host=Constant(ip_str)] with "
		"Assign[host=Call[os.environ.get](Constant('SERVICE_HOST'), Constant('localhost'))]"
	),
)

_td(
	"11.2.3",
	"Hardcoded Bugs",
	"Hardcoded Environment & Config",
	"Cloud",
	"A cloud resource identifier (S3 bucket, IAM role, region, endpoint) is hardcoded in source",
	[
		"Step 1: Extract to an environment variable (S3_BUCKET, AWS_REGION, etc.)",
		"Step 2: Ensure different buckets/regions for dev, staging, and production",
		"Step 3: Never reference production cloud resources from development code",
		"Step 4: Apply least-privilege IAM policies — no wildcard resource ARNs",
		"Step 5: Add cloud resource names to .env.example",
	],
	cwe_id="CWE-798",
	cwe_name="Use of Hard-coded Credentials",
	negative_example='S3_BUCKET = "yam-production-backups"  # prod bucket in dev code',
	positive_example='S3_BUCKET = os.environ.get("S3_BUCKET") or frappe.conf.get("s3_bucket")',
	telemetry_signatures=[
		"Dev process wrote to production S3 bucket yam-production-backups",
		"IAM policy violation: wildcard resource arn:aws:s3:::*",
	],
	ast_diff=(
		"Replace Assign[S3_BUCKET=Constant(bucket_name)] with "
		"Assign[S3_BUCKET=Call[os.environ.get](Constant('S3_BUCKET'))]"
	),
)

# 11.3 Hardcoded Business Logic
_td(
	"11.3.1",
	"Hardcoded Bugs",
	"Hardcoded Business Logic",
	"Workflow",
	"A business rule value (tax rate, discount %, shipping fee, trial period) is hardcoded in source",
	[
		"Step 1: Move the value to a Frappe Settings DocType or system configuration",
		"Step 2: Read it via frappe.db.get_single_value('Settings DocType', 'field')",
		"Step 3: Create a migration to populate the initial value in the DB",
		"Step 4: Add the Settings DocType to the relevant Workspace for admin access",
		"Step 5: Document which DocType field controls each business rule",
	],
	cwe_id="CWE-656",
	cwe_name="Reliance on Security Through Obscurity",
	negative_example="TAX_RATE = 0.15  # requires code change to update",
	positive_example=("TAX_RATE = frappe.db.get_single_value('YAM Settings', 'vat_rate') or 0.15"),
	telemetry_signatures=[
		"Tax calculation wrong after VAT rate changed — requires code deploy",
		"YAM Settings.vat_rate ignored; hardcoded 0.15 used instead",
	],
	ast_diff=(
		"Replace Assign[TAX_RATE=Constant(0.15)] with "
		"Assign[TAX_RATE=Call[frappe.db.get_single_value]('YAM Settings', 'vat_rate')]"
	),
)

_td(
	"11.3.2",
	"Hardcoded Bugs",
	"Hardcoded Business Logic",
	"UI/UX",
	"A UI string (label, message, description) is hardcoded without i18n wrapping",
	[
		"Step 1: Wrap Python strings in _('…') and JavaScript strings in __('…')",
		"Step 2: Run `bench update-translations` to export new strings",
		"Step 3: Add translations to translations/ar.csv for Arabic users",
		"Step 4: Avoid string concatenation inside _() — use named placeholders: _('Hello {0}').format(name)",
	],
	cwe_id="CWE-116",
	cwe_name="Improper Encoding or Escaping of Output",
	negative_example='frappe.msgprint("Record saved successfully")',
	positive_example='frappe.msgprint(__("Record saved successfully"))',
	telemetry_signatures=[
		"Arabic user interface shows English label 'Record saved successfully'",
		"bench update-translations: missing key 'Record saved successfully' in ar.csv",
	],
	ast_diff=("Wrap Constant(str) arg of Call[frappe.msgprint] in Call[__](Constant(str))"),
)

_td(
	"11.3.3",
	"Hardcoded Bugs",
	"Hardcoded Business Logic",
	"Feature Flags",
	"A feature toggle, role check, or access limit is hardcoded in source instead of driven by config",
	[
		"Step 1: Replace the hardcoded check with a Frappe role or System Setting",
		"Step 2: Use frappe.has_role('Role Name') for role-based checks",
		"Step 3: Use frappe.db.get_single_value('Settings', 'upload_limit') for limits",
		"Step 4: Document the configuration knob in the admin guide",
	],
	cwe_id="CWE-284",
	cwe_name="Improper Access Control",
	negative_example=(
		"ENABLE_SMS = True  # must re-deploy to toggle\n"
		"if frappe.session.user == 'admin@yam.internal':  # hardcoded user check"
	),
	positive_example=(
		"ENABLE_SMS = frappe.db.get_single_value('YAM Settings', 'enable_sms')\n"
		"if frappe.has_role('System Manager'):"
	),
	telemetry_signatures=[
		"Feature flag ENABLE_SMS not toggleable at runtime — requires code deploy",
		"Hardcoded user check: admin@yam.internal matched in site_permissions.py",
	],
	ast_diff=(
		"Replace Assign[ENABLE_SMS=Constant(True)] with "
		"Assign[ENABLE_SMS=Call[frappe.db.get_single_value]]; "
		"replace Compare[session.user == email] with Call[frappe.has_role](role)"
	),
)

# ── 12. Master Data Bugs ──────────────────────────────────────────────────
# 12.1 Data Completeness
_td(
	"12.1.1",
	"Master Data Bugs",
	"Data Completeness",
	"Missing Records",
	"A required master record (e.g. Site, Crop, Warehouse) is referenced but does not exist",
	[
		"Step 1: Identify which master record is missing from the referenced DocType",
		"Step 2: Create the missing record via Frappe Desk or a fixture",
		"Step 3: Add a validation in the controller to raise a clear error when the reference is missing",
		"Step 4: Add the required records to demo fixtures (seed/) to prevent recurrence on fresh installs",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example=("self.site = 'Sana\\'a Silo'  # site may not exist in DB"),
	positive_example=(
		"if not frappe.db.exists('Site', self.get('site')):\n"
		"    frappe.throw(_('Site {0} not found').format(self.site), frappe.ValidationError)"
	),
	telemetry_signatures=[
		"LinkValidationError: 'Sana'a Silo' not found in Site",
		"frappe.ValidationError: could not find Site record",
	],
	ast_diff=(
		"Add If[not Call[frappe.db.exists]('Site', self.site)] → Call[frappe.throw] "
		"before any use of self.site as a foreign key"
	),
)

_td(
	"12.1.2",
	"Master Data Bugs",
	"Data Completeness",
	"Incomplete Attributes",
	"A master record is missing one or more mandatory attributes (unit, currency, category, etc.)",
	[
		"Step 1: Identify which attribute is missing",
		"Step 2: Mark the field reqd:1 in the DocType JSON so the form enforces it",
		"Step 3: Add a Python validate() check for the field",
		"Step 4: Update existing incomplete records via a data migration patch",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example='{"fieldname": "unit_of_measure", "reqd": 0}  # optional — allows blank',
	positive_example='{"fieldname": "unit_of_measure", "reqd": 1}  # mandatory',
	telemetry_signatures=[
		"Calculation error: unit_of_measure is blank for Lot YAM-LOT-2024-00042",
		"Invoice line item has no unit — pricing engine returns zero",
	],
	ast_diff=("In DocType JSON field definition: replace KeyValue[reqd: 0] with KeyValue[reqd: 1]"),
)

_td(
	"12.1.3",
	"Master Data Bugs",
	"Data Completeness",
	"Orphan Records",
	"A child or transaction record references a master that no longer exists",
	[
		"Step 1: Run a DB audit query: SELECT name FROM tab WHERE parent_field NOT IN (SELECT name FROM tabParent)",
		"Step 2: Fix or delete orphan records",
		"Step 3: Add a DB-level FK constraint or a Frappe link validation",
		"Step 4: Add a scheduled job to detect and alert on new orphans",
	],
	cwe_id="CWE-459",
	cwe_name="Incomplete Cleanup",
	negative_example=("frappe.db.delete('Lot', lot_name)  # QCTests and ScaleTickets left orphaned"),
	positive_example=(
		"# Use frappe.delete_doc which cascades child DocType deletes\n"
		"frappe.delete_doc('Lot', lot_name, delete_permanently=True)"
	),
	telemetry_signatures=[
		"IntegrityError: orphan QCTest YAM-QCT-2024-00008 references deleted Lot",
		"Daily audit: 12 ScaleTickets have no parent Lot",
	],
	ast_diff=(
		"Replace Call[frappe.db.delete](Constant('Lot'), name) with "
		"Call[frappe.delete_doc](Constant('Lot'), name, delete_permanently=True)"
	),
)

# 12.2 Data Accuracy
_td(
	"12.2.1",
	"Master Data Bugs",
	"Data Accuracy",
	"Incorrect Values",
	"A master record contains a factually wrong value (wrong tax rate, wrong conversion factor, etc.)",
	[
		"Step 1: Identify the correct value from an authoritative source",
		"Step 2: Correct the record and document the change in a version note",
		"Step 3: Add a range/sanity validator in the controller (e.g. 0 < tax_rate <= 100)",
		"Step 4: If the value is variable, move it to a configurable Settings DocType",
	],
	cwe_id="CWE-682",
	cwe_name="Incorrect Calculation",
	negative_example=("# YAM Settings record has vat_rate = 0.25 — wrong for Yemen (should be 0.15)"),
	positive_example=(
		"def validate(self):\n"
		"    if not (0 < (self.vat_rate or 0) <= 1):\n"
		"        frappe.throw(_('VAT rate must be between 0 and 1'), frappe.ValidationError)"
	),
	telemetry_signatures=[
		"Invoice total 25% above expected — vat_rate is 0.25, not 0.15",
		"Sanity check failed: vat_rate=0.25 outside allowed range [0,1]",
	],
	ast_diff=(
		"Add If[not(0 < self.vat_rate <= 1)] → Call[frappe.throw] "
		"in FunctionDef[validate] of YAM Settings controller"
	),
)

_td(
	"12.2.3",
	"Master Data Bugs",
	"Data Accuracy",
	"Outdated Data",
	"A master record that should have been deactivated (expired contract, obsolete product, retired employee) is still active",
	[
		"Step 1: Add an expiry_date or is_active field to the DocType",
		"Step 2: Add a scheduled job that sets is_active=0 when expiry_date < today",
		"Step 3: Filter all list views by is_active=1 by default",
		"Step 4: Notify the responsible user 30 days before expiry",
	],
	cwe_id="N/A",
	cwe_name="Not applicable (data lifecycle/governance issue)",
	negative_example=(
		"# Device DocType has no is_active or expiry field\n{'fieldname': 'status'}  # manual status only"
	),
	positive_example=(
		"{'fieldname': 'is_active', 'fieldtype': 'Check', 'default': '1'},\n"
		"{'fieldname': 'expiry_date', 'fieldtype': 'Date'}"
	),
	telemetry_signatures=[
		"Retired Device YAM-DEV-2023-00003 still returned in active device list",
		"Scale ticket linked to decommissioned device — measurement unreliable",
	],
	ast_diff=(
		"Add Dict[fieldname=is_active, fieldtype=Check, default=1] to fields list in Device DocType JSON"
	),
)

# 12.3 Data Consistency
_td(
	"12.3.1",
	"Master Data Bugs",
	"Data Consistency",
	"Cross-System Inconsistency",
	"The same real-world entity has different IDs, names, or codes in different system modules",
	[
		"Step 1: Identify the canonical source of truth for the entity",
		"Step 2: Sync or migrate other systems to use the canonical ID",
		"Step 3: Implement a cross-module validation that raises an alert on mismatch",
		"Step 4: Document the master-system mapping in architecture docs",
	],
	cwe_id="CWE-116",
	cwe_name="Improper Encoding or Escaping of Output",
	negative_example=(
		"erp_lot_code = lot.name          # 'YAM-LOT-2024-00001'\n"
		"crm_lot_code = lot.external_ref  # 'LOT-24-001' — mismatch"
	),
	positive_example=(
		"# Use canonical lot.name as the cross-system identifier\n"
		"canonical_id = lot.name\n"
		"if lot.external_ref and lot.external_ref != canonical_id:\n"
		"    frappe.log_error(title='ID mismatch', message=f'{canonical_id} vs {lot.external_ref}')"
	),
	telemetry_signatures=[
		"CRM lookup failed: external_ref 'LOT-24-001' not found in ERP",
		"Cross-system reconciliation: 14 lots have mismatched IDs",
	],
	ast_diff=(
		"Add If[lot.external_ref != canonical_id] → Call[frappe.log_error] "
		"after Assign[canonical_id=lot.name]"
	),
)

_td(
	"12.3.3",
	"Master Data Bugs",
	"Data Consistency",
	"Duplication",
	"The same real-world entity appears as two or more separate master records",
	[
		"Step 1: Add unique constraints on natural key fields (name, code, email)",
		"Step 2: Run a deduplication script to merge duplicate records",
		"Step 3: Update all references from duplicate records to the canonical record",
		"Step 4: Enable frappe.DuplicateEntryError detection in the controller",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example=("# Two Site records: 'Sana'a Silo' and 'Sanaa Silo' — same physical site"),
	positive_example=(
		"def validate(self):\n"
		"    if frappe.db.exists('Site', {'site_name': self.site_name, 'name': ['!=', self.name]}):\n"
		"        frappe.throw(_('Site with name {0} already exists').format(self.site_name))"
	),
	telemetry_signatures=[
		"Duplicate Site records detected: 'Sana'a Silo' and 'Sanaa Silo'",
		"frappe.DuplicateEntryError on site_name field",
	],
	ast_diff=(
		"Add If[Call[frappe.db.exists]('Site', {'site_name': self.site_name, ...})] "
		"→ Call[frappe.throw] in FunctionDef[validate]"
	),
)

# 12.4 Referential Integrity
_td(
	"12.4.1",
	"Master Data Bugs",
	"Referential Integrity",
	"Broken Links",
	"A record contains a Link field pointing to a master that has been deleted or renamed",
	[
		"Step 1: Add a cascade-on-delete or restrict-on-delete policy to the Link field",
		"Step 2: Run an integrity check script to find broken links",
		"Step 3: Add a validate() check: if link_value and not frappe.db.exists(...): frappe.throw(...)",
		"Step 4: Schedule a daily integrity report for critical master links",
	],
	cwe_id="CWE-459",
	cwe_name="Incomplete Cleanup",
	negative_example=("self.lot = 'YAM-LOT-2024-00001'  # lot may have been deleted"),
	positive_example=(
		"if self.get('lot') and not frappe.db.exists('Lot', self.lot):\n"
		"    frappe.throw(_('Lot {0} not found — it may have been deleted').format(self.lot))"
	),
	telemetry_signatures=[
		"LinkValidationError: 'YAM-LOT-2024-00001' not found in Lot",
		"ScaleTicket references deleted Lot — integrity violation",
	],
	ast_diff=(
		"Add If[self.get('lot') and not Call[frappe.db.exists]('Lot', self.lot)] "
		"→ Call[frappe.throw] in FunctionDef[validate]"
	),
)

_td(
	"12.4.3",
	"Master Data Bugs",
	"Referential Integrity",
	"Foreign Key Violations",
	"A transaction record references a master ID that does not exist in the master table",
	[
		"Step 1: Add DB-level FK constraints where possible (InnoDB supports them)",
		"Step 2: Add a Frappe validate() check before insert/update",
		"Step 3: Add a data audit script to find and report existing violations",
		"Step 4: Prevent orphan creation by using frappe.db.exists() before saving",
	],
	cwe_id="CWE-20",
	cwe_name="Improper Input Validation",
	negative_example=("doc.lot = 'NONEXISTENT-LOT-ID'\ndoc.save()  # no FK check — corrupts data"),
	positive_example=(
		"if doc.lot and not frappe.db.exists('Lot', doc.lot):\n"
		"    frappe.throw(_('Invalid lot reference: {0}').format(doc.lot), frappe.ValidationError)\n"
		"doc.save()"
	),
	telemetry_signatures=[
		"IntegrityError: foreign key constraint failed — lot 'NONEXISTENT' does not exist",
		"Data audit: 3 QCTests reference non-existent Lots",
	],
	ast_diff=(
		"Add If[not Call[frappe.db.exists]('Lot', doc.lot)] → Call[frappe.throw] before Call[doc.save()]"
	),
)

# 12.5 Governance & Compliance
_td(
	"12.5.1",
	"Master Data Bugs",
	"Governance & Compliance",
	"Policy Violations",
	"A master record is missing a compliance-required attribute (certificate, KYC, approval status)",
	[
		"Step 1: Define which fields are compliance-required and mark them reqd:1",
		"Step 2: Add a before_submit validator that blocks submission if compliance fields are empty",
		"Step 3: Add compliance fields to the relevant document checklist",
		"Step 4: Generate a compliance report listing all records with missing data",
	],
	cwe_id="CWE-284",
	cwe_name="Improper Access Control",
	negative_example=(
		"# Certificate field is optional — vendor can be approved without one\n"
		"{'fieldname': 'compliance_certificate', 'reqd': 0}"
	),
	positive_example=(
		"def before_submit(self):\n"
		"    if not self.get('compliance_certificate'):\n"
		"        frappe.throw(_('Compliance certificate is required before approval'), frappe.ValidationError)"
	),
	telemetry_signatures=[
		"Vendor YAM-VEND-00042 approved without compliance certificate",
		"HACCP audit failed: 7 vendors missing compliance_certificate field",
	],
	ast_diff=(
		"Add FunctionDef[before_submit] with If[not self.compliance_certificate] "
		"→ Call[frappe.throw] to controller class"
	),
)

_td(
	"12.5.2",
	"Master Data Bugs",
	"Governance & Compliance",
	"Audit Failures",
	"A master DocType has no change log (track_changes disabled), so unauthorized edits are undetectable",
	[
		"Step 1: Enable track_changes:1 in the DocType JSON",
		"Step 2: Run bench migrate to activate journalling",
		"Step 3: Add a permission check that restricts edits to authorized roles",
		"Step 4: Add a daily report of master data changes for auditor review",
	],
	cwe_id="CWE-778",
	cwe_name="Insufficient Logging",
	negative_example='{"name": "Device", "track_changes": 0}  # no audit trail',
	positive_example='{"name": "Device", "track_changes": 1}  # all edits journalled',
	telemetry_signatures=[
		"Auditor: no Version log entries for Device YAM-DEV-2024-00001",
		"ISO 22000 audit: unauthorised Device record edit undetectable",
	],
	ast_diff=("In master DocType JSON: replace KeyValue[track_changes: 0] with KeyValue[track_changes: 1]"),
)

_td(
	"12.5.3",
	"Master Data Bugs",
	"Governance & Compliance",
	"Security",
	"Master data contains sensitive values (credentials, PII) that are stored or exposed insecurely",
	[
		"Step 1: Identify all sensitive fields (password, tax_id, bank_account)",
		"Step 2: Mark sensitive fields as password type or enable field encryption",
		"Step 3: Remove sensitive data from API responses (use frappe.has_permission checks)",
		"Step 4: Ensure sensitive fields are excluded from global search indexing",
		"Step 5: Add data-at-rest encryption for fields that hold PII",
	],
	cwe_id="CWE-312",
	cwe_name="Cleartext Storage of Sensitive Information",
	negative_example=(
		"# Site DocType exposes all fields including sensitive ones\n"
		"frappe.get_all('Site', fields=['*'])  # returns tax_id, bank_account, etc."
	),
	positive_example=(
		"# Restrict to non-sensitive fields only\n"
		"frappe.get_all('Site', fields=['name', 'site_type', 'site_name'])"
	),
	telemetry_signatures=[
		"API response for /api/resource/Site includes bank_account in plaintext",
		"Global search indexed sensitive field tax_id — visible to all users",
	],
	ast_diff=(
		"Replace Constant('*') in Call[frappe.get_all](fields=['*']) with "
		"List[Constant('name'), Constant('site_type'), Constant('site_name')]"
	),
)


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
	learned_rules: list[LearnedRule] = field(default_factory=list)

	def add(self, finding: QCFinding) -> None:
		self.findings.append(finding)

	def add_learned(self, rule: LearnedRule) -> None:
		self.learned_rules.append(rule)

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
				"learned_rules_proposed": len(self.learned_rules),
				"taxonomy_coverage": coverage_stats(),
			},
			"findings": [
				{
					"severity": f.severity,
					"rule_id": f.rule_id,
					"bug_code": f.bug_code,
					"category": f.category,
					"subcategory": f.subcategory,
					"bug_type": f.bug_type,
					"cwe_id": TAXONOMY[f.bug_code].cwe_id if f.bug_code in TAXONOMY else "",
					"cwe_name": TAXONOMY[f.bug_code].cwe_name if f.bug_code in TAXONOMY else "",
					"training_coverage": _compute_coverage(TAXONOMY[f.bug_code])
					if f.bug_code in TAXONOMY
					else 0.0,
					"file": f.file,
					"line": f.line,
					"message": f.message,
					"planned_response": list(f.planned_response),
				}
				for f in self.findings
			],
			"learned_rules": [r.to_dict() for r in self.learned_rules],
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
# Auto-learning infrastructure
# ---------------------------------------------------------------------------


@dataclass
class LearnedRule:
	"""A new bug pattern proposed by the agent during auto-learning.

	The agent generates these when it finds suspicious patterns that do NOT
	match any rule in the current TAXONOMY.  They can be reviewed by a
	developer and promoted to permanent BugDefinitions via --load-taxonomy.
	"""

	observed_pattern: str  # the raw snippet that triggered the proposal
	file: str
	line: int | None
	suggested_code: str  # e.g. "11.4.1"
	suggested_category: str
	suggested_subcategory: str
	suggested_bug_type: str
	proposed_message: str
	proposed_planned_response: tuple[str, ...]
	confidence: str  # "high" | "medium" | "low"

	def to_dict(self) -> dict:
		return {
			"observed_pattern": self.observed_pattern,
			"file": self.file,
			"line": self.line,
			"suggested_code": self.suggested_code,
			"suggested_category": self.suggested_category,
			"suggested_subcategory": self.suggested_subcategory,
			"suggested_bug_type": self.suggested_bug_type,
			"proposed_message": self.proposed_message,
			"proposed_planned_response": list(self.proposed_planned_response),
			"confidence": self.confidence,
		}


# Counter for generating unique auto-learned codes
_LEARNED_COUNTER: dict[str, int] = {}


def propose_bug_type(
	*,
	observed_pattern: str,
	file: str,
	line: int | None,
	suggested_category: str,
	suggested_subcategory: str,
	suggested_bug_type: str,
	proposed_message: str,
	proposed_planned_response: list[str],
	confidence: str = "medium",
) -> LearnedRule:
	"""Propose a new bug type based on an observed code pattern.

	The suggested_code is auto-generated as ``<category_num>.99.<seq>`` to
	avoid colliding with existing taxonomy codes.  Callers should review the
	returned LearnedRule and, if valid, register it with register_bug_type().
	"""
	# Derive a category number from the category name
	_cat_map = {
		"Hardcoded Bugs": "11",
		"Master Data Bugs": "12",
		"Functional Bugs": "1",
		"Logical Bugs": "2",
		"Performance Bugs": "3",
		"Compatibility Bugs": "4",
		"Security Bugs": "5",
		"UI/UX Bugs": "6",
		"Integration Bugs": "7",
		"Syntax & Build Bugs": "8",
		"Concurrency Bugs": "9",
		"Regression Bugs": "10",
	}
	cat_num = _cat_map.get(suggested_category, "99")
	key = f"{cat_num}.99"
	_LEARNED_COUNTER[key] = _LEARNED_COUNTER.get(key, 0) + 1
	code = f"{key}.{_LEARNED_COUNTER[key]}"

	return LearnedRule(
		observed_pattern=observed_pattern,
		file=file,
		line=line,
		suggested_code=code,
		suggested_category=suggested_category,
		suggested_subcategory=suggested_subcategory,
		suggested_bug_type=suggested_bug_type,
		proposed_message=proposed_message,
		proposed_planned_response=tuple(proposed_planned_response),
		confidence=confidence,
	)


def _auto_classify_credential(snippet: str) -> tuple[str, str, str]:
	"""Heuristic: return (category, subcategory, bug_type) for a credential snippet."""
	low = snippet.lower()
	# Map keyword → bug_type in a single pass
	keyword_map: dict[str, str] = {
		"password": "Passwords",
		"passwd": "Passwords",
		"pwd": "Passwords",
		"secret": "Passwords",
		"api_key": "API Keys",
		"apikey": "API Keys",
		"access_key": "API Keys",
		"client_secret": "API Keys",
		"token": "Tokens",
		"jwt": "Tokens",
		"bearer": "Tokens",
		"auth_token": "Tokens",
		"refresh_token": "Tokens",
	}
	for keyword, bug_type in keyword_map.items():
		if keyword in low:
			return ("Hardcoded Bugs", "Hardcoded Credentials", bug_type)
	return ("Security Bugs", "Data Protection", "Insecure storage")


def save_learned_rules(rules: list[LearnedRule], path: str) -> None:
	"""Persist proposed learned rules to a JSON file for later review."""
	with open(path, "w", encoding="utf-8") as fh:
		json.dump([r.to_dict() for r in rules], fh, indent=2)


def load_taxonomy_from_file(path: str) -> list[BugDefinition]:
	"""Load BugDefinitions from a JSON file (previously saved by save_learned_rules).

	Entries must have at least: code, category, subcategory, bug_type,
	proposed_message / predefined_message, proposed_planned_response / planned_response.
	Returns the list of loaded definitions (they are also auto-registered).
	"""
	try:
		with open(path, encoding="utf-8") as fh:
			raw = json.load(fh)
	except (json.JSONDecodeError, OSError) as exc:
		raise ValueError(f"Cannot load taxonomy file {path}: {exc}") from exc

	loaded: list[BugDefinition] = []
	for entry in raw:
		code = entry.get("suggested_code") or entry.get("code", "")
		if not code:
			continue
		defn = BugDefinition(
			code=code,
			category=entry.get("suggested_category") or entry.get("category", "Unknown"),
			subcategory=entry.get("suggested_subcategory") or entry.get("subcategory", "Unknown"),
			bug_type=entry.get("suggested_bug_type") or entry.get("bug_type", "Unknown"),
			predefined_message=entry.get("proposed_message") or entry.get("predefined_message", ""),
			planned_response=tuple(
				entry.get("proposed_planned_response") or entry.get("planned_response") or []
			),
			cwe_id=entry.get("cwe_id", ""),
			cwe_name=entry.get("cwe_name", ""),
			negative_example=entry.get("negative_example", ""),
			positive_example=entry.get("positive_example", ""),
			telemetry_signatures=tuple(entry.get("telemetry_signatures") or []),
			ast_diff=entry.get("ast_diff", ""),
		)
		register_bug_type(defn)
		loaded.append(defn)
	return loaded


# ---------------------------------------------------------------------------
# Training dataset — JSON-LD export
# ---------------------------------------------------------------------------

_JSONLD_CONTEXT = {
	"@vocab": "https://yam-agri.io/taxonomy/",
	"schema": "https://schema.org/",
	"yam": "https://yam-agri.io/taxonomy/",
	"cwe": "https://cwe.mitre.org/data/definitions/",
	"xsd": "http://www.w3.org/2001/XMLSchema#",
	"rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}


class TrainingDataset:
	"""JSON-LD training dataset for the auto-learning agent.

	The dataset maps every BugDefinition to a structured node that includes:
	- CWE classification (cwe:id, cwe:name)
	- Pattern pair  (yam:negativeExample, yam:positiveExample)
	- Telemetry signatures  (yam:telemetrySignatures)
	- AST-level diff description  (yam:astDiff)
	- Coverage score  (yam:trainingCoverage)

	Usage::

	    from tools.frappe_skill_agent import TrainingDataset, TAXONOMY

	    TrainingDataset.to_jsonld_file("/tmp/training.jsonld.json")

	    # Export a subset (e.g. only Security bugs)
	    security = {k: v for k, v in TAXONOMY.items() if v.category == "Security Bugs"}
	    TrainingDataset.to_jsonld_file("/tmp/security.json", security)
	"""

	@staticmethod
	def _node(defn: BugDefinition) -> dict:
		"""Convert a BugDefinition to a JSON-LD graph node."""
		node: dict = {
			"@type": "yam:BugDefinition",
			"@id": f"yam:{defn.code}",
			"yam:code": {"@value": defn.code, "@type": "xsd:string"},
			"yam:category": defn.category,
			"yam:subcategory": defn.subcategory,
			"schema:name": defn.bug_type,
			"yam:predefinedMessage": defn.predefined_message,
			"yam:plannedResponse": list(defn.planned_response),
			"yam:negativeExample": defn.negative_example,
			"yam:positiveExample": defn.positive_example,
			"yam:telemetrySignatures": list(defn.telemetry_signatures),
			"yam:astDiff": defn.ast_diff,
			"yam:trainingCoverage": {
				"@value": str(_compute_coverage(defn)),
				"@type": "xsd:decimal",
			},
		}
		if defn.cwe_id:
			node["cwe:id"] = defn.cwe_id
			node["cwe:name"] = defn.cwe_name
			cwe_num = defn.cwe_id.replace("CWE-", "")
			if cwe_num.isdigit():
				node["cwe:reference"] = {"@id": f"https://cwe.mitre.org/data/definitions/{cwe_num}.html"}
		return node

	@staticmethod
	def to_jsonld(taxonomy: dict[str, BugDefinition] | None = None) -> dict:
		"""Return the full taxonomy as a JSON-LD document (Python dict).

		Pass a subset dict to export only selected categories.
		"""
		if taxonomy is None:
			taxonomy = TAXONOMY
		stats = coverage_stats(taxonomy)
		graph = [TrainingDataset._node(defn) for defn in taxonomy.values()]
		return {
			"@context": _JSONLD_CONTEXT,
			"@type": "yam:TaxonomyDataset",
			"schema:name": "YAM Agri Core Bug Taxonomy Training Dataset",
			"schema:version": "4.0",
			"schema:description": (
				"JSON-LD training dataset for the Frappe Skill auto-learning agent. "
				"Each node contains a CWE mapping, buggy/fixed code pair, "
				"telemetry signatures, and AST diff for 100% agent training coverage."
			),
			"yam:coverageStats": stats,
			"@graph": graph,
		}

	@staticmethod
	def to_jsonld_file(path: str, taxonomy: dict[str, BugDefinition] | None = None) -> dict:
		"""Serialise the taxonomy as a JSON-LD file and return the coverage stats dict."""
		data = TrainingDataset.to_jsonld(taxonomy)
		with open(path, "w", encoding="utf-8") as fh:
			json.dump(data, fh, indent=2, ensure_ascii=False)
		return data["yam:coverageStats"]


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
	# Skip test files — they intentionally contain bad patterns to validate detection
	if "test_" in os.path.basename(py_file):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	pattern = re.compile(
		r"""frappe\.throw\s*\(\s*(?!_\s*\(|frappe\._\s*\()(?:f?['"])""",
	)
	for lineno, line in enumerate(lines, 1):
		if pattern.search(line):
			report.add(
				_finding(
					severity="critical",
					rule_id="FS-001",
					bug_code="6.3.1",
					file=rel,
					line=lineno,
					message=(
						"frappe.throw() uses a raw string — not translatable. "
						"Arabic/RTL users will see English error text."
					),
				)
			)


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
				report.add(
					_finding(
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
					)
				)
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
		report.add(
			_finding(
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
			)
		)


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
		report.add(
			_finding(
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
			)
		)


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
		report.add(
			_finding(
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
			)
		)


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
			report.add(
				_finding(
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
				)
			)


def check_default_in_validate_not_before_insert(report: QCReport, py_file: str, base: str) -> None:
	"""FS-007 / 1.1.2: Default values set in validate() but not before_insert()."""
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	content = "".join(lines)
	has_before_insert = "def before_insert" in content
	has_validate = "def validate" in content
	if not has_validate or has_before_insert:
		return
	default_in_validate = re.compile(r"def validate\s*\(self[^)]*\).*?(?=def |\Z)", re.DOTALL)
	match = default_in_validate.search(content)
	if not match:
		return
	validate_block = match.group(0)
	assignment_re = re.compile(r"self\.\w+\s*=\s*['\"](\w+)['\"]")
	assignments = assignment_re.findall(validate_block)
	if assignments:
		report.add(
			_finding(
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
			)
		)


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
					report.add(
						_finding(
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
						)
					)
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
		re.search(r"""self\.get\s*\(\s*['"]lot['"]\s*\)""", content) or re.search(r"""self\.lot\b""", content)
	)
	if not has_lot:
		return
	has_check = bool(re.search(r"""frappe\.db\.get_value\s*\(\s*['"]Lot['"]""", content))
	if not has_check:
		report.add(
			_finding(
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
			)
		)


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
			report.add(
				_finding(
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
				)
			)


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
		report.add(
			_finding(
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
			)
		)
	for dt in sorted(hp_doctypes - pqc_doctypes):
		report.add(
			_finding(
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
			)
		)


# ── FS-012 / 11.1.x — Hardcoded credential patterns ──────────────────────

# Variable name prefixes that suggest credentials
_CREDENTIAL_VAR_RE = re.compile(
	r"""(?i)(password|passwd|secret|api_key|apikey|access_key|auth_key|client_secret|token|jwt)\s*=\s*['"][^'"]{3,}['"]"""
)
# Exclude obviously safe values (env-var reads, config reads, empty placeholders)
_SAFE_CREDENTIAL_RE = re.compile(
	r"""(os\.environ|frappe\.conf|getenv|env\.get|<|>|CHANGE_ME|your_|example|placeholder|xxx|test|demo)""",
	re.IGNORECASE,
)


def check_hardcoded_credentials(report: QCReport, py_file: str, base: str) -> None:
	"""FS-012 / 11.1.x: Hard-coded password, API key, or token in Python source."""
	# Skip test files — they intentionally contain fake credentials to validate detection
	if os.path.basename(py_file).startswith("test_"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		stripped = line.lstrip()
		if stripped.startswith("#"):
			continue
		match = _CREDENTIAL_VAR_RE.search(line)
		if match and not _SAFE_CREDENTIAL_RE.search(line):
			snippet = match.group(0)
			_cat, _sub, btype = _auto_classify_credential(snippet)
			# Map to the correct taxonomy code
			if btype == "Passwords":
				code = "11.1.1"
			elif btype == "API Keys":
				code = "11.1.2"
			elif btype == "Tokens":
				code = "11.1.3"
			else:
				code = "5.1.3"
			report.add(
				_finding(
					severity="critical",
					rule_id="FS-012",
					bug_code=code,
					file=rel,
					line=lineno,
					message=(
						f"Hardcoded credential detected: `{snippet[:60]}…` "
						"Treat this value as compromised and rotate it immediately."
					),
				)
			)


# ── FS-013 / 11.2.2 — Hardcoded server / IP / URL ────────────────────────

_IP_LITERAL_RE = re.compile(
	# Standard IP-octet alternation: 250-255 | 200-249 | 0-199 (leading zero accepted)
	r"""['"](?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)['"]"""
)
_LOCALHOST_RE = re.compile(r"""['"](?:localhost|127\.0\.0\.1)['"]""")


def check_hardcoded_server_config(report: QCReport, py_file: str, base: str) -> None:
	"""FS-013 / 11.2.2: Hardcoded IP addresses or localhost in non-test, non-example files."""
	# Skip env example and test files
	fname = os.path.basename(py_file)
	if fname.startswith("test_") or fname.endswith(".example"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		if line.lstrip().startswith("#"):
			continue
		if _IP_LITERAL_RE.search(line) or _LOCALHOST_RE.search(line):
			report.add(
				_finding(
					severity="high",
					rule_id="FS-013",
					bug_code="11.2.2",
					file=rel,
					line=lineno,
					message=(
						"Hardcoded server address (IP or localhost) detected. "
						"The code will break when deployed to staging or production."
					),
				)
			)


# ── FS-014 / 11.2.1 — Hardcoded DB connection strings ────────────────────

_DB_URL_RE = re.compile(
	r"""['"](?:mysql|mariadb|postgresql|postgres|sqlite)://[^'"]{4,}['"]""",
	re.IGNORECASE,
)
_DB_HOST_RE = re.compile(
	r"""(?i)(?:db_host|db_name|database_url|connection_string)\s*=\s*['"][^'"]{3,}['"]"""
)


def check_hardcoded_db_config(report: QCReport, py_file: str, base: str) -> None:
	"""FS-014 / 11.2.1: Hardcoded database URL or host in Python source."""
	fname = os.path.basename(py_file)
	if fname.startswith("test_"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		if line.lstrip().startswith("#"):
			continue
		if _DB_URL_RE.search(line) or _DB_HOST_RE.search(line):
			if not _SAFE_CREDENTIAL_RE.search(line):
				report.add(
					_finding(
						severity="high",
						rule_id="FS-014",
						bug_code="11.2.1",
						file=rel,
						line=lineno,
						message=(
							"Hardcoded database connection string or host detected. "
							"Production DB credentials will be exposed in version control."
						),
					)
				)


# ── FS-015 / 11.3.1 — Hardcoded business-logic values ────────────────────

_BIZ_LOGIC_RE = re.compile(
	r"""(?i)(?:tax_rate|vat_rate|discount_pct|shipping_fee|trial_days|max_upload_mb|rate_limit)\s*=\s*\d"""
)


def check_hardcoded_business_logic(report: QCReport, py_file: str, base: str) -> None:
	"""FS-015 / 11.3.1: Hardcoded business-rule values (tax, discount, trial period, etc.)."""
	fname = os.path.basename(py_file)
	if fname.startswith("test_"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		if line.lstrip().startswith("#"):
			continue
		if _BIZ_LOGIC_RE.search(line):
			report.add(
				_finding(
					severity="medium",
					rule_id="FS-015",
					bug_code="11.3.1",
					file=rel,
					line=lineno,
					message=(
						"Hardcoded business-rule value detected (tax rate, discount, "
						"upload limit, etc.). Business rules change; they must be "
						"configurable via a Settings DocType or environment variable."
					),
				)
			)


# ── FS-016 / 11.2.3 — Hardcoded cloud resource identifiers ───────────────

_CLOUD_RE = re.compile(
	r"""(?i)(?:s3_bucket|bucket_name|aws_region|cloud_endpoint|iam_role)\s*=\s*['"][^'"]{3,}['"]"""
)
_REGION_LITERAL_RE = re.compile(
	r"""['"](?:us-east-[12]|us-west-[12]|eu-west-[123]|ap-southeast-[12]|me-south-1)['"]"""
)


def check_hardcoded_cloud_config(report: QCReport, py_file: str, base: str) -> None:
	"""FS-016 / 11.2.3: Hardcoded cloud resource name or region identifier."""
	fname = os.path.basename(py_file)
	if fname.startswith("test_"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		if line.lstrip().startswith("#"):
			continue
		if _CLOUD_RE.search(line) or _REGION_LITERAL_RE.search(line):
			if not _SAFE_CREDENTIAL_RE.search(line):
				report.add(
					_finding(
						severity="medium",
						rule_id="FS-016",
						bug_code="11.2.3",
						file=rel,
						line=lineno,
						message=(
							"Hardcoded cloud resource identifier (bucket, region, IAM role) "
							"detected. Different environments must use different resources."
						),
					)
				)


# ── FS-017 / 12.5.2 — Master DocType missing audit trail ─────────────────


def check_master_doctype_audit_trail(report: QCReport, json_file: str, base: str) -> None:
	"""FS-017 / 12.5.2: Master DocType without track_changes and no naming_series."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	if not data.get("fields"):
		return
	field_names = {f.get("fieldname") for f in data.get("fields", [])}
	# Master DocTypes: have fields but NO naming_series (not a transaction DocType)
	if "naming_series" in field_names:
		return  # transaction DocType — handled by FS-005
	# Must have a 'site' field to be in scope (i.e. a YAM custom master)
	if "site" not in field_names:
		return
	rel = _rel(json_file, base)
	dt_name = data.get("name", json_file)
	if not data.get("track_changes"):
		report.add(
			_finding(
				severity="medium",
				rule_id="FS-017",
				bug_code="12.5.2",
				file=rel,
				line=None,
				message=(
					f"Master DocType '{dt_name}': track_changes not enabled. "
					"Unauthorized edits to master data cannot be detected — "
					"a HACCP/ISO 22000 governance failure."
				),
			)
		)


# ── FS-018 / 12.1.2 — Master DocType missing required attributes ──────────


def check_master_doctype_required_fields(report: QCReport, json_file: str, base: str) -> None:
	"""FS-018 / 12.1.2: Master DocType with site field but no status/is_active field."""
	data = _load_json(json_file)
	if not data or not isinstance(data, dict) or data.get("doctype") != "DocType":
		return
	field_names = {f.get("fieldname") for f in data.get("fields", [])}
	if "naming_series" in field_names:
		return  # transaction — skip
	if "site" not in field_names:
		return
	rel = _rel(json_file, base)
	dt_name = data.get("name", json_file)
	# Every master that can become "stale" should have a lifecycle status field
	if not any(fn in field_names for fn in ("status", "is_active", "enabled", "disabled")):
		report.add(
			_finding(
				severity="low",
				rule_id="FS-018",
				bug_code="12.1.2",
				file=rel,
				line=None,
				message=(
					f"Master DocType '{dt_name}' has no lifecycle status field "
					"(status / is_active / enabled). Obsolete master records "
					"cannot be deactivated without deleting them."
				),
			)
		)


# ── FS-019 / 11.3.3 — Hardcoded feature flags / role checks ─────────────

_FEATURE_FLAG_RE = re.compile(
	r"""(?i)(?:is_beta|is_experimental|show_feature|enable_|disable_)\s*=\s*(?:True|False|1|0)\b"""
)
_INLINE_ROLE_CHECK_RE = re.compile(r"""frappe\.session\.user\s*==\s*['"](?!Administrator)[^'"]+['"]""")


def check_hardcoded_feature_flags(report: QCReport, py_file: str, base: str) -> None:
	"""FS-019 / 11.3.3: Hardcoded feature toggle or inline user/role check."""
	fname = os.path.basename(py_file)
	if fname.startswith("test_"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		if line.lstrip().startswith("#"):
			continue
		if _FEATURE_FLAG_RE.search(line):
			report.add(
				_finding(
					severity="low",
					rule_id="FS-019",
					bug_code="11.3.3",
					file=rel,
					line=lineno,
					message=(
						"Hardcoded feature flag (True/False/1/0) detected. "
						"Feature toggles should be driven by a System Setting or "
						"custom DocType field, not hardcoded in source."
					),
				)
			)
		elif _INLINE_ROLE_CHECK_RE.search(line):
			report.add(
				_finding(
					severity="medium",
					rule_id="FS-019",
					bug_code="11.3.3",
					file=rel,
					line=lineno,
					message=(
						"Inline user-identity check detected "
						"(frappe.session.user == 'specific@email'). "
						"Use frappe.has_role('Role Name') for role-based access control."
					),
				)
			)


# ── FS-020 / Auto-learning — unclassified suspicious patterns ─────────────

# Patterns that are suspicious but don't fit the above checks;
# the agent proposes new rules for them.
_AUTO_LEARN_PATTERNS: list[tuple[re.Pattern, str, str, str, str]] = [
	# (pattern, category, subcategory, bug_type, description)
	(
		re.compile(r"""(?i)cors_origins?\s*=\s*['"]\*['"]"""),
		"Hardcoded Bugs",
		"Hardcoded Environment & Config",
		"Server",
		"Wildcard CORS origin detected — allows any domain to call the API",
	),
	(
		re.compile(r"""(?i)debug\s*=\s*True\b"""),
		"Security Bugs",
		"Data Protection",
		"Insecure storage",
		"DEBUG=True may expose tracebacks and sensitive data to end-users",
	),
	(
		re.compile(r"""(?i)ssl_verify\s*=\s*False\b|verify\s*=\s*False\b"""),
		"Security Bugs",
		"Authentication",
		"Token leakage",
		"SSL verification disabled — man-in-the-middle attacks become possible",
	),
	(
		re.compile(r"""(?i)allow_all_origins\s*=\s*True\b"""),
		"Hardcoded Bugs",
		"Hardcoded Environment & Config",
		"Server",
		"allow_all_origins=True disables CORS protection entirely",
	),
	# This pattern maps to a Concurrency category not yet in TAXONOMY;
	# it will generate a LearnedRule (auto-learning) rather than a QCFinding.
	(
		re.compile(r"""(?i)threading\.Thread\s*\("""),
		"Concurrency Bugs",
		"Threading",
		"Thread leaks",
		"Direct threading.Thread creation detected — ensure proper lifecycle management to prevent leaks",
	),
]


def check_auto_learn_patterns(report: QCReport, py_file: str, base: str) -> None:
	"""FS-020: Detect suspicious patterns not covered by other rules and propose new types."""
	# Skip test files — they intentionally contain bad patterns to validate detection
	if os.path.basename(py_file).startswith("test_"):
		return
	lines = _read_lines(py_file)
	rel = _rel(py_file, base)
	for lineno, line in enumerate(lines, 1):
		if line.lstrip().startswith("#"):
			continue
		for pattern, cat, sub, btype, desc in _AUTO_LEARN_PATTERNS:
			if pattern.search(line):
				snippet = line.strip()[:80]
				# Check if we already have a taxonomy entry matching this signature
				existing = next(
					(d for d in TAXONOMY.values() if d.category == cat and d.bug_type == btype),
					None,
				)
				if existing:
					# Emit a regular finding using the existing taxonomy
					report.add(
						_finding(
							severity="high",
							rule_id="FS-020",
							bug_code=existing.code,
							file=rel,
							line=lineno,
							message=f"{desc} — `{snippet}`",
						)
					)
				else:
					# Propose a new rule (auto-learning)
					learned = propose_bug_type(
						observed_pattern=snippet,
						file=rel,
						line=lineno,
						suggested_category=cat,
						suggested_subcategory=sub,
						suggested_bug_type=btype,
						proposed_message=desc,
						proposed_planned_response=[
							"Step 1: Identify all occurrences of this pattern in the codebase",
							"Step 2: Determine the correct fix based on context",
							"Step 3: Add a targeted check to the QC agent for future scans",
							"Step 4: Register this proposed rule via register_bug_type() if confirmed",
						],
						confidence="high",
					)
					report.add_learned(learned)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_qc(app_path: str, scope: str = "all") -> QCReport:
	"""Run QC checks on the given app path and return a QCReport.

	scope:
	- "all": server + client checks (default)
	- "server": Python + hooks parity checks only
	- "client": JavaScript + DocType JSON checks only
	"""
	report = QCReport(app_path=app_path)
	base = app_path

	py_files = _iter_python_files(app_path)
	json_files = _iter_json_files(app_path)
	js_files = _iter_js_files(app_path)

	if scope in ("all", "server"):
		for py_file in py_files:
			check_missing_translations(report, py_file, base)
			check_hardcoded_emails(report, py_file, base)
			check_default_in_validate_not_before_insert(report, py_file, base)
			check_broad_except(report, py_file, base)
			check_missing_cross_site_lot_validation(report, py_file, base)
			check_ai_writes_frappe(report, py_file, base)
			check_hardcoded_credentials(report, py_file, base)
			check_hardcoded_server_config(report, py_file, base)
			check_hardcoded_db_config(report, py_file, base)
			check_hardcoded_business_logic(report, py_file, base)
			check_hardcoded_cloud_config(report, py_file, base)
			check_hardcoded_feature_flags(report, py_file, base)
			check_auto_learn_patterns(report, py_file, base)

		hooks_candidates = [
			os.path.join(app_path, "hooks.py"),
			os.path.join(app_path, "..", "hooks.py"),
		]
		for hf in hooks_candidates:
			if os.path.exists(hf):
				check_perm_query_has_permission_parity(hf, report, base)
				break

	if scope in ("all", "client"):
		for js_file in js_files:
			check_missing_js_translations(report, js_file, base)

		for json_file in json_files:
			check_doctype_json_site_required(report, json_file, base)
			check_doctype_json_title_field(report, json_file, base)
			check_doctype_json_track_changes(report, json_file, base)
			check_master_doctype_audit_trail(report, json_file, base)
			check_master_doctype_required_fields(report, json_file, base)

	order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
	report.findings.sort(key=lambda f: (order.get(f.severity, 99), f.file, f.line or 0))
	return report


def append_daily_list(report: QCReport, output_path: str, scope: str) -> None:
	"""Append a dated QC findings list to a markdown file for daily tracking."""
	parent = os.path.dirname(output_path)
	if parent:
		os.makedirs(parent, exist_ok=True)

	summary = report.to_dict()["summary"]
	today = date.today().isoformat()
	lines = [
		f"## {today} — Frappe Skill Agent ({scope})",
		f"- Result: {'PASSED' if report.passed() else 'FAILED'}",
		(
			"- Findings: "
			f"total={summary['total']} critical={summary['critical']} high={summary['high']} "
			f"medium={summary['medium']} low={summary['low']}"
		),
	]

	if report.findings:
		lines.append("- List:")
		for finding in report.findings:
			location = f"{finding.file}:{finding.line}" if finding.line else finding.file
			lines.append(f"  - [{finding.severity.upper()}] {finding.rule_id} {location} — {finding.message}")
	else:
		lines.append("- List: No findings.")

	lines.append("")

	with open(output_path, "a", encoding="utf-8") as handle:
		handle.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def print_text_report(report: QCReport, *, verbose: bool = False) -> None:
	s = report.to_dict()["summary"]
	cov = s.get("taxonomy_coverage", {})
	print(f"\n{'=' * 72}")
	print("  Frappe Skill QC Agent — Report")
	print(f"  App path : {report.app_path}")
	print(f"  Result   : {'✅ PASSED' if report.passed() else '❌ FAILED'}")
	print(
		f"  Findings : {s['total']} total  "
		f"(critical:{s['critical']}  high:{s['high']}  "
		f"medium:{s['medium']}  low:{s['low']})"
	)
	if cov:
		cov_icon = "✅" if cov.get("coverage_pct", 0) >= 100 else "⚠️"
		print(
			f"  Training : {cov_icon} {cov.get('coverage_pct', 0):.1f}% full coverage  "
			f"({cov.get('full_coverage', 0)}/{cov.get('total', 0)} definitions, "
			f"avg score {cov.get('avg_score', 0):.3f})"
		)
	if s["learned_rules_proposed"]:
		print(
			f"  Auto-learned: {s['learned_rules_proposed']} new rule(s) proposed (use --save-learned to persist)"
		)
	print(f"{'=' * 72}\n")

	if not report.findings:
		print("No issues found.\n")
	else:
		for f in report.findings:
			loc = f"{f.file}:{f.line}" if f.line else f.file
			sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(f.severity, "⚪")
			print(f"{sev_icon} [{f.rule_id} / {f.bug_code}] {f.severity.upper()}  {loc}")
			print(f"   Classification : {f.category} › {f.subcategory} › {f.bug_type}")
			defn = TAXONOMY.get(f.bug_code)
			if defn and defn.cwe_id:
				print(f"   CWE            : {defn.cwe_id} — {defn.cwe_name}")
			print(f"   Finding        : {f.message}")
			if verbose or f.severity in ("critical", "high"):
				print("   📋 Planned Response:")
				for step in f.planned_response:
					print(f"      {step}")
				if verbose and defn and defn.negative_example:
					print("   ❌ Buggy pattern:")
					for line in defn.negative_example.splitlines():
						print(f"      {line}")
					print("   ✅ Fixed pattern:")
					for line in defn.positive_example.splitlines():
						print(f"      {line}")
			print()

	if report.learned_rules:
		print(f"{'─' * 72}")
		print(f"  🤖 Auto-Learned Rules ({len(report.learned_rules)} proposed)")
		print(f"{'─' * 72}\n")
		for lr in report.learned_rules:
			conf_icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(lr.confidence, "⚪")
			loc = f"{lr.file}:{lr.line}" if lr.line else lr.file
			print(f"{conf_icon} [PROPOSED / {lr.suggested_code}] {lr.confidence.upper()} confidence  {loc}")
			print(
				f"   Category  : {lr.suggested_category} › {lr.suggested_subcategory} › {lr.suggested_bug_type}"
			)
			print(f"   Pattern   : {lr.observed_pattern}")
			print(f"   Message   : {lr.proposed_message}")
			if verbose:
				print("   📋 Proposed Response:")
				for step in lr.proposed_planned_response:
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
		"--scope",
		choices=["all", "server", "client"],
		default="all",
		help="Scan scope: all (default), server (Python/hooks), or client (JS/DocType JSON)",
	)
	parser.add_argument(
		"--verbose",
		action="store_true",
		help="Show planned response steps for every finding (default: only for critical/high)",
	)
	parser.add_argument(
		"--save-learned",
		metavar="PATH",
		help="Save auto-learned rule proposals to a JSON file for review",
	)
	parser.add_argument(
		"--load-taxonomy",
		metavar="PATH",
		help="Load additional BugDefinitions from a JSON file (extends the taxonomy registry)",
	)
	parser.add_argument(
		"--export-training-data",
		metavar="PATH",
		help=(
			"Export the full bug taxonomy as a JSON-LD training dataset to PATH. "
			"The dataset includes CWE IDs, negative/positive code pairs, "
			"telemetry signatures, and AST diffs for every bug type."
		),
	)
	parser.add_argument(
		"--daily-list",
		metavar="PATH",
		help="Append a dated markdown findings list to PATH (useful for once-daily server checks)",
	)
	args = parser.parse_args()

	# Load external taxonomy extensions before scanning
	if args.load_taxonomy:
		try:
			loaded = load_taxonomy_from_file(args.load_taxonomy)
			print(f"Loaded {len(loaded)} custom bug type(s) from {args.load_taxonomy}", file=sys.stderr)
		except ValueError as exc:
			print(f"Error: {exc}", file=sys.stderr)
			return 2

	app_path = os.path.realpath(args.app_path)
	if not os.path.isdir(app_path):
		print(f"Error: app-path does not exist: {app_path}", file=sys.stderr)
		return 2

	report = run_qc(app_path, scope=args.scope)

	if args.format == "json":
		print_json_report(report)
	else:
		print_text_report(report, verbose=args.verbose)

	# Export training dataset if requested
	if args.export_training_data:
		stats = TrainingDataset.to_jsonld_file(args.export_training_data)
		print(
			f"\n📚 Training dataset exported to {args.export_training_data}  "
			f"({stats['total']} definitions, "
			f"{stats['coverage_pct']:.1f}% full coverage, "
			f"avg score {stats['avg_score']:.3f})",
			file=sys.stderr,
		)

	# Save learned rules if requested
	if args.save_learned and report.learned_rules:
		save_learned_rules(report.learned_rules, args.save_learned)
		print(f"\nSaved {len(report.learned_rules)} learned rule(s) to {args.save_learned}", file=sys.stderr)
	elif args.save_learned:
		print("\nNo new rules to save.", file=sys.stderr)

	if args.daily_list:
		append_daily_list(report, args.daily_list, args.scope)
		print(f"\nDaily findings list appended to {args.daily_list}", file=sys.stderr)

	return 0 if report.passed() else 1


if __name__ == "__main__":
	sys.exit(main())
