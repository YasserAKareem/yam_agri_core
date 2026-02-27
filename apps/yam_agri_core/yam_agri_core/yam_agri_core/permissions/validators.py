import frappe


def enforce_qc_test_site_consistency(doc, method=None) -> None:
	lot = doc.get("lot") if hasattr(doc, "get") else None
	if not lot:
		return

	lot_site = frappe.db.get_value("Lot", lot, "site")
	qc_site = (doc.get("site") or "").strip() if hasattr(doc, "get") else ""
	if lot_site and qc_site and lot_site != qc_site:
		frappe.throw(frappe._("Lot site must match QCTest site"), frappe.ValidationError)


def enforce_certificate_site_consistency(doc, method=None) -> None:
	lot = doc.get("lot") if hasattr(doc, "get") else None
	if not lot:
		return

	lot_site = frappe.db.get_value("Lot", lot, "site")
	certificate_site = (doc.get("site") or "").strip() if hasattr(doc, "get") else ""
	if lot_site and certificate_site and lot_site != certificate_site:
		frappe.throw(frappe._("Lot site must match Certificate site"), frappe.ValidationError)
