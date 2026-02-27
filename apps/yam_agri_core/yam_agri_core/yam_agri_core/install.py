from __future__ import annotations

import frappe


def after_install() -> None:
	# Dev convenience: workspace navigation + sample org chart (guarded)
	from yam_agri_core.yam_agri_core.seed.dev_data import (
		seed_dev_baseline_demo_data_if_enabled,
		seed_dev_org_chart_if_enabled,
	)
	from yam_agri_core.yam_agri_core.workflow_setup import ensure_workflow_states_from_active_workflows
	from yam_agri_core.yam_agri_core.workspace.setup import (
		ensure_agriculture_workspace_modernized,
		ensure_yam_agri_workspaces,
	)

	ensure_workflow_states_from_active_workflows()
	ensure_yam_agri_workspaces()
	ensure_agriculture_workspace_modernized()
	seed_dev_org_chart_if_enabled()
	seed_dev_baseline_demo_data_if_enabled()


def after_migrate() -> None:
	from yam_agri_core.yam_agri_core.seed.dev_data import (
		seed_dev_baseline_demo_data_if_enabled,
		seed_dev_org_chart_if_enabled,
	)
	from yam_agri_core.yam_agri_core.workflow_setup import ensure_workflow_states_from_active_workflows
	from yam_agri_core.yam_agri_core.workspace.setup import (
		ensure_agriculture_workspace_modernized,
		ensure_yam_agri_workspaces,
	)

	ensure_workflow_states_from_active_workflows()
	ensure_yam_agri_workspaces()
	ensure_agriculture_workspace_modernized()
	seed_dev_org_chart_if_enabled()
	seed_dev_baseline_demo_data_if_enabled()


def get_lot_crop_link_status() -> dict:
	"""Compatibility wrapper for migration diagnostics.

	Canonical function:
	- yam_agri_core.yam_agri_core.patches.v1_2.migrate_lot_crop_links.get_lot_crop_link_status
	"""
	from yam_agri_core.yam_agri_core.patches.v1_2.migrate_lot_crop_links import (
		get_lot_crop_link_status as _get_lot_crop_link_status,
	)

	return _get_lot_crop_link_status()


def get_site_location_bridge_status() -> dict:
	"""Compatibility wrapper for migration diagnostics.

	Canonical function:
	- yam_agri_core.yam_agri_core.patches.v1_2.ensure_schema_and_roles.get_site_location_bridge_status
	"""
	from yam_agri_core.yam_agri_core.patches.v1_2.ensure_schema_and_roles import (
		get_site_location_bridge_status as _get_site_location_bridge_status,
	)

	return _get_site_location_bridge_status()


def check_app_permission() -> bool:
	"""Guard for add_to_apps_screen.

	Returns True if the current user should see YAM Agri in the Apps launcher.
	- Administrator always has access.
	- Website users (no desk access) are excluded.
	"""
	if frappe.session.user == "Administrator":
		return True

	from frappe.utils.user import is_website_user

	if is_website_user():
		return False

	return True
