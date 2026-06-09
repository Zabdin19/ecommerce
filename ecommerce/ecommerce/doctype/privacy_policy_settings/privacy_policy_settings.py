# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class PrivacyPolicySettings(Document):
	def on_update(self):
		from frappe.website.utils import clear_website_cache

		clear_website_cache()
