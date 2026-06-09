# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the About Us page (`/about`).

All content is managed from the **About Page Settings** Single DocType (Frappe
Desk). Every value falls back to a design-matched default so the page renders
correctly even before an administrator fills the settings in. The shared
header/footer chrome is built by ``ecommerce.website_context.get_chrome``.
"""

import frappe
from frappe.utils import strip_html

from ecommerce.website_context import get_chrome

no_cache = 1


DEFAULT_SUBTITLE = (
	"Powering industrial procurement for enterprises worldwide — quality "
	"verified, logistics guaranteed, since 1984."
)

DEFAULT_STORY_BODY = (
	"<p>What began in 1984 as a single regional warehouse has grown into one of "
	"the most trusted names in industrial distribution. We supply the tools, "
	"equipment, and components that keep factories, job sites, and supply chains "
	"moving.</p>"
	"<p>Today we serve thousands of enterprise customers with over 500,000 SKUs "
	"from the world's leading manufacturers — backed by the logistics network "
	"and technical expertise our partners depend on.</p>"
)

DEFAULT_STATS = [
	{"value": "40+", "label": "Years in Business"},
	{"value": "500K+", "label": "SKUs Available"},
	{"value": "12K+", "label": "Enterprise Clients"},
	{"value": "99.2%", "label": "On-time Delivery"},
]

DEFAULT_MISSION = (
	"To give every business reliable, fast access to the industrial supplies "
	"they need — with transparent pricing, verified quality, and logistics they "
	"can count on."
)
DEFAULT_VISION = (
	"To be the most trusted B2B procurement platform in the industry, connecting "
	"manufacturers and enterprises through technology and service."
)

DEFAULT_VALUES = [
	{
		"title": "Quality Verified",
		"description": "Every product is sourced from certified manufacturers and quality-checked before it reaches you.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="m9 12 2 2 4-4"/></svg>',
	},
	{
		"title": "Logistics Guaranteed",
		"description": "A nationwide distribution network delivers on time, every time, with full shipment tracking.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7h11v8H3z"/><path d="M14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/></svg>',
	},
	{
		"title": "Expert Support",
		"description": "Technical advisors available 24/7 to help you select the right specs for any job.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13a8 8 0 0 1 16 0"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/></svg>',
	},
]

DEFAULT_TEAM = [
	{"member_name": "Eleanor Vance", "role": "Chief Executive Officer", "image": None},
	{"member_name": "Marcus Reid", "role": "VP, Supply Chain", "image": None},
	{"member_name": "Priya Nair", "role": "Head of Engineering", "image": None},
	{"member_name": "David Okafor", "role": "Director, Client Success", "image": None},
]

DEFAULT_CTA = (
	"Open a corporate account and streamline your procurement with dedicated "
	"support, bulk pricing, and NET-30 terms."
)


def _about():
	try:
		return frappe.get_cached_doc("About Page Settings")
	except Exception:
		return None


def get_context(context):
	ap = _about()
	chrome = get_chrome()

	def val(fieldname, default=""):
		return ((ap.get(fieldname) if ap else None) or "").strip() or default

	def table(fieldname):
		return (ap.get(fieldname) if ap else None) or None

	about = frappe._dict(
		page_title=val("page_title", "About Frappe Ecommerce"),
		page_subtitle=val("page_subtitle", DEFAULT_SUBTITLE),
		hero_image=(ap.get("hero_image") if ap else None),
		story_heading=val("story_heading", "Our Story"),
		story_body=(ap.get("story_body") if ap else None) or DEFAULT_STORY_BODY,
		story_image=(ap.get("story_image") if ap else None),
		stats=_rows(table("stats"), DEFAULT_STATS, ("value", "label")),
		mission_heading=val("mission_heading", "Our Mission"),
		mission_text=val("mission_text", DEFAULT_MISSION),
		vision_heading=val("vision_heading", "Our Vision"),
		vision_text=val("vision_text", DEFAULT_VISION),
		values_heading=val("values_heading", "What We Stand For"),
		value_items=_rows(table("value_items"), DEFAULT_VALUES, ("title", "icon", "description")),
		team_heading=val("team_heading", "Leadership Team"),
		team=_rows(table("team_members"), DEFAULT_TEAM, ("member_name", "role", "image")),
		cta_heading=val("cta_heading", "Ready to partner with us?"),
		cta_text=val("cta_text", DEFAULT_CTA),
		cta_button_text=val("cta_button_text", "Browse Catalog"),
		cta_button_link=val("cta_button_link", "/all-products"),
	)

	context.chrome = chrome
	context.about = about
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1

	context.title = val("meta_title", f"{about.page_title} | {chrome.brand}")
	context.description = val("meta_description", strip_html(about.page_subtitle))
	context.metatags = {
		"title": context.title,
		"description": context.description,
		"og:type": "website",
	}
	return context


def _rows(rows, default, fields):
	if rows:
		return [frappe._dict({f: row.get(f) for f in fields}) for row in rows]
	return [frappe._dict(item) for item in default]
