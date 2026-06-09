# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the checkout page (`/checkout`). Summary from the live cart."""

import frappe

from ecommerce.api import checkout as checkout_api
from ecommerce.api.auth import get_current_customer_session
from ecommerce.website_context import get_chrome

no_cache = 1


def get_context(context):
	# Checkout requires the independent ecommerce customer token.
	if not get_current_customer_session():
		frappe.local.flags.redirect_location = "/sign-in?redirect=/checkout"
		raise frappe.Redirect

	data = checkout_api.get_checkout_context()

	context.chrome = get_chrome()
	context.steps = [("1", "Shipping", True), ("2", "Payment", False), ("3", "Review", False)]
	context.shipping_methods = data["shipping_methods"]
	context.payment_methods = data["payment_methods"]
	context.summary_items = data["summary_items"]
	context.summary = data["summary"]
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"Checkout | {context.chrome.brand}"
	context.metatags = {"title": context.title, "description": "Complete your order."}
	return context
