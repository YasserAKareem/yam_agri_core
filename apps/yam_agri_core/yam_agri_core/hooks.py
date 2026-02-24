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


after_install = "yam_agri_core.yam_agri_core.install.after_install"
after_migrate = "yam_agri_core.yam_agri_core.install.after_migrate"
before_uninstall = "yam_agri_core.yam_agri_core.uninstall.before_uninstall"


extend_bootinfo = "yam_agri_core.yam_agri_core.boot.extend_bootinfo"

# Fallback for Frappe variants that use `boot_session` instead of `extend_bootinfo`.
boot_session = "yam_agri_core.yam_agri_core.boot.boot_session"

# Include JS / CSS files in the Frappe desk header
# app_include_css = "yam_agri_core.bundle.css"
app_include_js = ["yam_agri_core.bundle.js"]


permission_query_conditions = {
	"Site": "yam_agri_core.yam_agri_core.site_permissions.site_query_conditions",
	"Lot": "yam_agri_core.yam_agri_core.site_permissions.lot_query_conditions",
	"QCTest": "yam_agri_core.yam_agri_core.site_permissions.qc_test_query_conditions",
	"Certificate": "yam_agri_core.yam_agri_core.site_permissions.certificate_query_conditions",
	"Nonconformance": "yam_agri_core.yam_agri_core.site_permissions.nonconformance_query_conditions",
	"Device": "yam_agri_core.yam_agri_core.site_permissions.device_query_conditions",
	"Observation": "yam_agri_core.yam_agri_core.site_permissions.observation_query_conditions",
	"ScaleTicket": "yam_agri_core.yam_agri_core.site_permissions.scale_ticket_query_conditions",
	"Transfer": "yam_agri_core.yam_agri_core.site_permissions.transfer_query_conditions",
	"StorageBin": "yam_agri_core.yam_agri_core.site_permissions.storage_bin_query_conditions",
	"EvidencePack": "yam_agri_core.yam_agri_core.site_permissions.evidence_pack_query_conditions",
	"Complaint": "yam_agri_core.yam_agri_core.site_permissions.complaint_query_conditions",
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
	"ScaleTicket": "yam_agri_core.yam_agri_core.site_permissions.scale_ticket_has_permission",
	"Transfer": "yam_agri_core.yam_agri_core.site_permissions.transfer_has_permission",
	"StorageBin": "yam_agri_core.yam_agri_core.site_permissions.storage_bin_has_permission",
	"EvidencePack": "yam_agri_core.yam_agri_core.site_permissions.evidence_pack_has_permission",
	"Complaint": "yam_agri_core.yam_agri_core.site_permissions.complaint_has_permission",
	"Location": "yam_agri_core.yam_agri_core.site_permissions.location_has_permission",
	"Weather": "yam_agri_core.yam_agri_core.site_permissions.weather_has_permission",
	"Crop Cycle": "yam_agri_core.yam_agri_core.site_permissions.crop_cycle_has_permission",
}
