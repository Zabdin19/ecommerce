# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the customer wishlist page (`/wishlist`).

Requires a valid ecommerce customer token; guests are redirected to login.
Items come from ``ecommerce.api.wishlist`` and are customer-specific.
"""

import frappe

from ecommerce.api import wishlist as wishlist_api
from ecommerce.api.auth import get_current_customer_session
from ecommerce.website_context import get_chrome

no_cache = 1


def get_context(context):
	if not get_current_customer_session():
		frappe.local.flags.redirect_location = "/sign-in?redirect=/wishlist"
		raise frappe.Redirect

	data = wishlist_api.get_wishlist()

	context.chrome = get_chrome()
	context.items = data["items"]
	context.wishlist_count = data["count"]
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"My Wishlist | {context.chrome.brand}"
	context.metatags = {"title": context.title, "description": "Your saved products."}
	return context
