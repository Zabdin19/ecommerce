# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the customer registration page (`/register`)."""

import frappe

from ecommerce.website_context import get_chrome

no_cache = 1

TRUST_CHIPS = [
	{"title": "Business Account", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20h16V8H4zM8 8V4h8v4M8 12h8"/></svg>'},
	{"title": "Order History", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 4h14v16H5zM8 9h8M8 13h8"/></svg>'},
	{"title": "Quote Requests", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 5h16v12H8l-4 3zM8 9h8M8 13h5"/></svg>'},
]


def get_context(context):
	chrome = get_chrome()
	context.brand = chrome.brand
	context.logo = chrome.logo_on_light
	context.trust_chips = TRUST_CHIPS
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.body_class = "fe-auth-page"
	context.title = f"Create Account | {chrome.brand}"
	context.metatags = {"title": context.title, "description": f"Create your {chrome.brand} account."}
	return context
