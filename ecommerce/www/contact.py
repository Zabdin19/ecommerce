# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the Contact Us page (`/contact`).

Content is managed from the **Contact Page Settings** Single DocType (Frappe
Desk), with design-matched defaults so the page renders before it is filled in.
Form submissions are stored as **Ecommerce Contact Message** records, viewable
in Desk. The shared chrome is built by ``ecommerce.website_context.get_chrome``.
"""

import frappe
from frappe.utils import strip_html, validate_email_address

from ecommerce.website_context import get_chrome

no_cache = 1

DEFAULT_SUBTITLE = (
	"Have a question about bulk orders, pricing, or logistics? Our team is here "
	"to help — reach out and we'll respond within one business day."
)
DEFAULT_EMAIL = "support@frappe-ecommerce.com"
DEFAULT_PHONE = "1-800-FRAPPE-01"
DEFAULT_ADDRESS = "1200 Industrial Way, Suite 400, Chicago, IL 60601"
DEFAULT_HOURS = "Monday – Friday, 8:00 AM – 6:00 PM (CST)"
DEFAULT_FORM_SUBTITLE = "Fill out the form and a representative will get back to you shortly."
DEFAULT_SUCCESS = "Thanks! Your message has been sent. Our team will get back to you shortly."


def _settings():
	try:
		return frappe.get_cached_doc("Contact Page Settings")
	except Exception:
		return None


def get_context(context):
	cp = _settings()
	chrome = get_chrome()

	def val(fieldname, default=""):
		return ((cp.get(fieldname) if cp else None) or "").strip() or default

	contact = frappe._dict(
		page_title=val("page_title", "Contact Us"),
		page_subtitle=val("page_subtitle", DEFAULT_SUBTITLE),
		hero_image=(cp.get("hero_image") if cp else None),
		email=val("email", DEFAULT_EMAIL),
		phone=val("phone", DEFAULT_PHONE),
		address=val("address", DEFAULT_ADDRESS),
		hours=val("hours", DEFAULT_HOURS),
		map_embed_url=val("map_embed_url"),
		form_heading=val("form_heading", "Send us a message"),
		form_subtitle=val("form_subtitle", DEFAULT_FORM_SUBTITLE),
		form_button_text=val("form_button_text", "Send Message"),
		success_message=val("success_message", DEFAULT_SUCCESS),
	)

	context.chrome = chrome
	context.contact = contact
	context.current_year = frappe.utils.now_datetime().year
	context.no_cache = 1

	context.title = val("meta_title", f"{contact.page_title} | {chrome.brand}")
	context.description = val("meta_description", strip_html(contact.page_subtitle))
	context.metatags = {
		"title": context.title,
		"description": context.description,
		"og:type": "website",
	}
	return context


@frappe.whitelist(allow_guest=True)
def submit(full_name=None, email=None, phone=None, subject=None, message=None):
	"""Store a contact-form submission as an Ecommerce Contact Message."""
	full_name = (full_name or "").strip()
	email = (email or "").strip()
	message = (message or "").strip()

	if not full_name:
		return {"ok": False, "message": "Please enter your name."}
	if not email or not validate_email_address(email):
		return {"ok": False, "message": "Please enter a valid email address."}
	if not message:
		return {"ok": False, "message": "Please enter a message."}

	try:
		frappe.get_doc({
			"doctype": "Ecommerce Contact Message",
			"full_name": full_name,
			"email": email,
			"phone": (phone or "").strip(),
			"subject": (subject or "").strip(),
			"message": message,
			"status": "New",
		}).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error("Contact form submission failed", frappe.get_traceback())
		return {"ok": False, "message": "Something went wrong. Please try again."}

	cp = _settings()
	success = ((cp.get("success_message") if cp else None) or "").strip() or DEFAULT_SUCCESS
	return {"ok": True, "message": success}
