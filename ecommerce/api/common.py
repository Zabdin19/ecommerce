# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Shared helpers for the Ecommerce API layer: pricing, stock, money formatting."""

import frappe
from frappe.utils import flt

# Selling price list used for storefront prices. Falls back to the first enabled
# selling price list if this one does not exist on the site.
DEFAULT_PRICE_LIST = "Standard Selling"


def price_list():
	if frappe.db.exists("Price List", DEFAULT_PRICE_LIST):
		return DEFAULT_PRICE_LIST
	return frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name") or DEFAULT_PRICE_LIST


def currency():
	return frappe.db.get_value("Price List", price_list(), "currency") or "USD"


def money(value):
	"""Format a number as the storefront currency string, e.g. ``$1,249.00``."""
	return "${:,.2f}".format(flt(value))


def get_price(item_code):
	rate = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list(), "selling": 1},
		"price_list_rate",
	)
	return flt(rate)


def get_stock(item_code):
	qty = frappe.db.sql(
		"select sum(actual_qty) from `tabBin` where item_code=%s", item_code
	)
	return flt(qty[0][0]) if qty and qty[0][0] else 0.0
