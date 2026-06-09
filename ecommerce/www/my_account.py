# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the customer profile dashboard (`/my-account`).

Requires an ecommerce customer token. Data comes from the token-linked Customer,
Sales Orders and Address via ``ecommerce.api.account``.
"""

import frappe

from ecommerce.api import account
from ecommerce.api.auth import get_current_customer_session
from ecommerce.website_context import get_chrome

no_cache = 1


def get_context(context):
	if not get_current_customer_session():
		frappe.local.flags.redirect_location = "/sign-in"
		raise frappe.Redirect

	data = account.get_dashboard()

	context.chrome = get_chrome()
	context.account = data["account"]
	context.address = data["address"]
	context.nav = data["nav"]
	context.stats = data["stats"]
	context.recent_orders = data["recent_orders"]
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"My Account | {context.chrome.brand}"
	context.metatags = {"title": context.title, "description": "Manage your procurement account."}
	return context
