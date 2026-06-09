# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Public storefront API.

Exposes spec-named whitelisted endpoints under ``ecommerce.api.*`` that delegate
to the focused submodules (auth, cart, checkout, account). Frappe v15 compatible.
"""

import json

import frappe

from ecommerce.api import auth as _auth
from ecommerce.api import cart as _cart
from ecommerce.api import checkout as _checkout
from ecommerce.api import wishlist as _wishlist


# --- Auth -------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def register_customer(first_name=None, last_name=None, email=None, phone=None,
		password=None, confirm_password=None):
	"""Register a storefront customer account. Does NOT create a Frappe User."""
	return _auth.register(
		first_name=first_name, last_name=last_name, email=email,
		phone=phone, password=password, confirm_password=confirm_password,
	)


@frappe.whitelist(allow_guest=True)
def login_customer(email=None, password=None, cart=None):
	"""Authenticate by ecommerce customer password and set only ecommerce token."""
	info = _auth.login(email=email, password=password)
	try:
		if info.get("ok") and cart:
			sync_cart_after_login(cart)
	except Exception:
		frappe.log_error("cart sync on customer login failed", frappe.get_traceback())
	return info


@frappe.whitelist(allow_guest=True)
def logout_customer():
	"""End only the ecommerce customer token session."""
	return _auth.logout()


@frappe.whitelist(allow_guest=True)
def get_logged_in_customer():
	"""Return storefront login state from ecommerce_customer_token only."""
	return _auth.get_logged_in_customer()


# --- Cart sync --------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def sync_cart_after_login(items=None):
	"""Merge a client-side cart payload ([{item_code, qty}]) into the draft Sales Order cart."""
	if not _auth.get_current_customer_session():
		return {"ok": False, "message": "Not logged in."}
	if isinstance(items, str):
		items = json.loads(items or "[]")
	items = items or []

	for it in items:
		code = it.get("item_code")
		qty = frappe.utils.cint(it.get("qty") or 1)
		if not code or qty <= 0:
			continue
		_cart.add_to_cart(code, qty)
	return _cart.get_cart()


# --- Sales Order cart --------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def add_to_cart(item_code, qty=1):
	return _cart.add_to_cart(item_code=item_code, qty=qty)


@frappe.whitelist(allow_guest=True)
def get_cart():
	return _cart.get_cart()


@frappe.whitelist(allow_guest=True)
def update_cart_item(item_code, qty):
	return _cart.update_cart_item(item_code=item_code, qty=qty)


@frappe.whitelist(allow_guest=True)
def remove_cart_item(item_code):
	return _cart.remove_cart_item(item_code=item_code)


@frappe.whitelist(allow_guest=True)
def clear_cart():
	return _cart.clear_cart()


@frappe.whitelist(allow_guest=True)
def submit_cart_order(address=None, shipping_method=None, payment_method=None):
	return _cart.submit_cart_order(address=address, shipping_method=shipping_method, payment_method=payment_method)


# --- Wishlist (customer-specific) ------------------------------------------

@frappe.whitelist(allow_guest=True)
def add_to_wishlist(item_code):
	return _wishlist.add_to_wishlist(item_code=item_code)


@frappe.whitelist(allow_guest=True)
def remove_from_wishlist(item_code):
	return _wishlist.remove_from_wishlist(item_code=item_code)


@frappe.whitelist(allow_guest=True)
def toggle_wishlist(item_code):
	return _wishlist.toggle_wishlist(item_code=item_code)


@frappe.whitelist(allow_guest=True)
def get_wishlist():
	return _wishlist.get_wishlist()


# --- Orders (delegate to checkout) -----------------------------------------

@frappe.whitelist(allow_guest=True)
def create_sales_order(address=None, shipping_method=None, payment_method=None):
	return _checkout.create_sales_order(address=address, shipping_method=shipping_method, payment_method=payment_method)


@frappe.whitelist(allow_guest=True)
def submit_sales_order(name):
	return _checkout.submit_sales_order(name)
