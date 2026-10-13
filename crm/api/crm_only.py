import frappe

CRM_ONLY_FIELD = "crm_only"
CRM_ROUTE = "/crm"
# first URL segment of the ERPNext desk: /desk on v16, /app and /apps on v15
DESK_ROOTS = ("desk", "app", "apps")
# never lock these out of the desk, even if the box is ticked by mistake
BYPASS_ROLES = {"System Manager", "Administrator"}


def is_crm_only_user(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Administrator", "Guest"):
		return False

	if not frappe.get_meta("User").has_field(CRM_ONLY_FIELD):
		return False

	if not frappe.get_cached_value("User", user, CRM_ONLY_FIELD):
		return False

	return not (set(frappe.get_roles(user)) & BYPASS_ROLES)


def redirect_crm_only_user(login_manager=None):
	"""on_login hook: send CRM Only users straight to /crm.
	on_login runs before set_user_info, so home_page can't be set directly;
	get_home_page() (v16) returns this flag first. On v15 the login lands on
	the desk and block_desk_for_crm_only bounces it to /crm."""
	user = login_manager.user if login_manager else frappe.session.user
	if is_crm_only_user(user):
		frappe.local.flags.home_page = CRM_ROUTE


def block_desk_for_crm_only(context):
	"""update_website_context hook: CRM Only users may not open the ERPNext
	desk (/desk on v16, /app on v15). Only pages are blocked, /api calls the
	CRM SPA relies on never pass through here."""
	# request.path, not local.path: v16's resolver returns the desk route
	# before setting local.path
	request = getattr(frappe.local, "request", None)
	root = (request.path if request else "").strip("/").split("/")[0]
	if root not in DESK_ROOTS:
		return

	if not is_crm_only_user():
		return

	# 302, not frappe.redirect's 301: browsers cache a 301, which would keep
	# bouncing the desk after the box is unticked or another user logs in
	frappe.flags.redirect_location = CRM_ROUTE
	raise frappe.Redirect(302)
