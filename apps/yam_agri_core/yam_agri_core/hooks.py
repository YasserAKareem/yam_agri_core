# hooks for yam_agri_core

app_name = "yam_agri_core"
app_title = "YAM Agri Core"
app_publisher = "YAM Agri Co."
app_description = "YAM Agri Core app (skeleton for tests and controllers)"
app_email = ""
app_license = "MIT"


after_install = "yam_agri_core.yam_agri_core.install.after_install"
after_migrate = "yam_agri_core.yam_agri_core.install.after_migrate"


permission_query_conditions = {
	"Site": "yam_agri_core.yam_agri_core.site_permissions.site_query_conditions",
	"YAM Plot": "yam_agri_core.yam_agri_core.site_permissions.yam_plot_query_conditions",
	"YAM Soil Test": "yam_agri_core.yam_agri_core.site_permissions.yam_soil_test_query_conditions",
	"YAM Plot Yield": "yam_agri_core.yam_agri_core.site_permissions.yam_plot_yield_query_conditions",
	"YAM Crop Variety": "yam_agri_core.yam_agri_core.site_permissions.yam_crop_variety_query_conditions",
	"YAM Crop Variety Recommendation": "yam_agri_core.yam_agri_core.site_permissions.yam_crop_variety_recommendation_query_conditions",
}
