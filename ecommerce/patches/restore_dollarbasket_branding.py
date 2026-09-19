# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Restore DollarBasket identity in database-backed website settings.

Only blank values and exact/recognisable copy from the two previous storefront
themes are changed. This keeps unrelated administrator customisations intact
and makes the rebrand reproducible on each site through ``bench migrate``.
"""

import frappe


def execute():
	_update_website_settings()
	_update_homepage_settings()
	_update_about_settings()
	_update_contact_settings()


def _legacy(value):
	text = (value or "").lower()
	return any(term in text for term in ("lapmarkaz", "lap markaz", "laptop store", "industrial supply"))


def _replace(doc, fieldname, value, legacy_values=()):
	current = (doc.get(fieldname) or "").strip()
	if not current or current in legacy_values or _legacy(current):
		doc.set(fieldname, value)


def _update_website_settings():
	ws = frappe.get_doc("Website Settings")
	_replace(ws, "app_name", "DollarBasket", ("Frappe", "ERPNext", "Ecommerce"))
	_replace(ws, "copyright", "DollarBasket. All Rights Reserved.")
	_replace(ws, "custom_footer_description", (
		"DollarBasket is a B2B ecommerce platform for business customers, retailers, "
		"resellers, and wholesale buyers. Browse the catalogue or request a quote "
		"for a bulk requirement."
	))
	_replace(ws, "custom_meta_title", "DollarBasket | B2B Ecommerce for Business Buyers")
	_replace(ws, "custom_meta_description", (
		"Browse the DollarBasket business product catalogue, place an order, or "
		"request a quote for a bulk requirement."
	))
	_replace(ws, "custom_meta_keywords", (
		"DollarBasket, B2B ecommerce, business purchasing, bulk orders, wholesale catalogue"
	))
	if not ws.get("favicon") or _legacy(ws.get("favicon")):
		ws.favicon = "/assets/ecommerce/images/favicon.svg"
	if not ws.get("home_page") or ws.get("home_page") == "home":
		ws.home_page = "storefront"
	ws.save(ignore_permissions=True)


def _update_homepage_settings():
	if not frappe.db.exists("DocType", "Ecommerce Homepage Settings"):
		return
	hp = frappe.get_doc("Ecommerce Homepage Settings")
	mapping = {
		"hero_badge": ("B2B ECOMMERCE", ("Established 1984", "Pakistan's Laptop Store")),
		"hero_heading": ("Business buying,", ("The Gold Standard in", "Best Deals on")),
		"hero_heading_highlight": ("made straightforward", ("Industrial Supply", "New & Refurbished Laptops")),
		"hero_subtext": ("Browse products, place business orders, or send a quote request for a bulk requirement through a professional purchasing experience.", ()),
		"hero_button_text": ("Browse Catalogue", ("Shop Now",)),
		"hero_secondary_button_text": ("Request a Quote", ("Refurbished Deals",)),
		"hero_secondary_button_link": ("/request-quote", ("/sign-in", "/all-products?item_group=Refurbished Laptops")),
		"topbar_free_freight_text": ("Built for business purchasing", ("Free freight on orders over $1,500", "Free Delivery All Over Pakistan")),
		"topbar_distributor_text": ("Bulk order quote requests available", ("Official B2B Distributor", "100% Genuine Products with Official Warranty")),
		"search_placeholder": ("Search by product name, SKU, or brand…", ("Search by SKU, Model, or Component…", "Search by brand, model, or specs...")),
		"categories_heading": ("Ways to Buy", ("Essential Categories", "Shop by Category")),
		"categories_subtext": ("Use the online catalogue for standard orders or contact our team about a bulk requirement.", ()),
		"best_sellers_heading": ("Featured Products", ("Best Sellers",)),
		"promo_title": ("Bulk Purchasing", ("Precision Performance", "Refurbished Laptops")),
		"promo_subtitle": ("Request a Business Quote", ("Now Within Reach", "Same Performance, Better Price")),
		"promo_text": ("Share your product and quantity requirements so the team can review your enquiry.", ()),
		"promo_button_text": ("Request a Quote", ("View Special Offer", "Shop Refurbished")),
		"promo_button_link": ("/request-quote", ("#", "/all-products?item_group=Refurbished Laptops")),
		"promo_note": ("For business and wholesale enquiries", ("Ends in 48 hours", "Limited Stock Available")),
		"newsletter_title": ("Stay Informed", ("Get the Best Laptop Deals",)),
		"newsletter_subtitle": ("Subscribe for catalogue and product updates from DollarBasket.", ()),
	}
	for fieldname, (value, old_values) in mapping.items():
		_replace(hp, fieldname, value, old_values)
	hp.save(ignore_permissions=True)


def _update_about_settings():
	if not frappe.db.exists("DocType", "About Page Settings"):
		return
	ap = frappe.get_doc("About Page Settings")
	_replace(ap, "page_title", "About DollarBasket", ("About Us",))
	_replace(ap, "page_subtitle", "DollarBasket is a B2B ecommerce platform for business customers, retailers, resellers, and wholesale buyers.")
	_replace(ap, "story_body", (
		"<p>DollarBasket provides a straightforward online purchasing experience for "
		"organisations and trade buyers. Customers can browse the live product catalogue, "
		"manage an account and place orders through the storefront.</p><p>Businesses with "
		"larger requirements can submit a quote request with their product, quantity and "
		"company details.</p>"
	))
	_replace(ap, "mission_text", "To make business purchasing clear and efficient through a focused B2B ecommerce experience.")
	_replace(ap, "vision_text", "To help business customers source and order products with confidence.")
	_replace(ap, "cta_heading", "Planning a bulk purchase?", ("Need Laptops in Bulk?", "Ready to partner with us?"))
	_replace(ap, "cta_text", "Send your product and quantity requirements through the business quote form.")
	_replace(ap, "cta_button_text", "Request a Quote", ("Browse Laptops", "Browse Catalog"))
	_replace(ap, "cta_button_link", "/request-quote", ("/all-products",))
	ap.save(ignore_permissions=True)


def _update_contact_settings():
	if not frappe.db.exists("DocType", "Contact Page Settings"):
		return
	cp = frappe.get_doc("Contact Page Settings")
	_replace(cp, "page_subtitle", "Have a question about a product, an order, or a bulk requirement? Send the DollarBasket team a message.")
	_replace(cp, "form_subtitle", "Provide your contact details and a short description of your request.")
	if _legacy(cp.get("email")):
		cp.email = ""
	cp.save(ignore_permissions=True)
