from __future__ import annotations

import frappe


def ensure_workflow_states_from_active_workflows() -> dict:
	"""Ensure Workflow State master records exist for all active workflows.

	Fixes runtime errors like: "Workflow State Draft not found".
	Idempotent and safe to run after every migrate.
	"""
	if not frappe.db.exists("DocType", "Workflow"):
		return {"created": [], "missing_states": [], "checked_states": []}
	if not frappe.db.exists("DocType", "Workflow State"):
		return {"created": [], "missing_states": [], "checked_states": []}

	states = set()
	# Child table rows that define states.
	if frappe.db.exists("DocType", "Workflow Document State"):
		for state in frappe.get_all("Workflow Document State", pluck="state") or []:
			if state and isinstance(state, str):
				states.add(state.strip())

	# Fallback: at minimum, Draft should exist if any workflow uses it.
	if "Draft" not in states:
		states.add("Draft")

	states = {s for s in states if s}

	created: list[str] = []
	missing: list[str] = []
	for state in sorted(states):
		if frappe.db.exists("Workflow State", state):
			continue
		missing.append(state)
		try:
			doc = frappe.get_doc(
				{
					"doctype": "Workflow State",
					"workflow_state_name": state,
					"style": _pick_style_for_state(state),
				}
			)
			doc.insert(ignore_permissions=True)
			created.append(state)
		except Exception:
			# Best-effort: don't fail migrations for styling or edge-case validation.
			pass

	if created:
		frappe.db.commit()

	return {
		"checked_states": sorted(states),
		"missing_states": missing,
		"created": created,
	}


def get_workflow_state_status() -> dict:
	"""Diagnostic helper for bench execute."""
	existing = frappe.get_all("Workflow State", pluck="name") if frappe.db.exists("DocType", "Workflow State") else []
	return {
		"workflow_state_count": len(existing),
		"workflow_states": sorted(existing),
	}


def _pick_style_for_state(state: str) -> str:
	name = (state or "").strip().lower()
	if name in {"approved", "completed", "closed", "done", "passed"}:
		return "Success"
	if name in {"rejected", "failed", "cancelled", "canceled"}:
		return "Danger"
	if name in {"pending", "in progress", "review", "under review"}:
		return "Warning"
	return "Primary"
