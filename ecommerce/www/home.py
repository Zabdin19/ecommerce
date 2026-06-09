# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the Ecommerce landing page (`/home`).

All visible content is driven by the standard **Website Settings** DocType,
which the Ecommerce app extends with custom fields (see
``ecommerce/fixtures/custom_field.json``). Every value falls back to a sensible
default that matches the reference design, so the page renders correctly even
before an administrator fills the settings in. The shared header/footer chrome
is built by ``ecommerce.website_context.get_chrome``.
"""

import frappe
from frappe.utils import strip_html

from ecommerce.api import products
from ecommerce.website_context import get_chrome, homepage_settings

no_cache = 1


# --- Default content (mirrors the reference design) -------------------------

DEFAULT_CATEGORY_CARDS = [
	{
		"title": "Power Tools",
		"subtitle": "Drills, Saws, Sanders & Precision Machinery",
		"link": "/all-products",
		"is_large": 1,
		"image": None,
	},
	{"title": "Safety Equipment", "subtitle": "", "link": "/all-products", "is_large": 0, "image": None},
	{"title": "Electrical", "subtitle": "", "link": "/all-products", "is_large": 0, "image": None},
	{
		"title": "Pneumatics & Hydraulics",
		"subtitle": "",
		"link": "/all-products",
		"is_large": 0,
		"image": None,
	},
]

DEFAULT_FEATURES = [
	{
		"title": "Reliable Shipping",
		"description": "Next-day delivery for corporate partners within 50 miles of any hub center.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7h11v8H3z"/><path d="M14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/></svg>',
	},
	{
		"title": "B2B Integration",
		"description": "Seamlessly connect your ERP for automated procurement and bulk invoicing.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/><path d="M11 7h4a2 2 0 0 1 2 2v4"/></svg>',
	},
	{
		"title": "Expert Support",
		"description": "Technical advisors available 24/7 to help you select the right specs for any job.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13a8 8 0 0 1 16 0"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/><path d="M20 19a4 4 0 0 1-4 3h-2"/></svg>',
	},
]

DEFAULT_BEST_SELLERS = [
	{"brand": "DEWALT", "name": "20V MAX XR Brushless Orbital Sander", "sku": "DW-OS-9921", "price": "$189.00", "price_value": 189.0, "badge": "Best Seller"},
	{"brand": "MILWAUKEE", "name": 'M18 FUEL 1/2" High Torque Impact Wrench', "sku": "MW-IW-4410", "price": "$299.00", "price_value": 299.0, "badge": "In Stock"},
	{"brand": "3M SAFETY", "name": "SecureFit Vented Safety Helmet with Visor", "sku": "3M-SH-005", "price": "$45.50", "price_value": 45.5, "badge": ""},
	{"brand": "CAMPBELL HAUSFELD", "name": "20-Gallon Vertical Air Compressor 150 PSI", "sku": "CH-AC-20V", "price": "$549.00", "price_value": 549.0, "badge": ""},
]

DEFAULT_BRANDS = ["MAKITA", "BOSCH", "DEWALT", "3M SAFETY", "HILTI", "MILWAUKEE"]

DEFAULT_HERO_SUBTEXT = (
	"Streamline your B2B operations with over 500,000 SKUs from world-leading "
	"manufacturers. Quality verified, logistics guaranteed."
)


def get_context(context):
	# All homepage content is managed from the "Ecommerce Homepage Settings"
	# Single DocType (Frappe Desk). Every value falls back to a design-matched
	# default so the page renders even when the settings are empty.
	hp = homepage_settings()
	chrome = get_chrome()

	def val(fieldname, default=""):
		return ((hp.get(fieldname) if hp else None) or "").strip() or default

	def row_table(fieldname):
		return (hp.get(fieldname) if hp else None) or None

	landing = frappe._dict(
		# Hero
		hero_badge=val("hero_badge", "Established 1984"),
		hero_heading=val("hero_heading", "The Gold Standard in"),
		hero_heading_highlight=val("hero_heading_highlight", "Industrial Supply"),
		hero_subtext=val("hero_subtext", DEFAULT_HERO_SUBTEXT),
		hero_button_text=val("hero_button_text", "Shop Now"),
		hero_button_link=val("hero_button_link", "/all-products"),
		hero_secondary_button_text=val("hero_secondary_button_text", "Request a Quote"),
		hero_secondary_button_link=val("hero_secondary_button_link", "/sign-in"),
		hero_background_image=(hp.get("hero_background_image") if hp else None),
		hero_images=_hero_images(hp),
		# Essential categories
		categories_heading=val("categories_heading", "Essential Categories"),
		categories_subtext=val(
			"categories_subtext",
			"Browse our curated selection of high-performance industrial equipment "
			"tailored for professional requirements.",
		),
		category_cards=_rows_or_default(row_table("category_cards"), DEFAULT_CATEGORY_CARDS,
			fields=("title", "subtitle", "link", "is_large", "image")),
		# Featured products — admin-picked Items, else best-sellers, else demo
		best_sellers_heading=val("best_sellers_heading", "Best Sellers"),
		best_sellers=_featured_products(row_table("featured_products")) or products.get_best_sellers(4) or DEFAULT_BEST_SELLERS,
		# Promotion banner
		promo_title=val("promo_title", "Precision Performance"),
		promo_subtitle=val("promo_subtitle", "Now Within Reach"),
		promo_text=val(
			"promo_text",
			"Save up to 30% on bulk machining equipment and precision lathes for "
			"corporate account holders. Limitless efficiency, legendary durability.",
		),
		promo_button_text=val("promo_button_text", "View Special Offer"),
		promo_button_link=val("promo_button_link", "#"),
		promo_note=val("promo_note", "Ends in 48 hours"),
		promo_image=(hp.get("promo_image") if hp else None),
		# Brand strip
		brands=_brands(val("brands")) or DEFAULT_BRANDS,
		# Trust features
		features=_rows_or_default(row_table("feature_items"), DEFAULT_FEATURES,
			fields=("title", "description", "icon")),
		# Newsletter
		newsletter_title=val("newsletter_title", "Stay Informed"),
		newsletter_subtitle=val(
			"newsletter_subtitle",
			"Get technical bulletins, industry news, and exclusive B2B offers.",
		),
	)

	context.chrome = chrome
	context.landing = landing
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1

	# --- SEO metadata (kept on Website Settings custom fields) ---------------
	ws = frappe.get_cached_doc("Website Settings")

	def wsval(fieldname, default=""):
		return (ws.get(fieldname) or "").strip() or default

	context.title = wsval("custom_meta_title", f"{chrome.brand} — {landing.hero_heading} {landing.hero_heading_highlight}")
	context.description = wsval("custom_meta_description", strip_html(landing.hero_subtext))
	context.metatags = {
		"title": context.title,
		"description": context.description,
		"keywords": wsval("custom_meta_keywords", "industrial supply, b2b wholesale, tools, equipment"),
		"image": ws.get("custom_meta_image") or "",
		"og:type": "website",
	}

	return context


def _rows_or_default(rows, default, fields):
	if rows:
		return [frappe._dict({f: row.get(f) for f in fields}) for row in rows]
	return [frappe._dict(item) for item in default]


def _brands(text):
	"""Split the newline-separated brand strip into a clean list."""
	return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _hero_images(hp):
	"""Ordered list of hero background images.

	Uses the ``hero_images`` slideshow table when present; otherwise falls back
	to the single ``hero_background_image`` (so existing setups keep working).
	"""
	rows = (hp.get("hero_images") if hp else None) or []
	images = [r.get("image") for r in rows if r.get("image")]
	if not images:
		single = hp.get("hero_background_image") if hp else None
		if single:
			images = [single]
	return images


def _featured_products(rows):
	"""Serialize admin-picked featured Items (Link rows) for the product grid."""
	if not rows:
		return None
	from ecommerce.api.common import get_price, money

	out = []
	for r in rows:
		code = r.get("item")
		if not code or not frappe.db.exists("Item", code):
			continue
		it = frappe.db.get_value("Item", code, ["item_name", "image", "brand"], as_dict=True) or {}
		price = get_price(code)
		out.append({
			"brand": it.get("brand") or "",
			"name": it.get("item_name") or code,
			"sku": code,
			"price": money(price),
			"price_value": price,
			"image": it.get("image"),
			"badge": (r.get("badge") or "").strip(),
		})
	return out or None


@frappe.whitelist(allow_guest=True)
def subscribe(email=None):
	"""Newsletter sign-up endpoint used by the landing page (progressive JS)."""
	from frappe.utils import validate_email_address

	email = (email or "").strip()
	if not email or not validate_email_address(email):
		frappe.local.response["http_status_code"] = 400
		return {"ok": False, "message": "Please enter a valid business email address."}

	try:
		group = frappe.db.get_value("Email Group", {"title": "Website"}) or frappe.db.get_value("Email Group", {})
		if group and not frappe.db.exists("Email Group Member", {"email": email, "email_group": group}):
			frappe.get_doc(
				{"doctype": "Email Group Member", "email": email, "email_group": group}
			).insert(ignore_permissions=True)
	except Exception:
		# Subscribing should never hard-fail the visitor; log and carry on.
		frappe.log_error("Newsletter subscribe failed", frappe.get_traceback())

	return {"ok": True, "message": "Thanks! You're subscribed."}
