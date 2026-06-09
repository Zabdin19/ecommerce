# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class EcommerceCart(Document):
	def recalculate(self):
		"""Refresh each row's amount from rate * qty."""
		for row in self.items:
			row.qty = max(1, int(row.qty or 1))
			row.amount = (row.rate or 0) * row.qty
