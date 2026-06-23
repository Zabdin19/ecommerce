# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Catalog API: list/search/filter products, categories, brands, product detail.

Sources data from ERPNext **Item** (+ Item Price, Bin, Item Group). Ratings are
a deterministic placeholder because the site has no review data; swap
``_rating`` for a real source (e.g. an Item Review doctype) when available.
"""

import math
import urllib.parse

import frappe
from frappe.utils import cint

from ecommerce.api.common import get_price, get_stock, money, price_list

PAGE_SIZE = 12


def _price_map():
	"""Return ``{item_code: price_list_rate}`` for the storefront price list in one query."""
	rows = frappe.get_all(
		"Item Price",
		filters={"price_list": price_list(), "selling": 1},
		fields=["item_code", "price_list_rate"],
	)
	return {r.item_code: r.price_list_rate for r in rows}


def _rating(item_code):
	h = sum(ord(c) for c in (item_code or "x"))
	return round(4.0 + (h % 10) / 10.0, 1)


def _badge(stock):
	return "In Stock" if stock > 0 else "Out of Stock"


def _card(it):
	stock = get_stock(it.name)
	price = get_price(it.name)
	return {
		"brand": (it.brand or it.item_group or "").upper(),
		"sku": it.name,
		"name": it.item_name or it.name,
		"rating": _rating(it.name),
		"price": money(price),
		"price_value": price,
		"badge": _badge(stock),
		"image": it.image,
	}


def list_products(q=None, item_group=None, brand=None, sort=None, page=1, page_size=PAGE_SIZE):
	page = max(1, cint(page))
	filters = {"disabled": 0, "is_sales_item": 1}
	if item_group:
		filters["item_group"] = item_group
	if brand:
		filters["brand"] = brand
	or_filters = None
	if q:
		or_filters = [["item_name", "like", f"%{q}%"], ["item_code", "like", f"%{q}%"]]

	fields = ["name", "item_name", "item_group", "brand", "image"]
	start = (page - 1) * page_size

	# Price sorts need the rate from Item Price, which isn't a column on Item,
	# so sort in Python over the full result set, then paginate.
	if sort in ("price_asc", "price_desc"):
		rows = frappe.get_all("Item", filters=filters, or_filters=or_filters, fields=fields, limit_page_length=0)
		total = len(rows)
		prices = _price_map()
		rows.sort(key=lambda it: prices.get(it.name, 0.0), reverse=(sort == "price_desc"))
		page_rows = rows[start : start + page_size]
		return [_card(it) for it in page_rows], total

	# SQL-orderable sorts.
	order_map = {
		"asc": "name asc",          # Ascending Order (by SKU/code)
		"desc": "name desc",        # Descending Order
		"name_asc": "item_name asc",  # A - Z Order
		"name_desc": "item_name desc",  # Z - A Order
	}
	order_by = order_map.get(sort, "creation desc")  # default: newest first

	all_names = frappe.get_all("Item", filters=filters, or_filters=or_filters, fields=["name"], limit_page_length=0)
	total = len(all_names)

	items = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by=order_by,
		start=start,
		page_length=page_size,
	)
	return [_card(it) for it in items], total


def page_numbers(total, page, page_size=PAGE_SIZE):
	pages = max(1, math.ceil(total / page_size))
	if pages <= 6:
		return list(range(1, pages + 1))
	if page <= 3:
		return [1, 2, 3, "…", pages]
	if page >= pages - 2:
		return [1, "…", pages - 2, pages - 1, pages]
	return [1, "…", page, "…", pages]


def get_categories():
	groups = frappe.get_all("Item Group", filters={"is_group": 0}, fields=["name"], order_by="name asc")
	return [g.name for g in groups if g.name != "All Item Groups"]


def get_manufacturers(selected=None):
	rows = frappe.get_all("Item", filters={"disabled": 0, "is_sales_item": 1}, fields=["distinct brand as brand"])
	return [(r.brand, r.brand == selected) for r in rows if r.brand]


def get_best_sellers(limit=4):
	items = frappe.get_all(
		"Item",
		filters={"disabled": 0, "is_sales_item": 1},
		fields=["name", "item_name", "item_group", "brand", "image"],
		order_by="modified desc",
		page_length=limit,
	)
	out = []
	for it in items:
		stock = get_stock(it.name)
		price = get_price(it.name)
		out.append({
			"brand": (it.brand or it.item_group or "").upper(),
			"name": it.item_name or it.name,
			"sku": it.name,
			"price": money(price),
			"price_value": price,
			"badge": "In Stock" if stock > 0 else "",
			"image": it.image,
		})
	return out


def get_product_detail(item_code):
	if not item_code or not frappe.db.exists("Item", item_code):
		return None

	it = frappe.get_doc("Item", item_code)
	stock = get_stock(item_code)
	img = it.image
	gallery = [img, img, img, img] if img else [None, None, None, None]

	specs = [
		{"label": "Item Code", "value": it.item_code},
		{"label": "Item Group", "value": it.item_group},
		{"label": "Stock UOM", "value": it.stock_uom},
	]
	if it.brand:
		specs.append({"label": "Brand", "value": it.brand})
	if it.get("weight_per_unit"):
		specs.append({"label": "Weight", "value": f"{it.weight_per_unit} {it.get('weight_uom') or ''}".strip()})
	specs.append({"label": "Availability", "value": f"{int(stock)} in stock" if stock > 0 else "Out of stock"})

	related = []
	for r in frappe.get_all(
		"Item",
		filters={"item_group": it.item_group, "disabled": 0, "is_sales_item": 1, "name": ["!=", item_code]},
		fields=["name", "item_name", "image"],
		page_length=4,
	):
		r_price = get_price(r.name)
		related.append({
			"name": r.item_name or r.name,
			"subtitle": "SKU: " + r.name,
			"sku": r.name,
			"price": money(r_price),
			"price_value": r_price,
			"badge": "",
			"image": r.image,
		})

	product = {
		"in_stock": stock > 0,
		"stock_label": "In Stock" if stock > 0 else "Out of Stock",
		"sku": it.item_code,
		"item_code": it.item_code,
		"name": it.item_name or it.name,
		"rating": _rating(item_code),
		"review_count": 0,
		"price": money(get_price(item_code)),
		"price_value": get_price(item_code),
		"old_price": None,
		"save_label": None,
		"price_note": "Excl. VAT & Shipping costs",
		"gallery": gallery,
		"description_title": it.item_name or it.name,
		"description_html": it.description or "",
		"description_points": [],
		"description_image": img,
	}

	breadcrumbs = [
		{"label": "Catalog", "url": "/all-products"},
		{"label": it.item_group, "url": "/all-products?item_group=" + urllib.parse.quote(it.item_group or "")},
		{"label": product["name"], "url": None},
	]
	return {"product": product, "specs": specs, "related": related, "breadcrumbs": breadcrumbs}
