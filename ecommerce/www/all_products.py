# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the product listing / catalog page (`/all-products`).

Sources real products from ERPNext Item via ``ecommerce.api.products``.
Supports ?q= (search), ?item_group= (category), ?brand=, ?sort=, ?page=.
"""

import frappe

from ecommerce.api import products
from ecommerce.website_context import get_chrome

no_cache = 1


def get_context(context):
	fd = frappe.form_dict
	q = fd.get("q")
	item_group = fd.get("item_group")
	brand = fd.get("brand")
	sort = fd.get("sort")
	page = frappe.utils.cint(fd.get("page")) or 1

	rows, total = products.list_products(q=q, item_group=item_group, brand=brand, sort=sort, page=page)

	from urllib.parse import urlencode

	total_pages = max(1, -(-total // products.PAGE_SIZE))  # ceil division
	page = min(max(page, 1), total_pages)
	# Query-string prefix carrying the active filters so paging keeps them.
	active_filters = [(k, v) for k, v in (("q", q), ("item_group", item_group), ("brand", brand), ("sort", sort)) if v]
	base_query = "?" + urlencode(active_filters) + ("&" if active_filters else "")
	# Filter-only prefix (no sort/page) used by the Sort dropdown links.
	filter_only = [(k, v) for k, v in (("q", q), ("item_group", item_group), ("brand", brand)) if v]
	filter_query = "?" + urlencode(filter_only) + ("&" if filter_only else "")

	sort_options = [
		("asc", "Ascending Order"),
		("desc", "Descending Order"),
		("price_asc", "Low - High Price"),
		("price_desc", "High - Low Price"),
		("name_asc", "A - Z Order"),
		("name_desc", "Z - A Order"),
	]
	sort_label = dict(sort_options).get(sort, "Sort")

	context.chrome = get_chrome()
	context.products = rows
	context.categories = products.get_categories()
	context.manufacturers = products.get_manufacturers(brand)
	context.result_count = total
	context.page_count = len(rows)
	context.page = page
	context.total_pages = total_pages
	context.base_query = base_query
	context.range_start = (total and (page - 1) * products.PAGE_SIZE + 1) or 0
	context.range_end = (page - 1) * products.PAGE_SIZE + len(rows)
	context.page_pages = products.page_numbers(total, page)
	context.active_group = item_group
	context.active_brand = brand or ""
	context.sort = sort
	context.sort_options = sort_options
	context.sort_label = sort_label
	context.filter_query = filter_query
	context.search_q = q or ""
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"Industrial Catalog | {context.chrome.brand}"
	context.metatags = {"title": context.title, "description": "Browse the full product catalog."}
	return context
