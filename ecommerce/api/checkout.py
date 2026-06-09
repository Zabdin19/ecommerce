# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Checkout API for the Sales Order-backed storefront cart."""

import frappe
from frappe import _

from ecommerce.api.cart import _so_get, get_cart_data, submit_cart_order

# Shipping options are app-defined (the site has no shipping-rule data).
SHIPPING_METHODS = [
	{"id": "standard", "title": "Standard (3-5 days)", "desc": "Default carrier selection for small items.", "price": "$45.00", "checked": True},
	{"id": "express", "title": "Express (1-2 days)", "desc": "Prioritized air freight for urgent supplies.", "price": "$120.00", "checked": False},
	{"id": "freight", "title": "Wholesale Logistics (Freight)", "desc": "LTL shipping for palletized heavy machinery.", "price": "$450.00", "checked": False},
]

PAYMENT_METHODS = [
	{"id": "card", "title": "Corporate Credit Card", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg>', "checked": True},
	{"id": "wire", "title": "Bank Wire Transfer", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 21h18M5 21V10m14 11V10M3 10l9-6 9 6M9 21v-6h6v6"/></svg>', "checked": False},
	{"id": "cod", "title": "Cash on Delivery", "icon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/></svg>', "checked": False},
]


def get_checkout_context():
	cart = get_cart_data()
	summary_items = [{"name": i["name"], "qty": i["qty"], "price": i["total"]} for i in cart["items"]]
	return {
		"summary_items": summary_items,
		"summary": cart["summary"],
		"shipping_methods": SHIPPING_METHODS,
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
