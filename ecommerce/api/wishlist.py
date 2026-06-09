# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Customer-specific wishlist, keyed by the ecommerce customer token (NOT the
Frappe session). Guests are blocked with a PermissionError so the frontend can
redirect them to the login page."""

import frappe
from frappe import _

from ecommerce.api.auth import get_current_customer_session, require_customer_session
from ecommerce.api.common import get_price, get_stock, money

WISHLIST_DOCTYPE = "Ecommerce Wishlist Item"


def _customer():
	"""Resolve the logged-in customer from the token, or raise 403."""
	return require_customer_session().customer


def _row_name(customer, item_code):
	return frappe.db.get_value(WISHLIST_DOCTYPE, {"customer": customer, "item_code": item_code}, "name")


def is_in_wishlist(item_code):
	"""Best-effort check used by the product controller (never raises)."""
	session = get_current_customer_session()
	if not session or not item_code:
		return False
	return bool(_row_name(session.customer, item_code))


def wishlist_count():
	session = get_current_customer_session()
	if not session:
		return 0
	return frappe.db.count(WISHLIST_DOCTYPE, {"customer": session.customer})


def _add(customer, item_code):
	"""Insert a wishlist row if absent (no duplicates). Returns True if added."""
	if _row_name(customer, item_code):
		return False
	meta = frappe.db.get_value("Item", item_code, ["item_name", "image"], as_dict=True) or {}
	frappe.get_doc({
		"doctype": WISHLIST_DOCTYPE,
		"customer": customer,
		"item_code": item_code,
		"item_name": meta.get("item_name"),
		"image": meta.get("image"),
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	return True


def _remove(customer, item_code):
	name = _row_name(customer, item_code)
	if name:
		frappe.delete_doc(WISHLIST_DOCTYPE, name, ignore_permissions=True, force=True)
		frappe.db.commit()
		return True
	return False


# --- whitelisted endpoints --------------------------------------------------

@frappe.whitelist(allow_guest=True)
def add_to_wishlist(item_code):
	customer = _customer()
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))
	added = _add(customer, item_code)
	return {
		"ok": True,
		"in_wishlist": True,
		"added": added,
		"count": wishlist_count(),
		"message": "Added to wishlist" if added else "Already in your wishlist",
	}


@frappe.whitelist(allow_guest=True)
def remove_from_wishlist(item_code):
	customer = _customer()
	_remove(customer, item_code)
	return {"ok": True, "in_wishlist": False, "count": wishlist_count(), "message": "Removed from wishlist"}


@frappe.whitelist(allow_guest=True)
def toggle_wishlist(item_code):
	"""Add the item if absent, remove it if present — for the heart button."""
	customer = _customer()
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item not found"))
	if _row_name(customer, item_code):
		_remove(customer, item_code)
		return {"ok": True, "in_wishlist": False, "count": wishlist_count(), "message": "Removed from wishlist"}
	_add(customer, item_code)
	return {"ok": True, "in_wishlist": True, "count": wishlist_count(), "message": "Added to wishlist"}


@frappe.whitelist(allow_guest=True)
def get_wishlist():
	customer = _customer()
	rows = frappe.get_all(
		WISHLIST_DOCTYPE,
		filters={"customer": customer},
		fields=["item_code", "item_name", "image"],
		order_by="creation desc",
	)
	items = []
	for r in rows:
		if not frappe.db.exists("Item", r.item_code):
			continue
		items.append({
			"item_code": r.item_code,
			"name": r.item_name or r.item_code,
			"sku": r.item_code,
			"image": r.image,
			"price": money(get_price(r.item_code)),
			"in_stock": get_stock(r.item_code) > 0,
		})
	return {"items": items, "count": len(items)}
