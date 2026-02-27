# Frappe Skill Agent — Developer Guide

> **Version:** v4 · **File:** `tools/frappe_skill_agent.py`
> **Maintained by:** YAM Agri Core team
> **Last updated:** 2026-02-24

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Architecture](#3-architecture)
4. [CLI Reference](#4-cli-reference)
5. [Rule Reference (FS-001 – FS-020)](#5-rule-reference)
6. [Bug Taxonomy Reference](#6-bug-taxonomy-reference)
7. [Training Data Fields & JSON-LD](#7-training-data-fields--json-ld)
8. [Python API Reference](#8-python-api-reference)
9. [How to Add a New Rule](#9-how-to-add-a-new-rule)
10. [How to Extend the Taxonomy](#10-how-to-extend-the-taxonomy)
11. [Auto-Learning Pipeline](#11-auto-learning-pipeline)
12. [Training Coverage](#12-training-coverage)
13. [Testing Guide](#13-testing-guide)
14. [Contribution Checklist](#14-contribution-checklist)
15. [Roadmap](#15-roadmap)

---

## 1. Overview

The **Frappe Skill Agent** is a pure-Python, zero-dependency static analysis
tool that scans a Frappe app directory for bugs and deviations from Frappe best
practices. It requires **no running Frappe instance** — it works on source
files only.

### What it detects

| Layer | Examples |
|-------|---------|
| **Python (.py)** | Missing `_()` i18n wrappers, hardcoded credentials, AI module writing to DB, broad `except` clauses, missing cross-site validation |
| **DocType JSON** | Missing `site` field, missing `title_field`, `track_changes` disabled, missing audit fields on master DocTypes |
| **JavaScript (.js)** | User-visible strings not wrapped in `__()` |
| **hooks.py** | `permission_query_conditions` / `has_permission` out of sync |

### Design principles

- **Taxonomy-first:** every finding has a 3-level code (`category.subcategory.type`),
  a CWE ID, and a full remediation plan.
- **Training-data complete:** every taxonomy entry carries a negative/positive code
  pair, telemetry signatures, and an AST diff so the agent can learn from examples.
- **Auto-learning:** patterns not covered by existing rules are proposed as new
  `LearnedRule` definitions and can be promoted to permanent entries.
- **Zero dependencies:** pure Python 3.11 stdlib — no install step needed.
- **CI-first:** exit code `0`/`1`/`2` integrates directly with GitHub Actions.

---

## 2. Quick Start

```bash
# From repo root — scan the default app path
python tools/frappe_skill_agent.py

# Scan a different Frappe app
python tools/frappe_skill_agent.py --app-path path/to/your/frappe_app

# Machine-readable JSON output (for CI dashboards)
python tools/frappe_skill_agent.py --format json

# Show code pairs (negative/positive) for every finding
python tools/frappe_skill_agent.py --verbose

# Export the full training dataset as JSON-LD
python tools/frappe_skill_agent.py --export-training-data /tmp/training.jsonld.json

# Save auto-learned rules for review
python tools/frappe_skill_agent.py --save-learned proposals.json

# Load previously reviewed rules into the taxonomy
python tools/frappe_skill_agent.py --load-taxonomy approved.json

# Server-side only scan (Python + hooks)
python tools/frappe_skill_agent.py --scope server

# Append a dated daily findings list (recommended for daily server review)
python tools/frappe_skill_agent.py --scope server --daily-list artifacts/evidence/qc_daily/server_qc_daily.md
```

**Exit codes:** `0` = passed (no critical/high findings); `1` = failed; `2` = configuration error.

### Typical CI step (GitHub Actions)

```yaml
- name: Frappe Skill QC
  run: python tools/frappe_skill_agent.py --format json > qc-report.json
  # Fails the job on exit code 1 (critical or high findings present)
```

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        frappe_skill_agent.py                         │
│                                                                      │
│  ┌──────────────┐   ┌──────────────────────────────────────────────┐ │
│  │   TAXONOMY   │   │                  Rule Checks                  │ │
│  │  (registry)  │   │  check_missing_translations()  FS-001        │ │
│  │              │   │  check_missing_js_translations() FS-002      │ │
│  │  BugDefinition  │  check_doctype_json_site_required() FS-003   │ │
│  │  ├ code       │   │  check_doctype_json_title_field() FS-004    │ │
│  │  ├ cwe_id     │   │  check_doctype_json_track_changes() FS-005  │ │
│  │  ├ negative_  │   │  check_hardcoded_emails()      FS-006       │ │
│  │  │  example   │   │  check_default_in_validate_() FS-007        │ │
│  │  ├ positive_  │   │  check_broad_except()          FS-008       │ │
│  │  │  example   │   │  check_missing_cross_site_()  FS-009        │ │
│  │  ├ telemetry_ │   │  check_ai_writes_frappe()      FS-010       │ │
│  │  │  signatures│   │  check_perm_query_()           FS-011       │ │
│  │  └ ast_diff   │   │  check_hardcoded_credentials() FS-012       │ │
│  └──────────────┘   │  check_hardcoded_server_config() FS-013     │ │
│                      │  check_hardcoded_db_config()  FS-014        │ │
│  ┌──────────────┐   │  check_hardcoded_business_()  FS-015        │ │
│  │  Auto-Learn  │   │  check_hardcoded_cloud_()     FS-016        │ │
│  │              │   │  check_master_doctype_audit_() FS-017       │ │
│  │ propose_     │   │  check_master_doctype_req_()  FS-018        │ │
│  │  bug_type()  │   │  check_hardcoded_feature_()   FS-019        │ │
│  │              │   │  check_auto_learn_patterns()  FS-020        │ │
│  │ LearnedRule  │   └──────────────────────────────────────────────┘ │
│  └──────────────┘                      │                             │
│                                        ▼                             │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  run_qc(app_path) → QCReport                                   │  │
│  │  ├ findings: list[QCFinding]  (sorted: critical→high→med→low)  │  │
│  │  └ learned_rules: list[LearnedRule]                            │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                        │                             │
│           ┌────────────────────────────┴──────────────────┐         │
│           ▼                                               ▼         │
│  print_text_report()                         print_json_report()    │
│  TrainingDataset.to_jsonld_file()                                   │
└──────────────────────────────────────────────────────────────────────┘
```

### File-scanning pipeline

```
app_path/
├── **/*.py   → check_missing_translations, check_hardcoded_*, ...
├── **/*.js   → check_missing_js_translations
├── **/*.json → check_doctype_json_*, check_master_doctype_*
└── hooks.py  → check_perm_query_has_permission_parity
```

Each check function receives the file path, the `QCReport` to append to, and
`base` (the app root used to produce relative paths in findings).

---

## 4. CLI Reference

```
usage: frappe_skill_agent.py [--app-path PATH] [--format {text,json}]
                              [--scope {all,server,client}]
                              [--verbose]
                              [--save-learned PATH] [--load-taxonomy PATH]
                              [--export-training-data PATH]
                              [--daily-list PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--app-path PATH` | auto-detected | Root of the inner Frappe Python package to scan |
| `--format {text,json}` | `text` | Output format. `json` emits a single JSON document to stdout |
| `--scope {all,server,client}` | `all` | Scan all checks, server-side checks only (Python/hooks), or client-side checks only (JS/DocType JSON) |
| `--verbose` | off | Show remediation steps + buggy/fixed code for **every** finding (default: only critical/high) |
| `--save-learned PATH` | — | Write auto-learned rule proposals to `PATH` as JSON |
| `--load-taxonomy PATH` | — | Load additional `BugDefinition` entries from `PATH` and add them to the registry before scanning |
| `--export-training-data PATH` | — | Serialise the full taxonomy as a JSON-LD training dataset to `PATH` |
| `--daily-list PATH` | — | Append a dated markdown findings list to `PATH` for once-daily tracking |

### Text report anatomy

```
========================================================================
  Frappe Skill QC Agent — Report
  App path : apps/yam_agri_core/yam_agri_core/yam_agri_core
  Result   : ❌ FAILED
  Findings : 60 total  (critical:3  high:3  medium:45  low:9)
  Training : ✅ 100.0% full coverage  (44/44 definitions, avg score 1.000)
========================================================================

🔴 [FS-010 / 5.2.2] CRITICAL  ai/agr_cereal_001.py:74
   Classification : Security Bugs › Authorization › Privilege escalation
   CWE            : CWE-269 — Improper Privilege Management
   Finding        : frappe.get_doc().save() called from ai/ module
   📋 Planned Response:
      Step 1: Remove all frappe.get_doc/save/insert/submit calls from the ai/ module
      ...
   ❌ Buggy pattern:        (--verbose only)
      import frappe
      doc.save()
   ✅ Fixed pattern:
      # no frappe import; pure Python
      return {'top': sorted(varieties, key=score_fn)[0]}
```

### JSON report anatomy

```json
{
  "app_path": "...",
  "summary": {
    "total": 60,
    "critical": 3,
    "high": 3,
    "medium": 45,
    "low": 9,
    "passed": false,
    "learned_rules_proposed": 2,
    "taxonomy_coverage": {
      "total": 44,
      "full_coverage": 44,
      "coverage_pct": 100.0,
      "avg_score": 1.0
    }
  },
  "findings": [
    {
      "severity": "critical",
      "rule_id": "FS-010",
      "bug_code": "5.2.2",
      "category": "Security Bugs",
      "subcategory": "Authorization",
      "bug_type": "Privilege escalation",
      "cwe_id": "CWE-269",
      "cwe_name": "Improper Privilege Management",
      "training_coverage": 1.0,
      "file": "ai/agr_cereal_001.py",
      "line": 74,
      "message": "frappe.get_doc().save() called from ai/ module",
      "planned_response": ["Step 1: ...", "Step 2: ..."]
    }
  ],
  "learned_rules": []
}
```

---

## 5. Rule Reference

All 20 rules, their taxonomy codes, severities, and the file types they analyse.

| Rule ID | Taxonomy Code | Severity | File | Description |
|---------|--------------|----------|------|-------------|
| **FS-001** | 6.3.1 | medium | `.py` | `frappe.throw()` with raw string not wrapped in `_()` |
| **FS-002** | 6.3.1 | medium | `.js` | User-visible string not wrapped in `__()` |
| **FS-003** | 1.1.1 | medium | `.json` | DocType `site` field not marked `reqd: 1` |
| **FS-004** | 6.1.4 | low | `.json` | DocType missing `title_field` |
| **FS-005** | 2.3.3 | medium | `.json` | Transaction DocType missing `track_changes: 1` |
| **FS-006** | 5.3.3 | high | `.py` | Hardcoded email or credential in non-test Python file |
| **FS-007** | 1.1.2 | medium | `.py` | Default field value set in `validate()` but not `before_insert()` |
| **FS-008** | 2.2.4 | medium | `.py` | Broad `except Exception: return []` swallowing errors silently |
| **FS-009** | 5.2.4 | high | `.py` | DocType with `lot` field but no cross-site `lot.site` check |
| **FS-010** | 5.2.2 | critical | `.py` | AI module (`ai/`) calls Frappe write API (`save/insert/submit`) |
| **FS-011** | 5.2.3 + 10.1.1 | critical | `hooks.py` | `permission_query_conditions` / `has_permission` out of sync |
| **FS-012** | 11.1.x | critical | `.py` | Hardcoded password, API key, or token |
| **FS-013** | 11.2.2 | medium | `.py` | Hardcoded IP address, hostname, or URL |
| **FS-014** | 11.2.1 | high | `.py` | Hardcoded database connection string |
| **FS-015** | 11.3.1 | medium | `.py` | Hardcoded business-rule value (tax rate, discount, trial period) |
| **FS-016** | 11.2.3 | medium | `.py` | Hardcoded cloud resource identifier (S3 bucket, region, ARN) |
| **FS-017** | 12.5.2 | medium | `.json` | Master DocType without `track_changes` and no `naming_series` |
| **FS-018** | 12.1.2 | low | `.json` | Master DocType with `site` field but no `status` / `is_active` field |
| **FS-019** | 11.3.3 | medium | `.py` | Hardcoded feature flag or inline user/role check |
| **FS-020** | auto | medium | `.py` | Auto-learned: suspicious pattern not covered by FS-001 to FS-019 |

### Rule detail cards

---

#### FS-001 — Missing Python translation wrapper

- **Taxonomy:** `6.3.1` · UI/UX Bugs › Interaction › Unclear error messages
- **CWE:** CWE-116 Improper Encoding or Escaping of Output
- **File type:** `.py` (skips `test_*.py`)
- **Pattern detected:** `frappe.throw("…")` where the string is **not** wrapped in `_()`
- **Why it matters:** Arabic users see untranslated English errors; `bench update-translations` cannot discover un-wrapped strings.

```python
# ❌ Buggy
frappe.throw("Site is required")

# ✅ Fixed
frappe.throw(_("Site is required"), frappe.ValidationError)
```

---

#### FS-002 — Missing JavaScript translation wrapper

- **Taxonomy:** `6.3.1` · UI/UX Bugs › Interaction › Unclear error messages
- **File type:** `.js`
- **Pattern detected:** `frappe.msgprint("…")` / `frappe.confirm("…")` without `__()`

```javascript
// ❌ Buggy
frappe.msgprint("Record saved");

// ✅ Fixed
frappe.msgprint(__("Record saved"));
```

---

#### FS-003 — Site field not required in DocType JSON

- **Taxonomy:** `1.1.1` · Functional Bugs › Input Handling › Missing required field validation
- **File type:** `.json` (DocType definition files)
- **Pattern detected:** A field named `site` with `reqd` absent or `0`

```json
// ❌ Buggy
{"fieldname": "site", "fieldtype": "Link", "reqd": 0}

// ✅ Fixed
{"fieldname": "site", "fieldtype": "Link", "reqd": 1}
```

---

#### FS-004 — Missing title_field

- **Taxonomy:** `6.1.4` · UI/UX Bugs › Layout › Non-responsive design
- **File type:** `.json` (DocType definition files)
- **Pattern detected:** DocType JSON without a top-level `title_field` key

---

#### FS-005 — track_changes disabled on transaction DocType

- **Taxonomy:** `2.3.3` · Logical Bugs › State Management › Incorrect flag toggling
- **CWE:** CWE-778 Insufficient Logging
- **File type:** `.json` (DocType definition files)
- **Pattern detected:** DocType with `is_submittable: 1` or naming_series present, but `track_changes` absent or `0`

---

#### FS-006 — Hardcoded email in non-test Python

- **Taxonomy:** `5.3.3` · Security Bugs › Data Protection › Insecure storage
- **CWE:** CWE-312 Cleartext Storage of Sensitive Information
- **File type:** `.py` (skips `test_*.py`, `.env`, `.example`)
- **Pattern detected:** A string literal matching `user@domain.tld` format

---

#### FS-007 — Default set in validate(), not before_insert()

- **Taxonomy:** `1.1.2` · Functional Bugs › Input Handling › Incorrect default values
- **CWE:** CWE-20 Improper Input Validation
- **File type:** `.py`
- **Pattern detected:** `self.<field> = <default>` inside `def validate()` but no matching `before_insert()` in the same file

---

#### FS-008 — Silent broad except clause

- **Taxonomy:** `2.2.4` · Logical Bugs › Conditional Logic › Missing default cases
- **CWE:** CWE-390 Detection of Error Condition Without Action
- **File type:** `.py`
- **Pattern detected:** `except Exception:` with only a `return []` / `pass` body and no `frappe.log_error()`

---

#### FS-009 — Missing cross-site lot validation (IDOR)

- **Taxonomy:** `5.2.4` · Security Bugs › Authorization › Insecure direct object reference
- **CWE:** CWE-639 Authorization Bypass Through User-Controlled Key
- **File type:** `.py`
- **Pattern detected:** A class that has a `self.lot` field assignment but does not contain `frappe.db.get_value('Lot', …, 'site')` and a site comparison

---

#### FS-010 — AI module writes to Frappe DB (critical)

- **Taxonomy:** `5.2.2` · Security Bugs › Authorization › Privilege escalation
- **CWE:** CWE-269 Improper Privilege Management
- **File type:** `.py` files inside an `ai/` directory
- **Pattern detected:** `frappe.get_doc(`, `.save(`, `.insert(`, `.submit(` in `ai/` module

---

#### FS-011 — PQC/has_permission hook mismatch (critical)

- **Taxonomy:** `5.2.3 + 10.1.1` · Security Bugs + Regression Bugs
- **CWE:** CWE-284 Improper Access Control / CWE-862 Missing Authorization
- **File type:** `hooks.py`
- **Pattern detected:** A DocType key present in `permission_query_conditions` but absent from `has_permission`, or vice versa

---

#### FS-012 — Hardcoded credentials (critical)

- **Taxonomy:** `11.1.x` · Hardcoded Bugs › Hardcoded Credentials
- **CWE:** CWE-259 (passwords), CWE-798 (API keys/tokens)
- **File type:** `.py` (skips `test_*.py`, `.env.example`)
- **Pattern detected:** Assignment to a password/key/token variable with a non-empty string literal, not reading from `os.environ`/`frappe.conf`

---

#### FS-013 — Hardcoded server config

- **Taxonomy:** `11.2.2` · Hardcoded Bugs › Hardcoded Environment & Config › Server
- **CWE:** CWE-656 Reliance on Security Through Obscurity
- **Pattern detected:** String literals matching IPv4 addresses (`192.168.x.x`, `10.x.x.x`, `172.x.x.x`) or `http://localhost` in non-test, non-example files

---

#### FS-014 — Hardcoded DB connection string

- **Taxonomy:** `11.2.1` · Hardcoded Bugs › Hardcoded Environment & Config › Database
- **CWE:** CWE-312 Cleartext Storage of Sensitive Information
- **Pattern detected:** `mysql://`, `postgresql://`, `mongodb://`, `db_host =` literals

---

#### FS-015 — Hardcoded business-rule values

- **Taxonomy:** `11.3.1` · Hardcoded Bugs › Hardcoded Business Logic › Workflow
- **CWE:** CWE-656 Reliance on Security Through Obscurity
- **Pattern detected:** Variables named `tax_rate`, `vat`, `discount`, `trial_days`, etc. assigned a numeric literal

---

#### FS-016 — Hardcoded cloud resource identifiers

- **Taxonomy:** `11.2.3` · Hardcoded Bugs › Hardcoded Environment & Config › Cloud
- **CWE:** CWE-798 Use of Hard-coded Credentials
- **Pattern detected:** `S3_BUCKET =`, `AWS_REGION =`, `AZURE_`, bucket/region name patterns

---

#### FS-017 — Master DocType missing audit trail

- **Taxonomy:** `12.5.2` · Master Data Bugs › Governance & Compliance › Audit Failures
- **CWE:** CWE-778 Insufficient Logging
- **File type:** `.json` — master DocTypes (those **without** `naming_series`)
- **Pattern detected:** `track_changes` absent or `0` on a master DocType

---

#### FS-018 — Master DocType missing status field

- **Taxonomy:** `12.1.2` · Master Data Bugs › Data Completeness › Incomplete Attributes
- **File type:** `.json`
- **Pattern detected:** Master DocType with a `site` link field but no `status` or `is_active` field (needed to deactivate expired records)

---

#### FS-019 — Hardcoded feature flags / inline role check

- **Taxonomy:** `11.3.3` · Hardcoded Bugs › Hardcoded Business Logic › Feature Flags
- **CWE:** CWE-284 Improper Access Control
- **Pattern detected:** Boolean flag assignments (`ENABLE_X = True/False`) or `session.user == "email@…"` checks

---

#### FS-020 — Auto-learned (novel pattern)

- **Taxonomy:** auto-assigned under `<category>.99.<seq>`
- **Severity:** medium (by default)
- **Pattern detected:** Any of the following not already covered by FS-001 to FS-019:
  - Potential SQL injection (`frappe.db.sql(f"…")`)
  - Debug flags left on (`DEBUG = True`, `TESTING = True`)
  - Bare `os.system(` / `subprocess.call(` calls
  - Empty `except:` with `pass`
  - Potential credential in URL string (`http://user:pass@`)

---

## 6. Bug Taxonomy Reference

The agent uses a 3-level hierarchical taxonomy. Each level is separated by `.`
in the taxonomy code (e.g. `5.2.4` = category 5, subcategory 2, type 4).

### Category overview

| # | Category | Subcategories |
|---|----------|--------------|
| 1 | **Functional Bugs** | Input Handling · Workflow Errors · Feature Failures |
| 2 | **Logical Bugs** | Algorithm Errors · Conditional Logic · State Management |
| 3 | **Performance Bugs** | Speed Issues · Memory Issues · Scalability |
| 4 | **Compatibility Bugs** | OS/Device · Browser · Versioning |
| 5 | **Security Bugs** | Authentication · Authorization · Data Protection |
| 6 | **UI/UX Bugs** | Layout · Accessibility · Interaction |
| 7 | **Integration Bugs** | API Integration · Database Integration · Third-Party Services |
| 8 | **Syntax & Build Bugs** | Compilation · Runtime · Build System |
| 9 | **Concurrency Bugs** | Race Conditions · Resource Locking · Threading |
| 10 | **Regression Bugs** | Feature Breakage · UI Regression · Performance Regression |
| 11 | **Hardcoded Bugs** | Hardcoded Credentials · Hardcoded Environment & Config · Hardcoded Business Logic |
| 12 | **Master Data Bugs** | Data Completeness · Data Accuracy · Data Consistency · Referential Integrity · Governance & Compliance |

### Full taxonomy table (44 entries, v4)

| Code | Category | Subcategory | Bug Type | CWE |
|------|----------|-------------|----------|-----|
| 1.1.1 | Functional | Input Handling | Missing required field validation | CWE-20 |
| 1.1.2 | Functional | Input Handling | Incorrect default values | CWE-20 |
| 1.1.3 | Functional | Input Handling | Case sensitivity issues | CWE-178 |
| 1.1.4 | Functional | Input Handling | Special character mishandling | CWE-116 |
| 1.1.5 | Functional | Input Handling | Null/empty input crashes | CWE-476 |
| 1.2.5 | Functional | Workflow Errors | Duplicate record creation | CWE-20 |
| 1.3.1 | Functional | Feature Failures | Search returning no results | N/A |
| 2.1.5 | Logical | Algorithm Errors | Faulty recommendation logic | CWE-682 |
| 2.2.1 | Logical | Conditional Logic | Misplaced if/else | CWE-670 |
| 2.2.4 | Logical | Conditional Logic | Missing default cases | CWE-390 |
| 2.3.3 | Logical | State Management | Incorrect flag toggling | CWE-778 |
| 3.1.3 | Performance | Speed Issues | Excessive API calls (N+1) | N/A |
| 3.1.4 | Performance | Speed Issues | Unindexed DB queries | N/A |
| 4.3.2 | Compatibility | Versioning | Deprecated library usage | CWE-1104 |
| 5.1.3 | Security | Authentication | Token leakage | CWE-312 |
| 5.2.2 | Security | Authorization | Privilege escalation | CWE-269 |
| 5.2.3 | Security | Authorization | Broken access control | CWE-862 |
| 5.2.4 | Security | Authorization | Insecure direct object reference (IDOR) | CWE-639 |
| 5.3.3 | Security | Data Protection | Insecure storage | CWE-312 |
| 6.1.4 | UI/UX | Layout | Non-responsive design | N/A |
| 6.3.1 | UI/UX | Interaction | Unclear error messages | CWE-116 |
| 8.2.1 | Syntax & Build | Runtime | Null pointer exceptions | CWE-476 |
| 10.1.1 | Regression | Feature Breakage | Login system failure | CWE-284 |
| 11.1.1 | Hardcoded | Hardcoded Credentials | Passwords | CWE-259 |
| 11.1.2 | Hardcoded | Hardcoded Credentials | API Keys | CWE-798 |
| 11.1.3 | Hardcoded | Hardcoded Credentials | Tokens | CWE-798 |
| 11.2.1 | Hardcoded | Hardcoded Environment & Config | Database | CWE-312 |
| 11.2.2 | Hardcoded | Hardcoded Environment & Config | Server | CWE-656 |
| 11.2.3 | Hardcoded | Hardcoded Environment & Config | Cloud | CWE-798 |
| 11.3.1 | Hardcoded | Hardcoded Business Logic | Workflow | CWE-656 |
| 11.3.2 | Hardcoded | Hardcoded Business Logic | UI/UX | CWE-116 |
| 11.3.3 | Hardcoded | Hardcoded Business Logic | Feature Flags | CWE-284 |
| 12.1.1 | Master Data | Data Completeness | Missing Records | CWE-20 |
| 12.1.2 | Master Data | Data Completeness | Incomplete Attributes | CWE-20 |
| 12.1.3 | Master Data | Data Completeness | Orphan Records | CWE-459 |
| 12.2.1 | Master Data | Data Accuracy | Incorrect Values | CWE-682 |
| 12.2.3 | Master Data | Data Accuracy | Outdated Data | N/A |
| 12.3.1 | Master Data | Data Consistency | Cross-System Inconsistency | CWE-116 |
| 12.3.3 | Master Data | Data Consistency | Duplication | CWE-20 |
| 12.4.1 | Master Data | Referential Integrity | Broken Links | CWE-459 |
| 12.4.3 | Master Data | Referential Integrity | Foreign Key Violations | CWE-20 |
| 12.5.1 | Master Data | Governance & Compliance | Policy Violations | CWE-284 |
| 12.5.2 | Master Data | Governance & Compliance | Audit Failures | CWE-778 |
| 12.5.3 | Master Data | Governance & Compliance | Security | CWE-312 |

> **Note on N/A CWE IDs:** Performance, UX/discoverability, and data-lifecycle
> bugs do not map to a specific security weakness. These entries use `"N/A"` as
> the `cwe_id` sentinel. All 6 training-data fields are still populated so the
> coverage score remains 1.0.

---

## 7. Training Data Fields & JSON-LD

### 7.1 BugDefinition training fields

As of v4, every `BugDefinition` carries six training-data fields that together
enable an agent to learn the pattern, not just the description:

| Field | Type | Purpose |
|-------|------|---------|
| `cwe_id` | `str` | CWE identifier (`"CWE-259"`) or `"N/A"` for non-security issues |
| `cwe_name` | `str` | Human-readable CWE title |
| `negative_example` | `str` | Minimal **buggy** code snippet (the "before" in the pair) |
| `positive_example` | `str` | Minimal **fixed** code snippet (the "after" in the pair) |
| `telemetry_signatures` | `tuple[str, ...]` | Log/trace patterns that appear at runtime when this bug is present |
| `ast_diff` | `str` | Human-readable description of the AST-level structural change |

**Coverage score:** each field contributes 1/6 of the score. A score of `1.0`
(all 6 populated) is required for the agent to learn the pattern reliably.

```python
from frappe_skill_agent import _compute_coverage, coverage_stats, TAXONOMY

# Score for a single entry
score = _compute_coverage(TAXONOMY["5.2.4"])   # → 1.0

# Aggregate stats across all entries
stats = coverage_stats()
# {'total': 44, 'full_coverage': 44, 'coverage_pct': 100.0, 'avg_score': 1.0}
```

### 7.2 JSON-LD dataset format

The `TrainingDataset` class serialises the full taxonomy as a
[JSON-LD 1.1](https://json-ld.org/) document. The format is designed to be
consumable by graph databases, embedding pipelines, and ML training frameworks.

```json
{
  "@context": {
    "@vocab": "https://yam-agri.io/taxonomy/",
    "schema": "https://schema.org/",
    "yam":    "https://yam-agri.io/taxonomy/",
    "cwe":    "https://cwe.mitre.org/data/definitions/",
    "xsd":    "http://www.w3.org/2001/XMLSchema#",
    "rdfs":   "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@type": "yam:TaxonomyDataset",
  "schema:name": "YAM Agri Core Bug Taxonomy Training Dataset",
  "schema:version": "4.0",
  "yam:coverageStats": {
    "total": 44,
    "full_coverage": 44,
    "coverage_pct": 100.0,
    "avg_score": 1.0
  },
  "@graph": [
    {
      "@type": "yam:BugDefinition",
      "@id":   "yam:11.1.1",
      "yam:code":             {"@value": "11.1.1", "@type": "xsd:string"},
      "yam:category":         "Hardcoded Bugs",
      "yam:subcategory":      "Hardcoded Credentials",
      "schema:name":          "Passwords",
      "yam:predefinedMessage": "A password … hard-coded in source …",
      "yam:plannedResponse":  ["Step 1: Remove …", "Step 2: Rotate …"],
      "yam:negativeExample":  "db_password = \"P@ssw0rd123!\"",
      "yam:positiveExample":  "db_password = frappe.conf.get('db_password') or os.environ.get('DB_PASSWORD')",
      "yam:telemetrySignatures": ["git-secrets: matched pattern ******"],
      "yam:astDiff":           "Replace Assign[Name=Constant(password)] with Assign[Name=BoolOp[…]]",
      "yam:trainingCoverage":  {"@value": "1.0", "@type": "xsd:decimal"},
      "cwe:id":    "CWE-259",
      "cwe:name":  "Use of Hard-coded Password",
      "cwe:reference": {"@id": "https://cwe.mitre.org/data/definitions/259.html"}
    }
  ]
}
```

**Export:**

```bash
# Export to file via CLI
python tools/frappe_skill_agent.py --export-training-data training.jsonld.json

# Export programmatically (subset example)
from frappe_skill_agent import TrainingDataset, TAXONOMY

security = {k: v for k, v in TAXONOMY.items() if v.category == "Security Bugs"}
stats = TrainingDataset.to_jsonld_file("/tmp/security.jsonld.json", security)
# stats = {'total': 5, 'full_coverage': 5, 'coverage_pct': 100.0, 'avg_score': 1.0}
```

---

## 8. Python API Reference

### `BugDefinition` (dataclass, frozen)

```python
@dataclass(frozen=True)
class BugDefinition:
    code: str                         # e.g. "5.2.4"
    category: str                     # e.g. "Security Bugs"
    subcategory: str                  # e.g. "Authorization"
    bug_type: str                     # e.g. "Insecure direct object reference (IDOR)"
    predefined_message: str           # short diagnostic template
    planned_response: tuple[str, ...] # ordered remediation steps

    # Training-data fields (v4)
    cwe_id: str = ""
    cwe_name: str = ""
    negative_example: str = ""
    positive_example: str = ""
    telemetry_signatures: tuple[str, ...] = ()
    ast_diff: str = ""
```

### `TAXONOMY` (module-level dict)

```python
TAXONOMY: dict[str, BugDefinition]  # key = taxonomy code e.g. "5.2.4"
```

All 44 built-in entries are registered at import time. Additional entries
can be added via `register_bug_type()` or `load_taxonomy_from_file()`.

### `register_bug_type(definition)`

```python
def register_bug_type(definition: BugDefinition) -> None
```

Adds a `BugDefinition` to `TAXONOMY`. If a definition with the same code
already exists it is overwritten (safe for idempotent re-registration).

### `_td(code, category, subcategory, bug_type, message, steps, *, **training_kwargs)`

Internal helper used by the built-in taxonomy. Identical to `register_bug_type`
but accepts all training-data fields as keyword arguments. Use this when
defining new entries inline in the agent file.

### `_compute_coverage(defn)`

```python
def _compute_coverage(defn: BugDefinition) -> float
# Returns 0.0 – 1.0 (fraction of the 6 training fields that are populated)
```

### `coverage_stats(taxonomy=None)`

```python
def coverage_stats(taxonomy: dict[str, BugDefinition] | None = None) -> dict
# Returns: {'total': int, 'full_coverage': int, 'coverage_pct': float, 'avg_score': float}
```

Pass a subset dict to measure coverage for a specific category.

### `QCFinding` (dataclass)

```python
@dataclass
class QCFinding:
    severity: str            # "critical" | "high" | "medium" | "low"
    rule_id: str             # e.g. "FS-009"
    bug_code: str            # taxonomy code e.g. "5.2.4"
    category: str
    subcategory: str
    bug_type: str
    file: str                # relative path to source file
    line: int | None         # line number (None for whole-file findings)
    message: str             # specific diagnostic for this occurrence
    planned_response: tuple[str, ...]
```

### `QCReport` (dataclass)

```python
@dataclass
class QCReport:
    app_path: str
    findings: list[QCFinding]    # sorted: critical → high → medium → low
    learned_rules: list[LearnedRule]

    def add(finding: QCFinding) -> None
    def add_learned(rule: LearnedRule) -> None

    @property critical / high / medium / low: list[QCFinding]
    def passed() -> bool               # True iff no critical/high findings
    def to_dict() -> dict              # full JSON-serialisable representation
```

### `run_qc(app_path)`

```python
def run_qc(app_path: str) -> QCReport
```

Runs all 20 rule checks on every Python, JSON, and JavaScript file under
`app_path`. Returns a `QCReport` with findings sorted by severity.

### `LearnedRule` (dataclass)

```python
@dataclass
class LearnedRule:
    observed_pattern: str
    file: str
    line: int | None
    suggested_code: str       # auto-generated e.g. "5.99.1"
    suggested_category: str
    suggested_subcategory: str
    suggested_bug_type: str
    proposed_message: str
    proposed_planned_response: tuple[str, ...]
    confidence: str           # "high" | "medium" | "low"

    def to_dict() -> dict
```

### `propose_bug_type(*, observed_pattern, file, line, ...)`

```python
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
) -> LearnedRule
```

Creates a `LearnedRule` with an auto-generated `suggested_code`
(`<category_num>.99.<seq>`). Does **not** automatically register the rule
— use `register_bug_type()` after review.

### `save_learned_rules(rules, path)`

```python
def save_learned_rules(rules: list[LearnedRule], path: str) -> None
```

Writes the list as a JSON array to `path`. The format is compatible with
`load_taxonomy_from_file()` so rules can be reviewed and reloaded.

### `load_taxonomy_from_file(path)`

```python
def load_taxonomy_from_file(path: str) -> list[BugDefinition]
# Raises ValueError if file cannot be parsed
```

Loads `BugDefinition` entries from a JSON file and automatically registers
each one. Accepts both the full training-data format and the minimal format
produced by `save_learned_rules()`. All six training-data fields are preserved
if present in the file.

### `TrainingDataset`

```python
class TrainingDataset:
    @staticmethod
    def to_jsonld(taxonomy=None) -> dict
    # Returns the full JSON-LD document as a Python dict.

    @staticmethod
    def to_jsonld_file(path, taxonomy=None) -> dict
    # Writes to path and returns the coverage stats dict.
```

### Output functions

```python
def print_text_report(report: QCReport, *, verbose: bool = False) -> None
def print_json_report(report: QCReport) -> None
```

---

## 9. How to Add a New Rule

Adding a rule requires two changes: a taxonomy entry and a check function.

### Step 1 — Add a taxonomy entry

Open `tools/frappe_skill_agent.py` and find the section for the relevant
category (e.g. `# ── 5. Security Bugs`). Use `_td()` with all six
training-data fields:

```python
_td("5.4.1", "Security Bugs", "Authorization", "Missing QA Manager role check",
    "High-risk status transition (Accepted/Rejected) is not guarded by frappe.has_role()",
    [
        "Step 1: Add `if not frappe.has_role('QA Manager'): frappe.throw(...)` in validate()",
        "Step 2: Ensure the role check fires server-side, not just in JavaScript",
        "Step 3: Add a unit test that attempts the transition without the role",
    ],
    cwe_id="CWE-285",
    cwe_name="Improper Authorization",
    negative_example=(
        "def validate(self):\n"
        "    self.status = 'Accepted'  # no role check"
    ),
    positive_example=(
        "def validate(self):\n"
        "    if self.status == 'Accepted' and not frappe.has_role('QA Manager'):\n"
        "        frappe.throw(_('Only QA Manager may accept lots'), frappe.PermissionError)"
    ),
    telemetry_signatures=[
        "Lot status set to Accepted by user without QA Manager role",
        "PermissionError missing in audit log for lot acceptance",
    ],
    ast_diff=(
        "Add If[not Call[frappe.has_role]('QA Manager')] → Call[frappe.throw] "
        "before Assign[self.status='Accepted']"
    ))
```

### Step 2 — Implement the check function

Add a new `check_*` function in the `# Rule checks` section:

```python
def check_missing_qa_role_guard(report: QCReport, py_file: str, base: str) -> None:
    """FS-021 / 5.4.1: High-risk status transition missing QA Manager role check."""
    # Heuristic: look for 'Accepted' or 'Rejected' assignments without has_role
    if "test_" in os.path.basename(py_file):
        return
    lines = _read_lines(py_file)
    rel = _rel(py_file, base)
    transition_re = re.compile(r"""self\.status\s*=\s*['"](?:Accepted|Rejected)['"]""")
    role_re = re.compile(r"""has_role\s*\(""")
    # Read entire file as one string for context check
    content = "".join(lines)
    for lineno, line in enumerate(lines, 1):
        if transition_re.search(line) and not role_re.search(content):
            report.add(_finding(
                severity="high",
                rule_id="FS-021",
                bug_code="5.4.1",
                file=rel,
                line=lineno,
                message=f"Status transition to Accepted/Rejected without has_role() guard",
            ))
            break
```

### Step 3 — Wire it into `run_qc()`

In `run_qc()`, add the new check to the relevant loop:

```python
for py_file in py_files:
    # ... existing checks ...
    check_missing_qa_role_guard(report, py_file, base)   # ← add this
```

### Step 4 — Add tests

In `tests/test_frappe_skill_agent.py`, add a test class:

```python
class TestQARoleGuard(unittest.TestCase):
    def test_fs021_detects_missing_role_check(self):
        with write_temp_py("self.status = 'Accepted'\n") as path:
            findings = run_check_on_file(check_missing_qa_role_guard, path)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].rule_id, "FS-021")

    def test_fs021_passes_when_role_check_present(self):
        src = "if not frappe.has_role('QA Manager'): frappe.throw(_('…'))\nself.status = 'Accepted'\n"
        with write_temp_py(src) as path:
            findings = run_check_on_file(check_missing_qa_role_guard, path)
            self.assertEqual(findings, [])
```

### Step 5 — Verify coverage

```bash
python3 -c "
import sys; sys.path.insert(0, 'tools')
from frappe_skill_agent import coverage_stats
print(coverage_stats())
"
# {'total': 45, 'full_coverage': 45, 'coverage_pct': 100.0, 'avg_score': 1.0}
```

---

## 10. How to Extend the Taxonomy

### At runtime (programmatic)

```python
from frappe_skill_agent import register_bug_type, BugDefinition

register_bug_type(BugDefinition(
    code="7.1.1",
    category="Integration Bugs",
    subcategory="API Integration",
    bug_type="Missing retry logic",
    predefined_message="External API call has no retry or timeout handling",
    planned_response=[
        "Step 1: Wrap the call in a try/except with exponential back-off",
        "Step 2: Set a timeout using requests.get(..., timeout=10)",
        "Step 3: Log failures with frappe.log_error()",
    ],
    cwe_id="CWE-400",
    cwe_name="Uncontrolled Resource Consumption",
    negative_example="resp = requests.get(url)  # no timeout, no retry",
    positive_example="resp = requests.get(url, timeout=10)  # with timeout",
    telemetry_signatures=["requests.exceptions.ConnectionError in background job"],
    ast_diff="Add keyword arg timeout=10 to Call[requests.get]",
))
```

### From a JSON file

Create `custom_rules.json`:

```json
[
  {
    "code": "7.1.1",
    "category": "Integration Bugs",
    "subcategory": "API Integration",
    "bug_type": "Missing retry logic",
    "predefined_message": "External API call has no retry or timeout handling",
    "planned_response": ["Step 1: …", "Step 2: …"],
    "cwe_id": "CWE-400",
    "cwe_name": "Uncontrolled Resource Consumption",
    "negative_example": "resp = requests.get(url)",
    "positive_example": "resp = requests.get(url, timeout=10)",
    "telemetry_signatures": ["ConnectionError in background job"],
    "ast_diff": "Add keyword arg timeout=10 to Call[requests.get]"
  }
]
```

Load at scan time:

```bash
python tools/frappe_skill_agent.py --load-taxonomy custom_rules.json
```

Or programmatically:

```python
from frappe_skill_agent import load_taxonomy_from_file
loaded = load_taxonomy_from_file("custom_rules.json")
print(f"Loaded {len(loaded)} custom rules")
```

---

## 11. Auto-Learning Pipeline

The auto-learning pipeline (FS-020) detects suspicious patterns in Python
source that do not match any existing rule, and proposes them as new
`LearnedRule` definitions.

```
Source file
    │
    ▼
check_auto_learn_patterns()
    │  Regex patterns checked:
    │  • frappe.db.sql(f"…")      → potential SQL injection
    │  • DEBUG = True             → debug flag left on
    │  • os.system(               → shell injection risk
    │  • subprocess.call(         → shell injection risk
    │  • except:\n    pass        → swallowed exception
    │  • http://user:pass@        → credential in URL
    │
    ▼
propose_bug_type()
    │  auto-generated code: <cat>.99.<seq>
    │  confidence: "high" | "medium" | "low"
    │
    ▼
LearnedRule added to QCReport.learned_rules
    │
    ▼ (if --save-learned PATH)
save_learned_rules() → proposals.json

    REVIEW CYCLE (developer)
    │
    ▼ Promote a rule:
    1. Open proposals.json
    2. Add training-data fields (cwe_id, negative_example, etc.)
    3. Rename key "suggested_code" → "code"
    4. Save as approved.json
    │
    ▼
load_taxonomy_from_file("approved.json")
    │  → registers BugDefinition in TAXONOMY
    │  → rule fires as a first-class finding on next scan
    ▼
(Optional) Move to frappe_skill_agent.py as a permanent _td() entry
```

### Promoting a learned rule to permanent

```bash
# 1. Save all proposals
python tools/frappe_skill_agent.py --save-learned proposals.json

# 2. Review proposals.json — add training-data fields,
#    rename "suggested_code" → "code", etc.

# 3. Test the promoted rule
python tools/frappe_skill_agent.py --load-taxonomy approved.json

# 4. If the rule is working correctly, move it into frappe_skill_agent.py
#    as a _td() call in the appropriate taxonomy section.
```

---

## 12. Training Coverage

### What "100% training coverage" means

Every `BugDefinition` in the taxonomy must have all 6 training-data fields
populated. A definition with score `< 1.0` has incomplete training data and the
agent may not learn the pattern reliably.

| Score | Meaning |
|-------|---------|
| `1.0` | All 6 fields populated — agent can learn fully |
| `0.83` | 5/6 fields populated — one field missing |
| `0.17` | Only `planned_response` present — legacy entry, needs upgrading |
| `0.0` | No training data at all — agent cannot learn this pattern |

### Checking coverage

```python
from frappe_skill_agent import coverage_stats, _compute_coverage, TAXONOMY

# Global stats
print(coverage_stats())
# {'total': 44, 'full_coverage': 44, 'coverage_pct': 100.0, 'avg_score': 1.0}

# Find any entries below 1.0 (CI gate)
incomplete = [(code, _compute_coverage(d)) for code, d in TAXONOMY.items() if _compute_coverage(d) < 1.0]
assert incomplete == [], f"Incomplete training data: {incomplete}"
```

The test suite (`TestTrainingDataFields.test_all_taxonomy_entries_have_training_data`)
enforces this as an automated gate.

### N/A CWE IDs

Bugs that are purely about performance, UX discoverability, or data-lifecycle
(not security weaknesses) use `cwe_id = "N/A"`. The string `"N/A"` is truthy in
Python, so `bool("N/A") == True` and these entries still score `1.0`. The
`test_cwe_ids_are_well_formed` test allows `"N/A"` in addition to `"CWE-NNN"`.

---

## 13. Testing Guide

### Running tests

```bash
# From repo root — all agent tests (excludes Frappe integration tests)
python -m pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_frappe_skill_agent.py -v

# Quick pass/fail check
python -m pytest apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_frappe_skill_agent.py -q
```

### Test structure

```
tests/test_frappe_skill_agent.py
├── TestTaxonomyRegistry          — TAXONOMY is populated, all required codes exist
├── TestFindingFactory            — _finding() resolves metadata from TAXONOMY
├── TestMissingTranslations       — FS-001 (Python _() wrapping)
├── TestMissingJsTranslations     — FS-002 (JavaScript __() wrapping)
├── TestDoctypeJsonChecks         — FS-003, FS-004, FS-005 (DocType JSON rules)
├── TestHardcodedChecks           — FS-012 to FS-016, FS-019 (hardcoded patterns)
├── TestMasterDataChecks          — FS-017, FS-018 (master DocType rules)
├── TestAutoLearning              — FS-020, propose_bug_type, save/load lifecycle
├── TestTrainingDataFields        — _compute_coverage, coverage_stats, _td(), 100% gate
└── TestTrainingDataset           — TrainingDataset.to_jsonld(), file round-trip
```

### Writing a test for a new rule

```python
import tempfile
import os

class TestMyNewRule(unittest.TestCase):
    """Tests for FS-021 / 5.4.1: Missing QA Manager role check."""

    def _run(self, source: str) -> list[QCFinding]:
        """Write source to a temp file and run the check."""
        findings = []
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                        delete=False, prefix="lot_") as f:
            f.write(source)
            path = f.name
        try:
            report = QCReport(app_path="/tmp")
            check_missing_qa_role_guard(report, path, "/tmp")
            return report.findings
        finally:
            os.unlink(path)

    def test_detects_missing_guard(self):
        findings = self._run("self.status = 'Accepted'\n")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "FS-021")
        self.assertEqual(findings[0].severity, "high")

    def test_passes_when_guard_present(self):
        src = (
            "if not frappe.has_role('QA Manager'):\n"
            "    frappe.throw(_('Permission denied'))\n"
            "self.status = 'Accepted'\n"
        )
        findings = self._run(src)
        self.assertEqual(findings, [])

    def test_skips_test_files(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                        delete=False, prefix="test_lot_") as f:
            f.write("self.status = 'Accepted'\n")
            path = f.name
        try:
            report = QCReport(app_path="/tmp")
            check_missing_qa_role_guard(report, path, "/tmp")
            self.assertEqual(report.findings, [])
        finally:
            os.unlink(path)
```

### CI lint gate

```bash
# The agent itself must pass ruff lint
ruff check tools/frappe_skill_agent.py

# Test file also linted
ruff check apps/yam_agri_core/yam_agri_core/yam_agri_core/tests/test_frappe_skill_agent.py
```

---

## 14. Contribution Checklist

Before opening a PR that adds or changes the Frappe Skill Agent:

- [ ] **Taxonomy entry:** New bug type uses `_td()` with all 6 training-data fields (`cwe_id`, `negative_example`, `positive_example`, `telemetry_signatures`, `ast_diff`)
- [ ] **CWE ID:** Use `"CWE-NNN"` for security/logic bugs; `"N/A"` for performance/UX/data-lifecycle issues
- [ ] **Check function:** New `check_*()` function added with a clear docstring `"""FS-NNN / X.Y.Z: …"""`
- [ ] **Wired into `run_qc()`:** New check is called in the appropriate file loop
- [ ] **Tests:** At least 2 tests per rule — one positive (detects the pattern) and one negative (does not false-positive on clean code)
- [ ] **Coverage gate:** `coverage_stats()["coverage_pct"] == 100.0` after adding the entry
- [ ] **Ruff lint passes:** `ruff check tools/frappe_skill_agent.py`
- [ ] **All existing tests pass:** `python -m pytest tests/test_frappe_skill_agent.py -q`
- [ ] **Pattern pair is minimal:** Both `negative_example` and `positive_example` are the smallest possible snippet that illustrates the issue
- [ ] **AST diff is descriptive:** Describes the change at the structural level (e.g. "Add If[...] around Call[frappe.throw]"), not just "add a check"

---

## 15. Roadmap

### v5 — Planned enhancements

| Priority | Feature | Notes |
|----------|---------|-------|
| High | **FS-021** — Missing QA Manager role guard | Check for status → Accepted/Rejected without `has_role('QA Manager')` |
| High | **FS-022** — Missing `assert_site_access()` in `validate()` | Ensure every non-AI DocType controller calls `assert_site_access` |
| Medium | **FS-023** — `ignore_permissions=True` outside scheduled jobs | Flag unsafe permission bypass |
| Medium | **FS-024** — `frappe.db.sql()` with f-string or % formatting | Potential SQL injection |
| Medium | **FS-025** — `except:` with no exception type (bare except) | Swallows `KeyboardInterrupt`, `SystemExit` |
| Low | **Real AST parsing** | Replace regex-based checks with `ast.parse()` for higher precision and lower false-positive rate |
| Low | **Incremental scanning** | Only rescan files changed since the last run (git diff integration) |
| Low | **VS Code / LSP integration** | Surface findings as inline diagnostics in the editor |
| Low | **Vector similarity search** | Embed negative/positive pairs and rank findings by similarity to known bug patterns |
| Low | **Auto-promote learned rules** | When a `LearnedRule` reaches confidence `"high"` on 3+ independent files, auto-register it |

### Taxonomy gaps (categories not yet checked)

These categories exist in the taxonomy but no active rule currently fires for them.
Adding rules for each would increase the agent's detection surface:

| Category | Gap |
|----------|-----|
| **Functional — Workflow Errors (1.2.x)** | Duplicate record creation (1.2.5) — needs a check for missing `frappe.db.exists()` before insert |
| **Functional — Feature Failures (1.3.x)** | Search returning no results (1.3.1) — check for DocTypes missing from `global_search_doctypes` |
| **Logical — Algorithm Errors (2.1.x)** | Faulty recommendation logic (2.1.5) — difficult to detect statically |
| **Performance (3.x)** | N+1 queries (3.1.3), unindexed fields (3.1.4) — requires data-flow analysis |
| **Compatibility (4.x)** | Deprecated API usage (4.3.2) — needs a Frappe API deprecation list |
| **Master Data (12.x)** | Most entries detected by FS-017/FS-018; referential integrity checks need DB access |

---

*This document is generated and maintained as part of the YAM Agri Core v1.1 development cycle.
Update it whenever new rules, taxonomy entries, or architectural changes are made.*
