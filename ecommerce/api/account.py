# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Account/customer API for storefront customer dashboard data."""

import frappe
from frappe.utils import add_days, flt, formatdate, get_first_day, today

from ecommerce.api.common import money


def default_customer_group():
	return (
		frappe.db.get_single_value("Selling Settings", "customer_group")
		or frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
		or "All Customer Groups"
	)


def default_territory():
	return (
		frappe.db.get_single_value("Selling Settings", "territory")
		or frappe.db.get_value("Territory", {"is_group": 0}, "name")
		or "All Territories"
	)


def get_customer_for_user(user):
	"""Find the Customer linked to a user via their Contact, if any."""
	if not user or user == "Guest":
		return None
	contact = frappe.db.get_value("Contact", {"user": user}, "name")
	if contact:
		link = frappe.db.get_value(
			"Dynamic Link",
			{"parenttype": "Contact", "parent": contact, "link_doctype": "Customer"},
			"link_name",
		)
		if link:
			return link
	return None


def ensure_customer(user):
	"""Return the Customer linked to ``user``, creating + linking one by the
	user's email/name if none exists. Never falls back to another customer."""
	cust = get_customer_for_user(user)
	if cust:
		return cust

	u = frappe.db.get_value("User", user, ["first_name", "last_name", "full_name", "email"], as_dict=True) or {}
	full_name = u.get("full_name") or user
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": full_name,
		"customer_type": "Individual",
		"customer_group": default_customer_group(),
		"territory": default_territory(),
	}).insert(ignore_permissions=True)

	# Link (or create) the user's Contact to this Customer so future lookups resolve.
	contact_name = frappe.db.get_value("Contact", {"user": user})
	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
	else:
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": u.get("first_name") or full_name,
			"last_name": u.get("last_name"),
			"user": user,
		})
		contact.append("email_ids", {"email_id": u.get("email") or user, "is_primary": 1})
	if not any(l.link_doctype == "Customer" and l.link_name == customer.name for l in contact.links):
		contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})
	contact.flags.ignore_permissions = True
	contact.save(ignore_permissions=True)

	return customer.name


def _primary_address(customer):
	if not customer:
		return None
	addr_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
		"parent",
	)
	if not addr_name:
		return None
	a = frappe.db.get_value(
		"Address", addr_name,
		["address_title", "address_line1", "address_line2", "city", "state", "pincode", "country"],
		as_dict=True,
	)
	if not a:
		return None
	lines = [x for x in [
		a.address_line1,
		a.address_line2,
		", ".join([p for p in [a.city, a.state, a.pincode] if p]),
		a.country,
	] if x]
	return {"label": a.address_title or "Primary Address", "lines": lines}


def _status_class(status):
	s = (status or "").lower()
	if "complet" in s or "closed" in s or "delivered" in s:
		return "delivered"
	if "cancel" in s:
		return "delivered"
	return "processing"


def get_dashboard():
	from ecommerce.api.auth import require_customer_session

	session = require_customer_session()
	customer = session.customer
	c = frappe.db.get_value(
		"Customer", customer, ["customer_name", "email_id", "mobile_no"], as_dict=True
	) or {}
	first = session.first_name or (c.get("customer_name") or "Account").split(" ")[0]
	last = ""

	account = {
		"company": c.get("customer_name") or "My Account",
		"account_id": customer,
		"first_name": first,
		"last_name": last,
		"email": session.email or c.get("email_id") or "",
		"phone": session.phone or c.get("mobile_no") or "—",
		"role": "Customer",
	}

	address = _primary_address(customer) or {"label": "No address on file", "lines": ["Add a delivery address at checkout."]}

	so_filters = {"docstatus": ["<", 2]}
	if customer:
		so_filters["customer"] = customer
	orders = frappe.get_all(
		"Sales Order", filters=so_filters,
		fields=["name", "transaction_date", "status", "grand_total"],
		order_by="transaction_date desc", page_length=6,
	)
	recent_orders = [{
		"id": "#" + o.name,
		"date": formatdate(o.transaction_date, "MMM dd, yyyy"),
		"status": o.status,
		"status_class": _status_class(o.status),
		"total": money(o.grand_total),
	} for o in orders]

	last30 = frappe.db.count("Sales Order", {**so_filters, "transaction_date": [">=", add_days(today(), -30)]})
	ytd_rows = frappe.get_all(
		"Sales Order",
		filters={**so_filters, "transaction_date": [">=", get_first_day(today())]},
		fields=["grand_total"],
	)
	ytd = sum(flt(r.grand_total) for r in ytd_rows)
	quote_filters = {"status": ["in", ["Open", "Draft"]]}
	if customer:
		quote_filters["party_name"] = customer
	active_quotes = frappe.db.count("Quotation", quote_filters)

	stats = [
		{"label": "Recent Orders", "value": str(last30), "tag": "Last 30 Days"},
		{"label": "Total Spend", "value": money(ytd), "tag": "MTD Spend"},
		{"label": "Active Quotes", "value": f"{active_quotes:02d}", "tag": "Pending"},
	]
	nav = [
		{"label": "Dashboard", "key": "dashboard", "active": True},
		{"label": "Orders", "key": "orders", "active": False},
		{"label": "Addresses", "key": "addresses", "active": False},
		{"label": "Settings", "key": "settings", "active": False},
	]
	return {"account": account, "address": address, "nav": nav, "stats": stats, "recent_orders": recent_orders}
