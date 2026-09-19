# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Checkout API for the Sales Order-backed storefront cart."""

import frappe
from frappe import _

from ecommerce.api.cart import _so_get, get_cart_data, submit_cart_order
# The cart currently has one configured shipping charge. Do not advertise
# delivery times or geographic coverage until real Shipping Rules are wired in.
SHIPPING_METHODS = [
	{"id": "standard", "title": "Shipping arranged after order review", "desc": "Delivery timing and charges are not included in the online total.", "price_value": 0.00, "checked": True},
]

PAYMENT_METHODS = [
	{"id": "confirmation", "title": "Payment details to be confirmed", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 5h16v14H4zM8 9h8M8 13h5"/></svg>', "checked": True},
]


def get_checkout_context():
	cart = get_cart_data()
	summary_items = [{"name": i["name"], "qty": i["qty"], "price": i["total"]} for i in cart["items"]]
	shipping_methods = [dict(m, price="To confirm") for m in SHIPPING_METHODS]
	return {
		"summary_items": summary_items,
		"summary": cart["summary"],
		"shipping_methods": shipping_methods,
		"payment_methods": PAYMENT_METHODS,
	}


def _require_customer():
	"""Require the independent ecommerce customer token and return customer id."""
	from ecommerce.api.auth import require_customer_session
	return require_customer_session().customer


@frappe.whitelist(allow_guest=True)
def create_sales_order(address=None, shipping_method=None, payment_method=None):
	"""Compatibility endpoint: return the existing Draft Sales Order cart only."""
	customer = _require_customer()
	order = _so_get(customer, create=False)
	if not order or not order.items:
		frappe.throw(_("Your cart is empty."))
	if order.customer != customer:
		frappe.throw(_("This order does not belong to your account."), frappe.PermissionError)
	return {"ok": True, "name": order.name}


@frappe.whitelist(allow_guest=True)
def submit_sales_order(name):
	"""Compatibility endpoint: submit the current Draft Sales Order cart."""
	customer = _require_customer()
	order = _so_get(customer, create=False)
	if not order or order.name != name or order.customer != customer:
		frappe.throw(_("This order does not belong to your account."), frappe.PermissionError)
	return submit_cart_order()
