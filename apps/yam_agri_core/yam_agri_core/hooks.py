# hooks for yam_agri_core

app_name = "yam_agri_core"
app_title = "YAM Agri Core"
app_publisher = "YAM Agri Co."
app_description = "YAM Agri Core — cereal supply chain quality and traceability platform"
app_email = "dev@yam-agri.com"
app_license = "MIT"
app_version = "1.1.0-dev"
source_link = "https://github.com/YasserAKareem/yam_agri_core"
app_logo_url = "/assets/yam_agri_core/images/yam-agri-logo.svg"
required_apps = ["frappe/erpnext"]

add_to_apps_screen = [
	{
		"name": "yam_agri_core",
		"logo": "/assets/yam_agri_core/images/yam-agri-logo.svg",
		"title": "YAM Agri",
		"route": "/app/lot",
		"has_permission": "yam_agri_core.yam_agri_core.install.check_app_permission",
	}
]

after_install = "yam_agri_core.yam_agri_core.install.after_install"
after_migrate = "yam_agri_core.yam_agri_core.install.after_migrate"
before_uninstall = "yam_agri_core.yam_agri_core.uninstall.before_uninstall"

# Fixtures exported/imported by `bench export-fixtures` / loaded on `bench migrate`
fixtures = ["Workflow"]

extend_bootinfo = "yam_agri_core.yam_agri_core.boot.extend_bootinfo"

# Fallback for Frappe variants that use `boot_session` instead of `extend_bootinfo`.
boot_session = "yam_agri_core.yam_agri_core.boot.boot_session"

# Include JS / CSS files in the Frappe desk header
# app_include_css = "yam_agri_core.bundle.css"
app_include_js = ["yam_agri_core.bundle.js"]

# Per-doctype client-side JS (relative to the app's module directory)
doctype_js = {
	"Lot": "yam_agri_core/doctype/lot/lot.js",
	"Site": "yam_agri_core/doctype/site/site.js",
	"QCTest": "yam_agri_core/doctype/qc_test/qc_test.js",
}

permission_query_conditions = {
	"Site": "yam_agri_core.yam_agri_core.site_permissions.site_query_conditions",
	"Lot": "yam_agri_core.yam_agri_core.site_permissions.lot_query_conditions",
	"QCTest": "yam_agri_core.yam_agri_core.site_permissions.qc_test_query_conditions",
	"Certificate": "yam_agri_core.yam_agri_core.site_permissions.certificate_query_conditions",
	"Nonconformance": "yam_agri_core.yam_agri_core.site_permissions.nonconformance_query_conditions",
	"Device": "yam_agri_core.yam_agri_core.site_permissions.device_query_conditions",
	"Observation": "yam_agri_core.yam_agri_core.site_permissions.observation_query_conditions",
	"Observation Threshold Policy": "yam_agri_core.yam_agri_core.site_permissions.observation_threshold_policy_query_conditions",
	"ScaleTicket": "yam_agri_core.yam_agri_core.site_permissions.scale_ticket_query_conditions",
	"Transfer": "yam_agri_core.yam_agri_core.site_permissions.transfer_query_conditions",
	"StorageBin": "yam_agri_core.yam_agri_core.site_permissions.storage_bin_query_conditions",
	"EvidencePack": "yam_agri_core.yam_agri_core.site_permissions.evidence_pack_query_conditions",
	"Complaint": "yam_agri_core.yam_agri_core.site_permissions.complaint_query_conditions",
	"Season Policy": "yam_agri_core.yam_agri_core.site_permissions.season_policy_query_conditions",
	"Site Tolerance Policy": "yam_agri_core.yam_agri_core.site_permissions.site_tolerance_policy_query_conditions",
	"YAM Plot": "yam_agri_core.yam_agri_core.site_permissions.yam_plot_query_conditions",
	"YAM Soil Test": "yam_agri_core.yam_agri_core.site_permissions.yam_soil_test_query_conditions",
	"YAM Plot Yield": "yam_agri_core.yam_agri_core.site_permissions.yam_plot_yield_query_conditions",
	"YAM Crop Variety": "yam_agri_core.yam_agri_core.site_permissions.yam_crop_variety_query_conditions",
	"YAM Crop Variety Recommendation": "yam_agri_core.yam_agri_core.site_permissions.yam_crop_variety_recommendation_query_conditions",
	"Location": "yam_agri_core.yam_agri_core.site_permissions.location_query_conditions",
	"Weather": "yam_agri_core.yam_agri_core.site_permissions.weather_query_conditions",
	"Crop Cycle": "yam_agri_core.yam_agri_core.site_permissions.crop_cycle_query_conditions",
}


has_permission = {
	"Site": "yam_agri_core.yam_agri_core.site_permissions.site_has_permission",
	"Lot": "yam_agri_core.yam_agri_core.site_permissions.lot_has_permission",
	"QCTest": "yam_agri_core.yam_agri_core.site_permissions.qc_test_has_permission",
	"Certificate": "yam_agri_core.yam_agri_core.site_permissions.certificate_has_permission",
	"Nonconformance": "yam_agri_core.yam_agri_core.site_permissions.nonconformance_has_permission",
	"Device": "yam_agri_core.yam_agri_core.site_permissions.device_has_permission",
	"Observation": "yam_agri_core.yam_agri_core.site_permissions.observation_has_permission",
	"Observation Threshold Policy": "yam_agri_core.yam_agri_core.site_permissions.observation_threshold_policy_has_permission",
	"ScaleTicket": "yam_agri_core.yam_agri_core.site_permissions.scale_ticket_has_permission",
	"Transfer": "yam_agri_core.yam_agri_core.site_permissions.transfer_has_permission",
	"StorageBin": "yam_agri_core.yam_agri_core.site_permissions.storage_bin_has_permission",
	"EvidencePack": "yam_agri_core.yam_agri_core.site_permissions.evidence_pack_has_permission",
	"Complaint": "yam_agri_core.yam_agri_core.site_permissions.complaint_has_permission",
	"Season Policy": "yam_agri_core.yam_agri_core.site_permissions.season_policy_has_permission",
	"Site Tolerance Policy": "yam_agri_core.yam_agri_core.site_permissions.site_tolerance_policy_has_permission",
	"Location": "yam_agri_core.yam_agri_core.site_permissions.location_has_permission",
	"Weather": "yam_agri_core.yam_agri_core.site_permissions.weather_has_permission",
	"Crop Cycle": "yam_agri_core.yam_agri_core.site_permissions.crop_cycle_has_permission",
	"YAM Plot": "yam_agri_core.yam_agri_core.site_permissions.yam_plot_has_permission",
	"YAM Soil Test": "yam_agri_core.yam_agri_core.site_permissions.yam_soil_test_has_permission",
	"YAM Plot Yield": "yam_agri_core.yam_agri_core.site_permissions.yam_plot_yield_has_permission",
	"YAM Crop Variety": "yam_agri_core.yam_agri_core.site_permissions.yam_crop_variety_has_permission",
	"YAM Crop Variety Recommendation": "yam_agri_core.yam_agri_core.site_permissions.yam_crop_variety_recommendation_has_permission",
}

# ERPNext-style global search registration — lets Desk's global search bar find these records.
global_search_doctypes = {
	"Default": [
		{"doctype": "Lot", "index": 0},
		{"doctype": "Site", "index": 1},
		{"doctype": "QCTest", "index": 2},
		{"doctype": "Certificate", "index": 3},
		{"doctype": "StorageBin", "index": 4},
		{"doctype": "Transfer", "index": 5},
		{"doctype": "ScaleTicket", "index": 6},
		{"doctype": "Observation", "index": 7},
		{"doctype": "Observation Threshold Policy", "index": 8},
		{"doctype": "Nonconformance", "index": 8},
		{"doctype": "EvidencePack", "index": 9},
		{"doctype": "Complaint", "index": 10},
		{"doctype": "Season Policy", "index": 11},
		{"doctype": "Site Tolerance Policy", "index": 12},
	],
}


doc_events = {
	"QCTest": {
		"validate": "yam_agri_core.yam_agri_core.site_permissions.enforce_qc_test_site_consistency",
	},
	"Certificate": {
		"validate": "yam_agri_core.yam_agri_core.site_permissions.enforce_certificate_site_consistency",
	},
	"Observation": {
		"validate": "yam_agri_core.yam_agri_core.doctype.observation.observation.enforce_observation_validate",
	},
}
