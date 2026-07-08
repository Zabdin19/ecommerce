# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the Request a Quote page (`/request-quote`).

Renders a B2B quote-request form. Submissions are stored as
**Ecommerce Quote Request** records, viewable in Desk. The shared chrome is
built by ``ecommerce.website_context.get_chrome``.
"""

import frappe
from frappe.utils import validate_email_address

from ecommerce.website_context import get_chrome

no_cache = 1

PAGE_TITLE = "Request a Quote"
PAGE_SUBTITLE = (
	"Tell us about your requirements and our team will prepare a tailored "
	"wholesale quote for your business."
)
BUSINESS_TYPES = ["Retailer", "Wholesaler", "Distributor", "Manufacturer", "Other"]
SUCCESS_MESSAGE = "Thanks! Your quote request has been received. Our team will get back to you shortly."


def get_context(context):
	chrome = get_chrome()
	context.chrome = chrome
	context.page_title = PAGE_TITLE
	context.page_subtitle = PAGE_SUBTITLE
	context.business_types = BUSINESS_TYPES
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1
	context.title = f"{PAGE_TITLE} | {chrome.brand}"
	context.metatags = {
		"title": context.title,
		"description": "Request a wholesale quote for bulk orders.",
		"og:type": "website",
	}
	return context


@frappe.whitelist(allow_guest=True)
def submit(full_name=None, company_name=None, email=None, phone=None,
		square_footage=None, message=None, type_of_business=None):
	"""Store a quote-request submission as an Ecommerce Quote Request."""
	full_name = (full_name or "").strip()
	email = (email or "").strip()
	message = (message or "").strip()

	if not full_name:
		return {"ok": False, "message": "Please enter your full name."}
	if not email or not validate_email_address(email):
		return {"ok": False, "message": "Please enter a valid email address."}
	if not message:
		return {"ok": False, "message": "Please enter your message."}

	business = (type_of_business or "").strip()
	if business and business not in BUSINESS_TYPES:
		business = "Other"

	try:
		frappe.get_doc({
			"doctype": "Ecommerce Quote Request",
			"full_name": full_name,
			"company_name": (company_name or "").strip(),
			"email": email,
			"phone": (phone or "").strip(),
			"square_footage": (square_footage or "").strip(),
			"message": message,
			"type_of_business": business,
			"status": "New",
		}).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error("Quote request submission failed", frappe.get_traceback())
		return {"ok": False, "message": "Something went wrong. Please try again."}

	return {"ok": True, "message": SUCCESS_MESSAGE}
