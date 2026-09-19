# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Catalog API: list/search/filter products, categories, brands, product detail.

Sources data from ERPNext **Item** (+ Item Price, Bin and Item Group). Product
ratings are intentionally omitted until the site has a real review source.
"""

import math
import urllib.parse

import frappe
from frappe.utils import cint

from ecommerce.api.common import get_price, get_stock, money, price_list

PAGE_SIZE = 12

# Upper bound of the storefront's price-range slider. The slider's rightmost
# position means "no cap" (shown as "{cap}+"), not literally this value.
PRICE_FILTER_CAP = 1000000


def _price_map():
	"""Return ``{item_code: price_list_rate}`` for the storefront price list in one query."""
	rows = frappe.get_all(
		"Item Price",
		filters={"price_list": price_list(), "selling": 1},
		fields=["item_code", "price_list_rate"],
	)
	return {r.item_code: r.price_list_rate for r in rows}


def _badge(stock):
	return "In Stock" if stock > 0 else "Out of Stock"


def _card(it):
	stock = get_stock(it.name)
	price = get_price(it.name)
	return {
		"brand": (it.brand or it.item_group or "").upper(),
		"sku": it.name,
		"name": it.item_name or it.name,
		"rating": None,
		"price": money(price),
		"price_value": price,
		"badge": _badge(stock),
		"image": it.image,
	}


def list_products(q=None, item_group=None, brand=None, sort=None, page=1, page_size=PAGE_SIZE, price_max=None):
	page = max(1, cint(page))
	filters = {"disabled": 0, "is_sales_item": 1}
	if item_group:
		group = frappe.db.get_value("Item Group", item_group, ["is_group", "lft", "rgt"], as_dict=True)
		if group and group.is_group:
			descendants = frappe.get_all(
				"Item Group",
				filters={"lft": [">", group.lft], "rgt": ["<", group.rgt], "is_group": 0},
				pluck="name",
			)
			filters["item_group"] = ["in", descendants] if descendants else item_group
		else:
			filters["item_group"] = item_group
	if brand:
		filters["brand"] = brand
	or_filters = None
	if q:
		or_filters = [["item_name", "like", f"%{q}%"], ["item_code", "like", f"%{q}%"]]

	fields = ["name", "item_name", "item_group", "brand", "image", "creation"]
	start = (page - 1) * page_size

	# Price sorts/filters need the rate from Item Price, which isn't a column on
	# Item, so sort and filter in Python over the full result set, then paginate.
	if price_max is not None or sort in ("price_asc", "price_desc"):
		rows = frappe.get_all("Item", filters=filters, or_filters=or_filters, fields=fields, limit_page_length=0)
		prices = _price_map()
		if price_max is not None:
			rows = [r for r in rows if prices.get(r.name, 0.0) <= price_max]

		order_map = {
			"asc": lambda it: it.name,
			"desc": lambda it: it.name,
			"name_asc": lambda it: it.item_name,
			"name_desc": lambda it: it.item_name,
			"price_asc": lambda it: prices.get(it.name, 0.0),
			"price_desc": lambda it: prices.get(it.name, 0.0),
		}
		reverse = sort in ("desc", "name_desc", "price_desc")
		rows.sort(key=order_map.get(sort, lambda it: it.creation), reverse=reverse)

		total = len(rows)
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
	"""Return the site's configured leaf catalogue groups alphabetically."""
	groups = frappe.get_all(
		"Item Group",
		filters={"is_group": 0},
		fields=["name"],
		order_by="name asc",
	)
	return [group.name for group in groups if group.name != "All Item Groups"]


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
		"rating": None,
		"review_count": 0,
		"price": money(get_price(item_code)),
		"price_value": get_price(item_code),
		"old_price": None,
		"save_label": None,
		"price_note": "Price from the active storefront price list; shipping is shown at checkout.",
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
