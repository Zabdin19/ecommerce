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
	"Pakistan's trusted online store for new and refurbished laptops — genuine "
	"products, official warranty, and nationwide delivery."
)

DEFAULT_STORY_BODY = (
	"<p>Lapmarkaz started with a simple idea: buying a laptop online in Pakistan "
	"should be easy, transparent, and worry-free. We carry brand new laptops from "
	"Dell, HP, Lenovo, Asus, Acer, Apple, MSI and Microsoft, along with fully "
	"tested refurbished options for anyone who wants great performance at a "
	"lower price.</p>"
	"<p>Every laptop that leaves our warehouse is inspected and tested before it "
	"ships — with Cash on Delivery available across Pakistan and support to "
	"help you pick the right machine for your budget and workload.</p>"
)

DEFAULT_STATS = [
	{"value": "1000+", "label": "Laptops Delivered"},
	{"value": "8+", "label": "Brands Available"},
	{"value": "60+", "label": "Cities Covered"},
	{"value": "4.6★", "label": "Average Rating"},
]

DEFAULT_MISSION = (
	"To make buying a laptop online in Pakistan simple and trustworthy — with "
	"genuine products, honest pricing, and support that actually helps."
)
DEFAULT_VISION = (
	"To be the most trusted laptop store in Pakistan, for new and refurbished "
	"laptops alike."
)

DEFAULT_VALUES = [
	{
		"title": "100% Genuine",
		"description": "Every laptop is sourced from trusted suppliers and tested before it reaches you.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="m9 12 2 2 4-4"/></svg>',
	},
	{
		"title": "Nationwide Delivery",
		"description": "Fast, tracked delivery to every city in Pakistan, with Cash on Delivery available.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7h11v8H3z"/><path d="M14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/></svg>',
	},
	{
		"title": "Expert Support",
		"description": "Not sure which laptop is right for you? Our team is here to help you decide.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13a8 8 0 0 1 16 0"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/></svg>',
	},
]

DEFAULT_TEAM = []

DEFAULT_CTA = (
	"Looking for laptops in bulk for your office or institution? Get in touch "
	"for special pricing and dedicated support."
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
		page_title=val("page_title", "About Lapmarkaz"),
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
