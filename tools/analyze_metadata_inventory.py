"""Analyze exported Frappe metadata snapshots.

Reads the CSVs produced by `yam_agri_core.yam_agri_core.metadata_export.run` and
generates a concise inventory summary to drive planning and avoid DocType/field
duplication.

Usage (from repo root):
  python tools/analyze_metadata_inventory.py
  python tools/analyze_metadata_inventory.py --export-dir docs/metadata_exports/20260223_034233
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


NO_VALUE_FIELDTYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"HTML",
	"Table",
	"Table MultiSelect",
	"Button",
	"Image",
	"Fold",
	"Heading",
}


EXPECTED_DOMAIN_DOCTYPES = [
	"Site",
	"StorageBin",
	"Device",
	"Lot",
	"Transfer",
	"ScaleTicket",
	"QCTest",
	"Certificate",
	"Nonconformance",
	"EvidencePack",
	"Complaint",
	"Observation",
]


GAP_KEYWORDS: dict[str, list[str]] = {
	"StorageBin": ["bin", "storage", "warehouse", "silo", "location"],
	"Device": ["device", "sensor", "asset", "equipment", "machine", "meter"],
	"Transfer": ["transfer", "stock entry", "material transfer", "move", "movement"],
	"ScaleTicket": ["scale", "weigh", "weight", "weighbridge", "ticket"],
	"EvidencePack": ["evidence", "attachment", "file", "document", "audit"],
	"Complaint": ["complaint", "issue", "support", "ticket", "claim"],
	"Observation": ["observation", "reading", "telemetry", "log", "sensor"],
}


@dataclass(frozen=True)
class SnapshotPaths:
	export_dir: str
	doctypes_csv: str
	docfields_csv: str
	docperms_csv: str | None
	workspaces_csv: str | None
	workspace_links_csv: str | None
	reports_csv: str | None
	workflows_csv: str | None
	workflow_transitions_csv: str | None
	custom_fields_csv: str | None
	property_setters_csv: str | None


def _read_csv(path: str) -> list[dict[str, str]]:
	with open(path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		return list(reader)


def _find_latest_snapshot_dir(base_dir: str) -> str:
	if not os.path.isdir(base_dir):
		raise SystemExit(f"metadata_exports base directory not found: {base_dir}")

	candidates: list[str] = []
	for name in os.listdir(base_dir):
		full = os.path.join(base_dir, name)
		if not os.path.isdir(full):
			continue
		if os.path.exists(os.path.join(full, "doctypes.csv")) and os.path.exists(
			os.path.join(full, "docfields.csv")
		):
			candidates.append(full)

	if not candidates:
		raise SystemExit(
			"No snapshot directories found (expected doctypes.csv + docfields.csv under docs/metadata_exports/<timestamp>/)."
		)

	# Prefer lexicographically last folder name (timestamp format) but fall back to mtime.
	try:
		return sorted(candidates)[-1]
	except Exception:
		return max(candidates, key=lambda p: os.path.getmtime(p))


def _snapshot_paths(export_dir: str) -> SnapshotPaths:
	export_dir = os.path.abspath(export_dir)

	def p(name: str) -> str:
		return os.path.join(export_dir, name)

	def maybe(name: str) -> str | None:
		path = p(name)
		return path if os.path.exists(path) else None

	doctypes_csv = p("doctypes.csv")
	docfields_csv = p("docfields.csv")
	if not os.path.exists(doctypes_csv) or not os.path.exists(docfields_csv):
		raise SystemExit(f"Snapshot missing doctypes.csv/docfields.csv: {export_dir}")

	return SnapshotPaths(
		export_dir=export_dir,
		doctypes_csv=doctypes_csv,
		docfields_csv=docfields_csv,
		docperms_csv=maybe("docperms.csv"),
		workspaces_csv=maybe("workspaces.csv"),
		workspace_links_csv=maybe("workspace_links.csv"),
		reports_csv=maybe("reports.csv"),
		workflows_csv=maybe("workflows.csv"),
		workflow_transitions_csv=maybe("workflow_transitions.csv"),
		custom_fields_csv=maybe("custom_fields.csv"),
		property_setters_csv=maybe("property_setters.csv"),
	)


def _as_bool(v: str | None) -> bool:
	return str(v).strip().lower() in {"1", "true", "yes"}


def _safe_int(v: str | None, default: int = 0) -> int:
	try:
		return int(str(v).strip())
	except Exception:
		return default


def _top(counter: Counter[str], n: int) -> list[tuple[str, int]]:
	items = counter.most_common(n)
	# Normalize empty keys for readability
	return [(k if k else "(blank)", v) for k, v in items]


def _md_table(rows: Iterable[tuple[str, int]], headers: tuple[str, str]) -> str:
	lines = [f"| {headers[0]} | {headers[1]} |", "|---|---:|"]
	for k, v in rows:
		lines.append(f"| {k} | {v} |")
	return "\n".join(lines)


def generate_inventory_summary(export_dir: str) -> str:
	paths = _snapshot_paths(export_dir)
	doctypes = _read_csv(paths.doctypes_csv)
	fields = _read_csv(paths.docfields_csv)
	# look for classification columns in raw doctypes (they may have been
	# added by tooling such as generate_master_data_workbook)
	stage_missing = [d.get("name") for d in doctypes if not d.get("Supply_Chain_Stage")]
	proc_missing = [d.get("name") for d in doctypes if not d.get("E2E_Process")]
	if stage_missing or proc_missing:
		print()
		print("== Classification completeness check ==")
		if stage_missing:
			print(
				f"DocTypes missing Supply_Chain_Stage ({len(stage_missing)}): {stage_missing[:10]}{'...' if len(stage_missing) > 10 else ''}"
			)
		if proc_missing:
			print(
				f"DocTypes missing E2E_Process ({len(proc_missing)}): {proc_missing[:10]}{'...' if len(proc_missing) > 10 else ''}"
			)
		print()
	# also inspect generated master workbook if present
	master_path = os.path.join(REPO_ROOT, "master_data_export", "master.csv")
	if os.path.exists(master_path):
		master_rows = _read_csv(master_path)
		blk_stage = [r for r in master_rows if not r.get("Supply_Chain_Stage")]
		blk_proc = [r for r in master_rows if not r.get("E2E_Process")]
		if blk_stage or blk_proc:
			print("== Generated master.csv classification issues ==")
			if blk_stage:
				print(
					f"{len(blk_stage)} rows in master.csv have empty Supply_Chain_Stage (example: {blk_stage[0].get('DocType')})"
				)
			if blk_proc:
				print(
					f"{len(blk_proc)} rows in master.csv have empty E2E_Process (example: {blk_proc[0].get('DocType')})"
				)
			print()

	doctype_names = {d.get("name", "").strip() for d in doctypes if d.get("name")}

	# DocType breakdown
	module_counts = Counter((d.get("module") or "").strip() for d in doctypes)
	custom_doctypes = [d for d in doctypes if _as_bool(d.get("custom"))]
	non_table_doctypes = [d for d in doctypes if not _as_bool(d.get("istable"))]
	child_tables = [d for d in doctypes if _as_bool(d.get("istable"))]
	singles = [d for d in doctypes if _as_bool(d.get("issingle"))]
	submittables = [d for d in doctypes if _as_bool(d.get("is_submittable"))]

	# Field breakdown
	fieldtype_counts = Counter((f.get("fieldtype") or "").strip() for f in fields)
	value_fields = [f for f in fields if (f.get("fieldtype") or "").strip() not in NO_VALUE_FIELDTYPES]
	fields_by_parent = Counter((f.get("parent") or "").strip() for f in fields)
	value_fields_by_parent = Counter((f.get("parent") or "").strip() for f in value_fields)

	# Optional snapshot parts
	custom_fields_count = 0
	if paths.custom_fields_csv:
		custom_fields_count = sum(1 for _ in _read_csv(paths.custom_fields_csv))
	property_setters_count = 0
	if paths.property_setters_csv:
		property_setters_count = sum(1 for _ in _read_csv(paths.property_setters_csv))

	workspaces_count = 0
	if paths.workspaces_csv:
		workspaces_count = sum(1 for _ in _read_csv(paths.workspaces_csv))
	workspace_links_count = 0
	if paths.workspace_links_csv:
		workspace_links_count = sum(1 for _ in _read_csv(paths.workspace_links_csv))

	reports_count = 0
	if paths.reports_csv:
		reports_count = sum(1 for _ in _read_csv(paths.reports_csv))
	workflows_count = 0
	if paths.workflows_csv:
		workflows_count = sum(1 for _ in _read_csv(paths.workflows_csv))
	workflow_transitions_count = 0
	if paths.workflow_transitions_csv:
		workflow_transitions_count = sum(1 for _ in _read_csv(paths.workflow_transitions_csv))
	# if the master export workbook exists, compute stage distribution
	master_path = os.path.join(REPO_ROOT, "master_data_export", "master.csv")
	if os.path.exists(master_path):
		try:
			with open(master_path, newline="", encoding="utf-8") as f:
				reader = csv.DictReader(f)
				stage_counts = Counter(r.get("Supply_Chain_Stage", "") for r in reader)
			print("\nSupply-chain stage distribution in master.csv:")
			for stage, cnt in stage_counts.items():
				print(f"  {stage!r}: {cnt}")
		except Exception as e:
			print(f"failed to read master.csv for stage breakdown: {e}")

	present = [d for d in EXPECTED_DOMAIN_DOCTYPES if d in doctype_names]
	missing = [d for d in EXPECTED_DOMAIN_DOCTYPES if d not in doctype_names]

	def gap_candidates(missing_doctype: str, limit: int = 10) -> list[str]:
		keywords = GAP_KEYWORDS.get(missing_doctype) or []
		if not keywords:
			return []

		def score(name: str) -> int:
			name_l = name.lower()
			s = 0
			for kw in keywords:
				kw_l = kw.lower()
				if kw_l and kw_l in name_l:
					s += 1
			return s

		scored = [(name, score(name)) for name in doctype_names]
		scored = [(name, s) for name, s in scored if s > 0]
		scored.sort(key=lambda x: (-x[1], x[0].lower()))
		return [name for name, _ in scored[:limit]]

	def fmt_list(items: list[str]) -> str:
		return ", ".join(items) if items else "(none)"

	lines: list[str] = []
	lines.append("# Metadata Inventory Summary")
	lines.append("")
	lines.append(f"Snapshot: `{os.path.relpath(paths.export_dir, REPO_ROOT).replace(os.sep, '/')}`")
	lines.append(f"Generated: `{datetime.now().isoformat(timespec='seconds')}`")
	lines.append("")

	lines.append("## Counts")
	lines.append("")
	lines.append(
		f"- DocTypes: **{len(doctypes)}** (non-table: {len(non_table_doctypes)}, child tables: {len(child_tables)}, singles: {len(singles)}, submittable: {len(submittables)})"
	)
	lines.append(
		f"- DocFields: **{len(fields)}** (value-carrying: {len(value_fields)}, layout/no-value: {len(fields) - len(value_fields)})"
	)
	lines.append(f"- Custom DocTypes: **{len(custom_doctypes)}**")
	if custom_fields_count or property_setters_count:
		lines.append(
			f"- Customizations: Custom Fields **{custom_fields_count}**, Property Setters **{property_setters_count}**"
		)
	if workspaces_count or workspace_links_count:
		lines.append(f"- Workspaces: **{workspaces_count}** (workspace links: {workspace_links_count})")
	if reports_count:
		lines.append(f"- Reports: **{reports_count}**")
	if workflows_count:
		lines.append(f"- Workflows: **{workflows_count}** (transitions: {workflow_transitions_count})")
	lines.append("")

	lines.append("## Module Coverage (Top 20)")
	lines.append("")
	lines.append(_md_table(_top(module_counts, 20), ("Module", "DocTypes")))
	lines.append("")

	lines.append("## Largest DocTypes (by field count)")
	lines.append("")
	lines.append(_md_table(_top(fields_by_parent, 15), ("DocType", "Fields")))
	lines.append("")
	lines.append("## Largest DocTypes (value-carrying fields)")
	lines.append("")
	lines.append(_md_table(_top(value_fields_by_parent, 15), ("DocType", "Value Fields")))
	lines.append("")

	lines.append("## Fieldtype Mix (Top 25)")
	lines.append("")
	lines.append(_md_table(_top(fieldtype_counts, 25), ("Fieldtype", "Count")))
	lines.append("")

	lines.append("## Domain Baseline (V1.1 targets)")
	lines.append("")
	lines.append(f"Present: {fmt_list(present)}")
	lines.append(f"Missing: {fmt_list(missing)}")
	lines.append("")

	if missing:
		lines.append("## Gap Candidates (reuse-first hints)")
		lines.append("")
		lines.append(
			"This section lists existing DocTypes whose names match keywords for each missing V1.1 concept. It is a starting point for reuse/extension decisions."
		)
		lines.append("")
		for m in missing:
			candidates = gap_candidates(m)
			if candidates:
				lines.append(f"- **{m}** -> {', '.join(candidates)}")
			else:
				lines.append(f"- **{m}** -> (no keyword matches)")
		lines.append("")

	lines.append("## Planning Notes")
	lines.append("")
	lines.append(
		"- Treat this snapshot as the **single source of truth** for reuse: new features must start by linking to existing DocTypes/fields (or adding Custom Fields/Property Setters) before creating new DocTypes."
	)
	lines.append(
		"- When a new DocType is unavoidable, create it in the correct app/module and document the intent + relationships (links, child tables, workflows, reports)."
	)

	return "\n".join(lines)


def main() -> None:
	parser = argparse.ArgumentParser(description="Analyze Frappe metadata export snapshots")
	parser.add_argument(
		"--export-dir",
		help="Path to snapshot dir (contains doctypes.csv/docfields.csv). Defaults to latest under docs/metadata_exports/.",
		default=None,
	)
	parser.add_argument(
		"--write",
		action="store_true",
		help="Write inventory_summary.md into the snapshot dir (in addition to printing).",
	)
	args = parser.parse_args()

	base_dir = os.path.join(REPO_ROOT, "docs", "metadata_exports")
	export_dir = args.export_dir or _find_latest_snapshot_dir(base_dir)

	summary_md = generate_inventory_summary(export_dir)
	print(summary_md)
	if args.write:
		out_path = os.path.join(os.path.abspath(export_dir), "inventory_summary.md")
		with open(out_path, "w", encoding="utf-8", newline="\n") as f:
			f.write(summary_md)
		print(f"\nWrote: {os.path.relpath(out_path, REPO_ROOT).replace(os.sep, '/')}\n")


if __name__ == "__main__":
	main()
