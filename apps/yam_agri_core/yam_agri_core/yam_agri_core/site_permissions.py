from __future__ import annotations

from yam_agri_core.yam_agri_core.permissions.has_permission import *
from yam_agri_core.yam_agri_core.permissions.query_conditions import *
from yam_agri_core.yam_agri_core.permissions.site_scope import (
	_user_has_role,
	assert_site_access,
	get_allowed_locations,
	get_allowed_sites,
	has_site_permission,
	resolve_site,
)
from yam_agri_core.yam_agri_core.permissions.validators import (
	enforce_certificate_site_consistency,
	enforce_qc_test_site_consistency,
)


# Investment Opportunity permissions (uses standard pattern)
def investment_opportunity_query_conditions(user):
	"""Site-scoped query filter for Investment Opportunity."""
	from yam_agri_core.yam_agri_core.permissions.query_conditions import build_site_query_condition
	return build_site_query_condition("Investment Opportunity", user)


def investment_opportunity_has_permission(doc, ptype, user):
	"""Site-scoped permission check for Investment Opportunity."""
	from yam_agri_core.yam_agri_core.permissions.has_permission import _doctype_has_site_permission
	return _doctype_has_site_permission(doc, user)

