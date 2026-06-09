# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the corporate login page (`/sign-in`).

This is a design-matched front for the storefront. Frappe's own desk login
remains at `/login`; this page uses the ecommerce customer token endpoint.
"""

import frappe

from ecommerce.website_context import get_chrome
from ecommerce.api.auth import get_current_customer_session

no_cache = 1


def get_context(context):
	redirect_to = frappe.form_dict.get("redirect") or ""
	if not redirect_to.startswith("/"):
		redirect_to = ""

	# Already logged in as an ecommerce customer? Skip the login page.
	if get_current_customer_session():
		frappe.local.flags.redirect_location = redirect_to or "/my-account"
		raise frappe.Redirect

	chrome = get_chrome()
	context.redirect_to = redirect_to
	context.checkout_notice = redirect_to == "/checkout"
	context.brand = chrome.brand
	context.logo = chrome.logo_on_light
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.body_class = "fe-auth-page"
	context.title = f"Sign In | {chrome.brand}"
	context.metatags = {"title": context.title, "description": "Sign in to the corporate portal."}
	return context
