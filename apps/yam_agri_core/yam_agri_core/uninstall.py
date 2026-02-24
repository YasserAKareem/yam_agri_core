"""
Cleanup logic executed when yam_agri_core is uninstalled from a site.

Keep this module even if empty — Frappe expects it to exist if referenced in hooks.py.
"""

import frappe


def before_uninstall():
	"""Called before the app is removed from a site.

	Add any cleanup here (remove custom fields, workflows, etc.).
	Currently a no-op placeholder.
	"""
	frappe.logger(__name__).info("yam_agri_core: before_uninstall — no cleanup required")
