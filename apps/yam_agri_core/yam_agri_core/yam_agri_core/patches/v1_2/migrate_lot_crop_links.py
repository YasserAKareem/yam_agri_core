import frappe


def execute():
	normalize_lot_crop_links()


def normalize_lot_crop_links() -> None:
	"""Normalize legacy text values in Lot.crop to canonical Crop links.

	- Ensures every non-empty `Lot.crop` points to an existing Crop name.
	- Maps legacy text via `name`, `crop_name`, or `title` when available.
	- Logs unresolved values for manual cleanup.
	"""

	if not frappe.db.exists("DocType", "Lot"):
		return

	if not frappe.db.exists("DocType", "Crop"):
		return

	crop_meta = frappe.get_meta("Crop")
	has_crop_name = crop_meta.has_field("crop_name")
	has_title = crop_meta.has_field("title")

	lots = frappe.get_all("Lot", fields=["name", "crop"], limit_page_length=0)
	changed = False
	unresolved: set[str] = set()

	for lot in lots:
		raw_crop = (lot.get("crop") or "").strip()
		if not raw_crop:
			continue

		if frappe.db.exists("Crop", raw_crop):
			continue

		crop_name = None
		if has_crop_name:
			crop_name = frappe.db.get_value("Crop", {"crop_name": raw_crop}, "name")
		if not crop_name and has_title:
			crop_name = frappe.db.get_value("Crop", {"title": raw_crop}, "name")

		if crop_name:
			frappe.db.set_value("Lot", lot["name"], "crop", crop_name, update_modified=False)
			changed = True
			continue

		unresolved.add(raw_crop)

	if changed:
		frappe.db.commit()

	if unresolved:
		frappe.log_error(
			title="Lot crop normalization unresolved values",
			message="\n".join(sorted(unresolved)),
		)


def get_lot_crop_link_status() -> dict:
	"""Diagnostic summary for Lot->Crop migration readiness.

	Safe to run via:
	- bench --site <site> execute yam_agri_core.yam_agri_core.patches.v1_2.migrate_lot_crop_links.get_lot_crop_link_status
	"""
	if not frappe.db.exists("DocType", "Lot"):
		return {"available": False, "reason": "Lot doctype missing"}

	if not frappe.db.exists("DocType", "Crop"):
		return {"available": False, "reason": "Crop doctype missing"}

	crop_meta = frappe.get_meta("Crop")
	has_crop_name = crop_meta.has_field("crop_name")
	has_title = crop_meta.has_field("title")

	total = 0
	linked = 0
	mapped = 0
	unresolved_values: set[str] = set()

	lots = frappe.get_all("Lot", fields=["name", "crop"], limit_page_length=0)
	for lot in lots:
		total += 1
		crop_value = (lot.get("crop") or "").strip()
		if not crop_value:
			continue

		if frappe.db.exists("Crop", crop_value):
			linked += 1
			continue

		found = None
		if has_crop_name:
			found = frappe.db.get_value("Crop", {"crop_name": crop_value}, "name")
		if not found and has_title:
			found = frappe.db.get_value("Crop", {"title": crop_value}, "name")

		if found:
			mapped += 1
		else:
			unresolved_values.add(crop_value)

	return {
		"available": True,
		"total_lots": total,
		"linked_crop_names": linked,
		"mappable_legacy_values": mapped,
		"unresolved_count": len(unresolved_values),
		"unresolved_values": sorted(unresolved_values),
	}
