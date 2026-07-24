# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""One-time data setup for the laptop storefront rebrand.

This was originally applied by hand on the dev database (Item Group tree,
brand assignment, homepage/about copy) — this patch replays the same changes
so any other site (staging, production) gets them on its next `bench migrate`.
Every step checks before writing, so it's safe to run more than once.
"""

import frappe


def execute():
	_remove_unused_default_groups()
	_build_category_tree()
	_assign_items()
	_update_homepage_settings()
	_update_about_page_settings()


# --- Catalog: category tree + brand assignment ------------------------------

DEFAULT_GROUPS_TO_DROP = ("Products", "Raw Material", "Services", "Sub Assemblies", "Consumable")


def _remove_unused_default_groups():
	for g in DEFAULT_GROUPS_TO_DROP:
		if frappe.db.exists("Item Group", g) and not frappe.db.exists("Item", {"item_group": g}):
			frappe.delete_doc("Item Group", g, ignore_permissions=True, force=True)


def _ensure_group(name, parent, is_group):
	if frappe.db.exists("Item Group", name):
		return
	frappe.get_doc({
		"doctype": "Item Group",
		"item_group_name": name,
		"parent_item_group": parent,
		"is_group": is_group,
	}).insert(ignore_permissions=True)


def _build_category_tree():
	if not frappe.db.exists("Item Group", "All Item Groups"):
		return
	_ensure_group("Laptops", "All Item Groups", 1)
	_ensure_group("New Laptops", "Laptops", 0)
	_ensure_group("Refurbished Laptops", "Laptops", 0)
	_ensure_group("Accessories", "All Item Groups", 0)


# item_code -> (item_group, brand)
ITEM_ASSIGNMENTS = {
	"GMG-ROG-STRIX":      ("New Laptops", "Asus"),
	"PRM-MBP-16-M3":      ("New Laptops", "Apple"),
	"GMG-LEN-LEG5":       ("New Laptops", "Lenovo"),
	"GMG-MSI-RAID":       ("New Laptops", "MSI"),
	"BGT-LEN-IDP3":       ("New Laptops", "Lenovo"),
	"BGT-ACER-ASP3":      ("New Laptops", "Acer"),
	"PRM-SURF-STD2":      ("New Laptops", "Microsoft"),
	"GMG-HP-OMEN16":      ("New Laptops", "HP"),
	"PRM-TP-X1C":         ("New Laptops", "Lenovo"),
	"PRM-DELL-XPS13":     ("New Laptops", "Dell"),
	"BGT-HP-15S":         ("New Laptops", "HP"),
	"BGT-ASUS-VIVO":      ("New Laptops", "Asus"),
	"RFB-LEN-T480":       ("Refurbished Laptops", "Lenovo"),
	"RFB-DELL-LAT-7490":  ("Refurbished Laptops", "Dell"),
	"RFB-HP-840G5":       ("Refurbished Laptops", "HP"),
	"RFB-MAC-AIR-M1":     ("Refurbished Laptops", "Apple"),
	"ACC-LOGI-MX3":       ("Accessories", "Logitech"),
	"ACC-KEY-MECH":       ("Accessories", "Redragon"),
	"ACC-COOL-PAD":       ("Accessories", None),
	"ACC-USB-DOCK":       ("Accessories", None),
}


def _assign_items():
	if not frappe.db.exists("Item Group", "New Laptops"):
		return  # tree wasn't built (unexpected) — don't assign against groups that don't exist

	brands_needed = {b for _, b in ITEM_ASSIGNMENTS.values() if b}
	for b in brands_needed:
		if not frappe.db.exists("Brand", b):
			frappe.get_doc({"doctype": "Brand", "brand": b}).insert(ignore_permissions=True)

	for code, (group, brand) in ITEM_ASSIGNMENTS.items():
		if not frappe.db.exists("Item", code):
			continue  # this SKU doesn't exist on this site's catalog — nothing to tag
		values = {"item_group": group}
		if brand:
			values["brand"] = brand
		frappe.db.set_value("Item", code, values, update_modified=False)


# --- Homepage / About page copy ---------------------------------------------

def _update_homepage_settings():
	if not frappe.db.exists("DocType", "Ecommerce Homepage Settings"):
		return
	hp = frappe.get_doc("Ecommerce Homepage Settings")
	hp.hero_badge = "Pakistan's Laptop Store"
	hp.hero_heading = "Best Deals on"
	hp.hero_heading_highlight = "New & Refurbished Laptops"
	hp.hero_subtext = (
		"Genuine new and refurbished laptops from Dell, HP, Lenovo, Apple, Asus & "
		"more — with official warranty, nationwide delivery, and Cash on Delivery "
		"available across Pakistan."
	)
	hp.hero_button_text = "Shop Now"
	hp.hero_button_link = "/all-products"
	hp.hero_secondary_button_text = "Refurbished Deals"
	hp.hero_secondary_button_link = "/all-products?item_group=Refurbished Laptops"
	hp.topbar_free_freight_text = "Free Delivery All Over Pakistan"
	hp.topbar_distributor_text = "100% Genuine Products with Official Warranty"
	hp.search_placeholder = "Search by brand, model, or specs..."
	hp.categories_heading = "Shop by Category"
	hp.categories_subtext = (
		"Find the perfect laptop for study, gaming, or business — brand new or "
		"budget-friendly refurbished."
	)
	hp.best_sellers_heading = "Best Sellers"
	hp.promo_title = "Refurbished Laptops"
	hp.promo_subtitle = "Same Performance, Better Price"
	hp.promo_text = (
		"Fully tested, dependable laptops from Dell, HP, Lenovo & Apple at a "
		"fraction of the brand-new price — perfect for students and professionals."
	)
	hp.promo_button_text = "Shop Refurbished"
	hp.promo_button_link = "/all-products?item_group=Refurbished Laptops"
	hp.promo_note = "Limited Stock Available"
	hp.brands = "DELL\nHP\nLENOVO\nASUS\nACER\nAPPLE\nMSI\nMICROSOFT"
	hp.newsletter_title = "Get the Best Laptop Deals"
	hp.newsletter_subtitle = "Subscribe for new arrivals, price drops, and exclusive discounts."
	hp.save(ignore_permissions=True)


def _update_about_page_settings():
	if not frappe.db.exists("DocType", "About Page Settings"):
		return
	ap = frappe.get_doc("About Page Settings")
	ap.cta_heading = "Need Laptops in Bulk?"
	ap.cta_button_text = "Browse Laptops"
	ap.save(ignore_permissions=True)
