# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the shopping cart page (`/cart`). Backed by the live cart."""

import frappe

from ecommerce.api import cart as cart_api
from ecommerce.website_context import get_chrome

no_cache = 1


def get_context(context):
	data = cart_api.get_cart_data()

	context.chrome = get_chrome()
	context.cart_items = data["items"]
	context.item_count = data["item_count"]
	context.shipping_value = data["shipping_value"]
	context.tax_rate = data["tax_rate"]
	context.summary = data["summary"]
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"Shopping Cart | {context.chrome.brand}"
	context.metatags = {"title": context.title, "description": "Review the items in your cart."}
	return context
