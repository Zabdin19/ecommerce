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

	context.chrome = get_chrome()
	context.products = rows
	context.categories = products.get_categories()
	context.manufacturers = products.get_manufacturers(brand)
	context.result_count = total
	context.page_count = len(rows)
	context.page = page
	context.page_pages = products.page_numbers(total, page)
	context.active_group = item_group
	context.search_q = q or ""
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"Industrial Catalog | {context.chrome.brand}"
	context.metatags = {"title": context.title, "description": "Browse the full product catalog."}
	return context
