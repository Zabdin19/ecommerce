# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Storefront customer auth that is separate from Frappe/Desk sessions."""

import hashlib
import secrets

import frappe
from frappe.utils import add_days, now_datetime, validate_email_address

from ecommerce.api.account import default_customer_group, default_territory

CUSTOMER_TOKEN_COOKIE = "ecommerce_customer_token"
ACCOUNT_DOCTYPE = "Ecommerce Customer Account"
SESSION_DOCTYPE = "Ecommerce Customer Session"
PASSWORD_ITERATIONS = 260000
SESSION_DAYS = 30


def _hash_password(password, salt=None, iterations=PASSWORD_ITERATIONS):
	salt = salt or secrets.token_hex(16)
	digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
	return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def _verify_password(password, stored_hash):
	try:
		algo, iterations, salt, digest = (stored_hash or "").split("$", 3)
		if algo != "pbkdf2_sha256":
			return False
		candidate = _hash_password(password, salt=salt, iterations=int(iterations)).split("$", 3)[3]
		return secrets.compare_digest(candidate, digest)
	except Exception:
		return False


def _token_hash(token):
	return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _request_cookie(name):
	req = getattr(frappe.local, "request", None)
	return req.cookies.get(name) if req is not None else None


def _set_customer_cookie(token, expires=None):
	cm = getattr(frappe.local, "cookie_manager", None)
	if not cm:
		return
	kwargs = {"httponly": True, "samesite": "Lax"}
	req = getattr(frappe.local, "request", None)
	if req is not None and getattr(req, "scheme", "") == "https":
		kwargs["secure"] = True
	if expires:
		kwargs["expires"] = expires
	cm.set_cookie(CUSTOMER_TOKEN_COOKIE, token, **kwargs)


def clear_customer_cookie():
	cm = getattr(frappe.local, "cookie_manager", None)
	if not cm:
		return
	if hasattr(cm, "delete_cookie"):
		cm.delete_cookie(CUSTOMER_TOKEN_COOKIE)
	else:
		cm.set_cookie(CUSTOMER_TOKEN_COOKIE, "", expires="Thu, 01 Jan 1970 00:00:00 GMT")


def _customer_info(customer, account=None):
	customer_doc = frappe.db.get_value(
		"Customer", customer, ["name", "customer_name", "email_id", "mobile_no"], as_dict=True
	)
	if not customer_doc:
		return {"logged_in": False}
	full_name = customer_doc.customer_name or customer
	first_name = ((account or {}).get("first_name") or full_name).split(" ")[0]
	return {
		"logged_in": True,
		"customer": customer_doc.name,
		"customer_name": full_name,
		"full_name": full_name,
		"first_name": first_name,
		"email": (account or {}).get("email") or customer_doc.email_id,
		"phone": (account or {}).get("phone") or customer_doc.mobile_no,
	}


def get_current_customer_session():
	"""Return the active ecommerce customer session for the token cookie only."""
	token = _request_cookie(CUSTOMER_TOKEN_COOKIE)
	if not token:
		return None

	session = frappe.db.get_value(
		SESSION_DOCTYPE,
		{"token_hash": _token_hash(token), "status": "Active"},
		["name", "customer", "customer_account", "expires_on"],
		as_dict=True,
	)
	if not session:
		return None

	if session.expires_on and session.expires_on <= now_datetime():
		frappe.db.set_value(SESSION_DOCTYPE, session.name, "status", "Expired", update_modified=False)
		frappe.db.commit()
		clear_customer_cookie()
		return None

	account = frappe.db.get_value(
		ACCOUNT_DOCTYPE,
		session.customer_account,
		["name", "first_name", "last_name", "email", "phone", "enabled"],
		as_dict=True,
	) if session.customer_account else None
	if account and not account.enabled:
		return None

	info = _customer_info(session.customer, account)
	if not info.get("logged_in"):
		return None
	info.update({"session": session.name, "customer_account": session.customer_account})
	return frappe._dict(info)


def require_customer_session():
	session = get_current_customer_session()
	if not session:
		frappe.throw("Please login as a customer to continue.", frappe.PermissionError)
	return session


def login(email=None, password=None):
	email = (email or "").strip().lower()
	if not email or not password:
		return {"ok": False, "message": "Email and password are required."}

	account = frappe.db.get_value(
		ACCOUNT_DOCTYPE,
		{"email": email},
		["name", "customer", "first_name", "last_name", "email", "phone", "password_hash", "enabled"],
		as_dict=True,
	)
	if not account or not account.enabled or not _verify_password(password, account.password_hash):
		frappe.local.response["http_status_code"] = 401
		return {"ok": False, "message": "Invalid email or password."}

	token = secrets.token_urlsafe(32)
	expires_on = add_days(now_datetime(), SESSION_DAYS)
	session = frappe.get_doc({
		"doctype": SESSION_DOCTYPE,
		"customer": account.customer,
		"customer_account": account.name,
		"token_hash": _token_hash(token),
		"expires_on": expires_on,
		"status": "Active",
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	_set_customer_cookie(token, expires=expires_on)

	# Keep cart items across the login boundary: fold any guest cookie cart into
	# this customer's Draft Sales Order.
	try:
		from ecommerce.api.cart import merge_guest_cart_into_order

		merge_guest_cart_into_order(account.customer)
	except Exception:
		frappe.log_error("guest cart merge on login failed", frappe.get_traceback())

	info = _customer_info(account.customer, account)
	info.update({"ok": True, "message": "Login successful.", "session": session.name})
	return info


def logout():
	token = _request_cookie(CUSTOMER_TOKEN_COOKIE)
	if token:
		session_name = frappe.db.get_value(SESSION_DOCTYPE, {"token_hash": _token_hash(token), "status": "Active"}, "name")
		if session_name:
			frappe.db.set_value(SESSION_DOCTYPE, session_name, "status", "Revoked", update_modified=False)
			frappe.db.commit()
	clear_customer_cookie()
	return {"ok": True, "redirect": "/sign-in"}


def get_logged_in_customer():
	session = get_current_customer_session()
	if not session:
		return {"logged_in": False}
	return {
		"logged_in": True,
		"customer": session.customer,
		"customer_name": session.customer_name,
		"full_name": session.full_name,
		"first_name": session.first_name,
		"email": session.email,
		"phone": session.phone,
	}


@frappe.whitelist(allow_guest=True)
def register(first_name, last_name=None, email=None, phone=None, password=None, confirm_password=None):
	first_name = (first_name or "").strip()
	last_name = (last_name or "").strip()
	email = (email or "").strip().lower()
	phone = (phone or "").strip()

	if not first_name:
		return {"ok": False, "message": "Please enter your first name."}
	if not email or not validate_email_address(email):
		return {"ok": False, "message": "Please enter a valid corporate email address."}
	if not password:
		return {"ok": False, "message": "Please enter a password."}
	if len(password) < 8:
		return {"ok": False, "message": "Password must be at least 8 characters long."}
	if confirm_password is not None and password != confirm_password:
		return {"ok": False, "message": "Passwords do not match."}
	if frappe.db.exists(ACCOUNT_DOCTYPE, {"email": email}):
		return {"ok": False, "message": "A customer with this email already exists."}
	if frappe.db.exists("Customer", {"email_id": email}):
		return {"ok": False, "message": "A customer with this email already exists."}
	if phone and frappe.db.exists("Customer", {"mobile_no": phone}):
		return {"ok": False, "message": "A customer with this phone number already exists."}

	full_name = (first_name + " " + last_name).strip()
	try:
		# Customer record ONLY — no User, no Contact, no login provisioning.
		# Insert without email_id/mobile_no first: the Customer controller would
		# otherwise auto-spawn a primary Contact for them (create_primary_contact).
		customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": full_name or email,
			"customer_type": "Individual",
			"customer_group": default_customer_group(),
			"territory": default_territory(),
		}).insert(ignore_permissions=True)

		# Write contact details straight to the DB so the controller's
		# Contact-creation hook does not run again.
		frappe.db.set_value(
			"Customer", customer.name,
			{"email_id": email, "mobile_no": phone or None},
			update_modified=False,
		)
		frappe.get_doc({
			"doctype": ACCOUNT_DOCTYPE,
			"customer": customer.name,
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"phone": phone,
			"password_hash": _hash_password(password),
			"enabled": 1,
		}).insert(ignore_permissions=True)

		frappe.db.commit()
	except frappe.exceptions.ValidationError as e:
		frappe.db.rollback()
		msg = frappe.utils.strip_html_tags(str(e)) or "Please check your details and try again."
		return {"ok": False, "message": msg}
	except Exception:
		frappe.db.rollback()
		frappe.log_error("Ecommerce registration failed", frappe.get_traceback())
		return {"ok": False, "message": "We couldn't create your account. Please try again."}

	return {"ok": True, "message": "Customer registered successfully.", "redirect": "/sign-in"}
