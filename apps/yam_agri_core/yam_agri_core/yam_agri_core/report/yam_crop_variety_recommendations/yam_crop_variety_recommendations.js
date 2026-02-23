/* global frappe */

frappe.query_reports["YAM Crop Variety Recommendations"] = {
	filters: [
		{
			fieldname: "site",
			label: __("Site"),
			fieldtype: "Link",
			options: "Site",
			reqd: 1,
		},
		{
			fieldname: "season",
			label: __("Season"),
			fieldtype: "Data",
			reqd: 1,
			default: String(new Date().getFullYear()),
		},
		{
			fieldname: "crop",
			label: __("Crop"),
			fieldtype: "Link",
			options: "Crop",
			reqd: 1,
		},
	],
};
