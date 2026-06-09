# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Shared website chrome (header / announcement bar / footer).

Both the landing page (``www/home.py``) and the product detail page
(``www/product.py``) render the same header and footer. The content is sourced
from the standard **Website Settings** DocType (extended with custom fields by
this app) so it stays editable from one place, and every value falls back to a
default that matches the reference design.
"""

import frappe

DEFAULT_NAV = [
	{"label": "All Categories", "url": "/all-products"},
	{"label": "Bulk Orders", "url": "/cart"},
	{"label": "About Us", "url": "/about"},
	{"label": "Contact Us", "url": "/contact"},
]

DEFAULT_FOOTER_COLUMNS = [
	{
		"heading": "Solutions",
		"links": [
			{"label": "Bulk Distribution", "url": "/all-products"},
			{"label": "API Documentation", "url": "#"},
			{"label": "Logistics Services", "url": "#"},
			{"label": "Request Quote", "url": "/sign-in"},
		],
	},
	{
		"heading": "Information",
		"links": [
			{"label": "Privacy Policy", "url": "/privacy-policy"},
			{"label": "Terms of Service", "url": "/terms-of-service"},
			{"label": "About Us", "url": "/about"},
			{"label": "Contact Us", "url": "/contact"},
		],
	},
]

# Bundled brand marks. The navy mark suits light backgrounds (auth pages); the
# white mark is for the dark header/footer. An uploaded Website Settings logo
# (Banner Image / App Logo) overrides both.
DEFAULT_LOGO_ON_DARK = "/assets/ecommerce/images/logo-light.svg"
DEFAULT_LOGO_ON_LIGHT = "/assets/ecommerce/images/logo.svg"

DEFAULT_FOOTER_DESCRIPTION = (
	"Frappe Ecommerce is the leading wholesale distributor of industrial "
	"equipment, electrical supplies, and technical components. Serving global "
	"enterprises since 1984."
)


def homepage_settings():
	"""Return the **Ecommerce Homepage Settings** Single, or ``None``.

	Returns ``None`` if the DocType does not exist yet (e.g. before the first
	``bench migrate``) so the storefront keeps rendering with code defaults.
	"""
	try:
		return frappe.get_cached_doc("Ecommerce Homepage Settings")
	except Exception:
		return None


def get_chrome():
	"""Return the shared header/footer context as a ``frappe._dict``."""
	settings = frappe.get_cached_doc("Website Settings")
	hp = homepage_settings()

	def val(fieldname, default=""):
		return (settings.get(fieldname) or "").strip() or default

	def hpval(fieldname, default=""):
		return ((hp.get(fieldname) if hp else None) or "").strip() or default

	brand = val("brand") or "Frappe Ecommerce"
	uploaded_logo = (hp.get("header_logo") if hp else None) or settings.get("banner_image") or settings.get("app_logo")

	# Storefront login state is intentionally separate from Frappe/Desk sid.
	try:
		from ecommerce.api.auth import get_current_customer_session
		customer_session = get_current_customer_session()
	except Exception:
		customer_session = None
	logged_in = bool(customer_session)
	user_name = customer_session.full_name if customer_session else None
	first_name = customer_session.first_name if customer_session else ""

	# Live cart count for the header badge (best-effort).
	try:
		from ecommerce.api.cart import cart_count
		cart_qty = cart_count()
	except Exception:
		cart_qty = 0

	# Header nav: Homepage Settings menu links → Website Settings top bar → defaults.
	menu_rows = (hp.get("menu_items") if hp else None) or settings.get("top_bar_items")

	theme = frappe._dict(
		primary_color=(hp.get("primary_color") if hp else None),
		secondary_color=(hp.get("secondary_color") if hp else None),
		header_bg_color=(hp.get("header_bg_color") if hp else None),
		button_color=(hp.get("button_color") if hp else None),
		font_family=(hp.get("font_family") if hp else None),
	)

	return frappe._dict(
		brand=brand,
		brand_html=settings.get("brand_html"),
		# `logo` is shown on the dark header/footer; `logo_on_light` on light pages.
		logo=uploaded_logo or DEFAULT_LOGO_ON_DARK,
		logo_on_light=uploaded_logo or DEFAULT_LOGO_ON_LIGHT,
		search_placeholder=hpval("search_placeholder", "Search by SKU, Model, or Component…"),
		announcement_text_1=hpval("topbar_free_freight_text", val("custom_announcement_text_1", "Free freight on orders over $1,500")),
		announcement_text_2=hpval("topbar_distributor_text", val("custom_announcement_text_2", "Official B2B Distributor")),
		nav_items=_mark_active(nav_items(menu_rows)),
		footer_description=val("custom_footer_description", DEFAULT_FOOTER_DESCRIPTION),
		footer_contact_address=val("custom_footer_contact_address", "1200 Industrial Way, Suite 400, Chicago, IL"),
		footer_contact_phone=val("custom_footer_contact_phone", "1-800-FRAPPE-01"),
		footer_columns=footer_columns(settings.get("custom_footer_links")),
		copyright=val("copyright", "Frappe Ecommerce. All Rights Reserved."),
		cart_count=cart_qty,
		theme=theme,
		logged_in=logged_in,
		user_name=user_name,
		first_name=first_name,
	)


def nav_items(rows):
	if rows:
		return [frappe._dict(label=r.get("label"), url=r.get("url") or "#") for r in rows if r.get("label")]
	return [frappe._dict(item) for item in DEFAULT_NAV]


def _current_path():
	"""Current request path without a trailing slash (e.g. ``/product``)."""
	req = getattr(frappe.local, "request", None)
	path = (req.path if req is not None else "") or ""
	if len(path) > 1 and path.endswith("/"):
		path = path.rstrip("/")
	return path


def _mark_active(nav):
	"""Flag the first nav item whose URL matches the current route as active."""
	path = _current_path()
	matched = False
	for item in nav:
		is_match = bool(path) and not matched and item.url == path
		item.active = is_match
		matched = matched or is_match
	return nav


def footer_columns(rows):
	"""Group flat footer-link rows by their column heading, preserving order."""
	if not rows:
		return [
			frappe._dict(heading=c["heading"], links=[frappe._dict(link) for link in c["links"]])
			for c in DEFAULT_FOOTER_COLUMNS
		]

	grouped = {}
	order = []
	for r in rows:
		heading = (r.get("column_heading") or "").strip()
		if not heading:
			continue
		if heading not in grouped:
			grouped[heading] = []
			order.append(heading)
		grouped[heading].append(frappe._dict(label=r.get("label"), url=r.get("url") or "#"))
	return [frappe._dict(heading=h, links=grouped[h]) for h in order]
