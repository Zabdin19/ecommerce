# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the product detail page (`/product`).

Renders a real ERPNext Item via ``ecommerce.api.products``. Pass
``?item=<item_code>``; with no item it shows the first available product. The
delivery perks are app-defined; reviews come from a real source when available
(none on this site yet, so the Reviews tab shows an empty state)."""

import frappe

from ecommerce.api import products
from ecommerce.api import wishlist
from ecommerce.website_context import get_chrome

no_cache = 1

DELIVERY_CARDS = [
	{
		"title": "Free Bulk Delivery",
		"text": "On orders over $15,000 to logistics hubs.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7h11v8H3z"/><path d="M14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/></svg>',
	},
	{
		"title": "3 Year Manufacturer Warranty",
		"text": "Includes on-site maintenance support.",
		"icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="m9 12 2 2 4-4"/></svg>',
	},
]


def get_context(context):
	chrome = get_chrome()
	item_code = frappe.form_dict.get("item")
	if not item_code:
		item_code = frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1}, "name")

	detail = products.get_product_detail(item_code)
	if not detail:
		frappe.local.flags.redirect_location = "/all-products"
		raise frappe.Redirect

	context.chrome = chrome
	context.product = detail["product"]
	context.in_wishlist = wishlist.is_in_wishlist(detail["product"]["item_code"])
	context.specs = detail["specs"]
	context.reviews = []  # no review data on this site yet
	context.related = detail["related"]
	context.delivery_cards = DELIVERY_CARDS
	context.breadcrumbs = detail["breadcrumbs"]
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1

	context.title = f"{detail['product']['name']} | {chrome.brand}"
	context.description = frappe.utils.strip_html(detail["product"]["description_html"] or "")[:160]
	context.metatags = {
		"title": context.title,
		"description": context.description,
		"image": (detail["product"]["gallery"][0] if detail["product"]["gallery"] else "") or "",
		"og:type": "product",
	}
	return context
