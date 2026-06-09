# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Shared builder for simple backend-managed content pages (Privacy Policy,
Terms of Service, …). Each page is driven by its own Single DocType; this keeps
the controllers tiny and the rendering consistent. Every value falls back to a
default so the page renders even when the settings are empty.
"""

import frappe
from frappe.utils import strip_html

from ecommerce.website_context import get_chrome


def _settings(doctype):
	"""Return the Single settings doc, or ``None`` if it doesn't exist yet."""
	try:
		return frappe.get_cached_doc(doctype)
	except Exception:
		return None


def build_context(context, doctype, defaults):
	"""Populate ``context`` for a legal/content page from its settings DocType."""
	s = _settings(doctype)

	def val(fieldname, default=""):
		return ((s.get(fieldname) if s else None) or "").strip() or default

	chrome = get_chrome()
	page = frappe._dict(
		hero_heading=val("hero_heading", defaults["hero_heading"]),
		hero_description=val("hero_description", defaults.get("hero_description", "")),
		hero_image=(s.get("hero_image") if s else None),
		content=val("content", defaults["content"]),
	)

	context.chrome = chrome
	context.page = page
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = val("meta_title", f"{page.hero_heading} | {chrome.brand}")
	context.description = val("meta_description", strip_html(page.hero_description) or page.page_title)
	context.metatags = {
		"title": context.title,
		"description": context.description,
		"og:type": "website",
	}
	return context
