# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class EcommerceHomepageSettings(Document):
	def on_update(self):
		# Storefront pages read this Single via get_cached_doc; clear the website
		# cache so saved changes appear on the next page refresh.
		from frappe.website.utils import clear_website_cache

		clear_website_cache()
