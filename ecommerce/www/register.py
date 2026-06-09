# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the corporate registration page (`/register`)."""

import frappe

from ecommerce.website_context import get_chrome

no_cache = 1

TRUST_CHIPS = [
	{"title": "Global Distribution", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7h11v8H3z"/><path d="M14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/></svg>'},
	{"title": "Certified Quality", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="m9 12 2 2 4-4"/></svg>'},
	{"title": "24/7 B2B Support", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13a8 8 0 0 1 16 0"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/></svg>'},
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
	context.metatags = {"title": context.title, "description": "Create a corporate B2B account."}
	return context
