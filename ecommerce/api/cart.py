# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Storefront cart.

Two-tier so that **Add to Cart works without login**:

* Guests       → an ``Ecommerce Cart`` keyed by the ``ecom_cart_token`` cookie.
* Logged-in    → the customer's Draft ERPNext Sales Order.

On login the guest cookie cart is merged into the customer's Draft Sales Order
(see :func:`merge_guest_cart_into_order`) so items survive the login boundary.
Checkout still requires a customer session (handled by the checkout flow).
"""

import uuid

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, nowdate

from ecommerce.api.auth import get_current_customer_session, require_customer_session
from ecommerce.api.common import get_price, money
from ecommerce.api.common import price_list as default_price_list

SHIPPING_VALUE = 45.0
CART_COOKIE = "ecom_cart_token"

DEMO_COUPONS = {"WELCOME10": 10, "BULK15": 15}


def _delivery_date():
	"""Delivery date as a ``datetime.date`` (NOT a string) — ERPNext runs
	``max()`` over every row's delivery_date, which fails if types are mixed."""
	return getdate(add_days(nowdate(), 7))


# --- tax (from the ERPNext Sales Taxes and Charges Template) ----------------

def _default_tax_template(company):
	"""The Sales Taxes and Charges Template ERPNext applies to a Sales Order for
	this company (its default), mirroring the backend behaviour."""
	if not company:
		return None
	return (
		frappe.db.get_value("Sales Taxes and Charges Template", {"company": company, "is_default": 1, "disabled": 0}, "name")
		or frappe.db.get_value("Sales Taxes and Charges Template", {"company": company, "is_default": 1}, "name")
		or frappe.db.get_value("Sales Taxes and Charges Template", {"company": company, "disabled": 0}, "name")
	)


def _tax_label(rate):
	return f"Tax ({rate:g}%)" if rate else "Tax"


def _template_rate_label(company):
	"""(rate, label) from the company's default tax template — used for the guest
	estimate, where there is no Sales Order yet to calculate against."""
	template = _default_tax_template(company)
	if not template:
		return 0.0, "Tax"
	rate = sum(flt(r.rate) for r in frappe.get_all(
		"Sales Taxes and Charges", filters={"parent": template}, fields=["rate"]))
	return rate, _tax_label(rate)


def _apply_taxes(so):
	"""Attach the company's default Sales Taxes and Charges Template so ERPNext
	calculates tax on save exactly like a backend-created Sales Order."""
	if so.get("taxes_and_charges") and so.get("taxes"):
		return
	template = _default_tax_template(so.company)
	if not template:
		return
	from erpnext.controllers.accounts_controller import get_taxes_and_charges

	so.taxes_and_charges = template
	so.set("taxes", get_taxes_and_charges("Sales Taxes and Charges Template", template))


# --- shared payload ---------------------------------------------------------

def _finalize(items, subtotal, count, sales_order, tax_amount, tax_rate, tax_label):
	shipping = SHIPPING_VALUE if subtotal else 0.0
	total = subtotal + shipping + flt(tax_amount)
	return {
		"items": items,
		"item_count": count,
		"sales_order": sales_order,
		"shipping_value": shipping,
		"tax_rate": tax_rate,
		"summary": {
			"subtotal": money(subtotal),
			"shipping": money(shipping),
			"tax_label": tax_label,
			"tax": money(tax_amount),
			"total": money(total),
		},
	}


def _item_row(item_code, item_name, qty, rate, amount):
	meta = frappe.db.get_value("Item", item_code, ["item_name", "image"], as_dict=True) or {}
	return {
		"item_code": item_code,
		"name": item_name or meta.get("item_name") or item_code,
		"sku": item_code,
		"variant": "",
		"qty": cint(qty),
		"unit_value": flt(rate),
		"unit": money(rate),
		"total": money(amount),
		"image": meta.get("image"),
	}


# --- company / warehouse ----------------------------------------------------

def _company():
	company = frappe.defaults.get_global_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		frappe.throw(_("Default company is not configured."))
	return company


def _warehouse(company=None):
	company = company or _company()
	return (
		frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
		or frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
	)


# === Logged-in cart: Draft Sales Order ======================================

def _current_customer():
	return require_customer_session().customer


def _find_draft_order(customer):
	rows = frappe.get_all(
		"Sales Order",
		filters={"customer": customer, "docstatus": 0},
		fields=["name"],
		order_by="modified desc",
		page_length=1,
	)
	return rows[0].name if rows else None


def _so_get(customer, create=False):
	"""Get (or build) the customer's Draft Sales Order. No session required."""
	name = _find_draft_order(customer)
	if name:
		return frappe.get_doc("Sales Order", name)
	if not create:
		return None
	company = _company()
	warehouse = _warehouse(company)
	so = frappe.new_doc("Sales Order")
	so.customer = customer
	so.company = company
	so.transaction_date = nowdate()
	so.delivery_date = _delivery_date()
	so.selling_price_list = default_price_list()
	if warehouse:
		so.set_warehouse = warehouse
	return so


def _save_order(order):
	if not order.items and not order.is_new():
		name = order.name
		frappe.delete_doc("Sales Order", name, ignore_permissions=True, force=True)
		frappe.db.commit()
		return None
	_apply_taxes(order)
	order.flags.ignore_permissions = True
	if order.is_new():
		order.insert(ignore_permissions=True)
	else:
		order.save(ignore_permissions=True)
	frappe.db.commit()
	return order


def _serialize(order):
	items, subtotal, count = [], 0.0, 0
	if order:
		for row in order.items:
			amount = flt(row.amount) or flt(row.rate) * cint(row.qty)
			subtotal += amount
			count += cint(row.qty)
			items.append(_item_row(row.item_code, row.item_name, row.qty, row.rate, amount))

	if not order:
		tax_amount, rate, label = 0.0, 0.0, "Tax"
	elif order.get("taxes"):
		# Authoritative: amount ERPNext computed on the Sales Order itself.
		tax_amount = flt(order.total_taxes_and_charges)
		rate = sum(flt(t.rate) for t in order.taxes)
		label = _tax_label(rate)
	else:
		rate, label = _template_rate_label(order.company)
		tax_amount = subtotal * rate / 100
	return _finalize(items, subtotal, count, order.name if order else None, tax_amount, rate, label)


def _so_add(customer, item_code, qty):
	order = _so_get(customer, create=True)
	warehouse = _warehouse(order.company)
	rate = get_price(item_code)
	row = next((r for r in order.items if r.item_code == item_code), None)
	if row:
		row.qty = cint(row.qty) + qty
		row.rate = rate
		row.price_list_rate = rate
		if warehouse:
			row.warehouse = warehouse
	else:
		order.append("items", {
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
			"price_list_rate": rate,
			"warehouse": warehouse,
			"delivery_date": _delivery_date(),
		})
	return _serialize(_save_order(order))


def _so_update(customer, item_code, qty):
	order = _so_get(customer, create=False)
	if not order:
		return _serialize(None)
	row = next((r for r in order.items if r.item_code == item_code), None)
	if row:
		if qty <= 0:
			order.remove(row)
		else:
			rate = get_price(item_code)
			row.qty = qty
			row.rate = rate
			row.price_list_rate = rate
			warehouse = _warehouse(order.company)
			if warehouse:
				row.warehouse = warehouse
		order = _save_order(order)
	return _serialize(order)


def _so_remove(customer, item_code):
	order = _so_get(customer, create=False)
	if order:
		row = next((r for r in order.items if r.item_code == item_code), None)
		if row:
			order.remove(row)
			order = _save_order(order)
	return _serialize(order)


def _so_clear(customer):
	order = _so_get(customer, create=False)
	if order:
		order.set("items", [])
		order = _save_order(order)
	return _serialize(order)


# === Guest cart: Ecommerce Cart (cookie) ====================================

def _guest_token():
	req = getattr(frappe.local, "request", None)
	return req.cookies.get(CART_COOKIE) if req is not None else None


def _resolve_guest_cart(create=False):
	token = _guest_token()
	name = frappe.db.get_value("Ecommerce Cart", {"cart_token": token}) if token else None
	if name:
		return frappe.get_doc("Ecommerce Cart", name)
	if not create:
		return None
	token = token or uuid.uuid4().hex
	cart = frappe.new_doc("Ecommerce Cart")
	cart.cart_token = token
	cm = getattr(frappe.local, "cookie_manager", None)
	if cm:
		cm.set_cookie(CART_COOKIE, token, max_age=30 * 24 * 3600, httponly=True, samesite="Lax")
	cart.insert(ignore_permissions=True)
	return cart


def _save_guest_cart(cart):
	if hasattr(cart, "recalculate"):
		cart.recalculate()
	cart.save(ignore_permissions=True)
	frappe.db.commit()
	return cart


def _serialize_guest(cart):
	items, subtotal, count = [], 0.0, 0
	if cart:
		for row in cart.items:
			amount = flt(row.amount) or flt(row.rate) * cint(row.qty)
			subtotal += amount
			count += cint(row.qty)
			items.append(_item_row(row.item_code, row.item_name, row.qty, row.rate, amount))
	# No Sales Order yet for a guest — estimate using the same tax template the
	# Sales Order will apply after login (rate × net total).
	rate, label = _template_rate_label(_company())
	tax_amount = subtotal * rate / 100
	return _finalize(items, subtotal, count, None, tax_amount, rate, label)


def _guest_add(item_code, qty):
	cart = _resolve_guest_cart(create=True)
	rate = get_price(item_code)
	row = next((r for r in cart.items if r.item_code == item_code), None)
	if row:
		row.qty = cint(row.qty) + qty
		row.rate = rate
	else:
		meta = frappe.db.get_value("Item", item_code, ["item_name", "image", "stock_uom"], as_dict=True) or {}
		cart.append("items", {
			"item_code": item_code,
			"item_name": meta.get("item_name"),
			"image": meta.get("image"),
			"uom": meta.get("stock_uom"),
			"qty": qty,
			"rate": rate,
		})
	return _serialize_guest(_save_guest_cart(cart))


def _guest_update(item_code, qty):
	cart = _resolve_guest_cart(create=False)
	if not cart:
		return _serialize_guest(None)
	row = next((r for r in cart.items if r.item_code == item_code), None)
	if row:
		if qty <= 0:
			cart.remove(row)
		else:
			row.qty = qty
			row.rate = get_price(item_code)
		cart = _save_guest_cart(cart)
	return _serialize_guest(cart)


def _guest_remove(item_code):
	cart = _resolve_guest_cart(create=False)
	if cart:
		row = next((r for r in cart.items if r.item_code == item_code), None)
		if row:
			cart.remove(row)
			cart = _save_guest_cart(cart)
	return _serialize_guest(cart)


def _guest_clear():
	cart = _resolve_guest_cart(create=False)
	if cart:
		cart.set("items", [])
		cart = _save_guest_cart(cart)
	return _serialize_guest(cart)


# === Login merge ============================================================

def merge_guest_cart_into_order(customer):
	"""Fold the guest cookie cart into ``customer``'s Draft Sales Order, then
	drop the guest cart + cookie. Called right after a successful login."""
	if not customer:
		return
	cart = _resolve_guest_cart(create=False)
	if not cart or not cart.items:
		return

	order = _so_get(customer, create=True)
	warehouse = _warehouse(order.company)
	for g in cart.items:
		if not g.item_code or not frappe.db.exists("Item", g.item_code):
			continue
		rate = get_price(g.item_code)
		row = next((r for r in order.items if r.item_code == g.item_code), None)
		if row:
			row.qty = cint(row.qty) + cint(g.qty)
			row.rate = rate
			row.price_list_rate = rate
			if warehouse:
				row.warehouse = warehouse
		else:
			order.append("items", {
				"item_code": g.item_code,
				"qty": cint(g.qty),
				"rate": rate,
				"price_list_rate": rate,
				"warehouse": warehouse,
				"delivery_date": _delivery_date(),
			})
	_save_order(order)

	frappe.delete_doc("Ecommerce Cart", cart.name, ignore_permissions=True, force=True)
	frappe.db.commit()
	cm = getattr(frappe.local, "cookie_manager", None)
	if cm and hasattr(cm, "delete_cookie"):
		cm.delete_cookie(CART_COOKIE)


# === Server-side context (chrome badge + /cart page) ========================

def get_cart_data():
	session = get_current_customer_session()
	if session:
		return _serialize(_so_get(session.customer, create=False))
	return _serialize_guest(_resolve_guest_cart(create=False))


def cart_count():
	session = get_current_customer_session()
	if session:
		order = _so_get(session.customer, create=False)
		return sum(cint(r.qty) for r in order.items) if order else 0
	cart = _resolve_guest_cart(create=False)
	return sum(cint(r.qty) for r in cart.items) if cart else 0


# === Whitelisted endpoints ==================================================

@frappe.whitelist(allow_guest=True)
def get_cart():
	return get_cart_data()


@frappe.whitelist(allow_guest=True)
def add_to_cart(item_code, qty=1):
	qty = cint(qty)
	if qty <= 0:
		frappe.throw(_("Quantity must be greater than zero."))
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))
	if flt(get_price(item_code)) <= 0:
		frappe.throw(_("This item is not available for purchase."))

	session = get_current_customer_session()
	if session:
		return _so_add(session.customer, item_code, qty)
	return _guest_add(item_code, qty)


@frappe.whitelist(allow_guest=True)
def update_cart_item(item_code, qty):
	qty = cint(qty)
	if qty < 0:
		frappe.throw(_("Quantity cannot be negative."))
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))

	session = get_current_customer_session()
	if session:
		return _so_update(session.customer, item_code, qty)
	return _guest_update(item_code, qty)


@frappe.whitelist(allow_guest=True)
def remove_cart_item(item_code):
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))

	session = get_current_customer_session()
	if session:
		return _so_remove(session.customer, item_code)
	return _guest_remove(item_code)


@frappe.whitelist(allow_guest=True)
def clear_cart():
	session = get_current_customer_session()
	if session:
		return _so_clear(session.customer)
	return _guest_clear()


@frappe.whitelist(allow_guest=True)
def apply_coupon(code):
	code = (code or "").strip().upper()
	if not get_cart_data()["items"]:
		return {"ok": False, "message": "Your cart is empty."}
	if code not in DEMO_COUPONS:
		return {"ok": False, "message": "Invalid coupon code."}
	return {"ok": True, "message": f"Coupon {code} applied — {DEMO_COUPONS[code]}% off at checkout."}


@frappe.whitelist(allow_guest=True)
def submit_cart_order(address=None, shipping_method=None, payment_method=None):
	"""Submit the existing Draft Sales Order. Requires a customer session."""
	customer = _current_customer()
	order = _so_get(customer, create=False)
	if not order or not order.items:
		frappe.throw(_("Your cart is empty."))
	if order.customer != customer:
		frappe.throw(_("This order does not belong to your account."), frappe.PermissionError)

	warehouse = _warehouse(order.company)
	for row in order.items:
		qty = cint(row.qty)
		if not row.item_code or not frappe.db.exists("Item", row.item_code) or qty <= 0:
			frappe.throw(_("Cart contains an invalid item."))
		rate = get_price(row.item_code)
		row.rate = rate
		row.price_list_rate = rate
		if warehouse:
			row.warehouse = warehouse

	_apply_taxes(order)
	order.flags.ignore_permissions = True
	order.save(ignore_permissions=True)
	order.submit()
	frappe.db.commit()
	return {"ok": True, "order": order.name}
