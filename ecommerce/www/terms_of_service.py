# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the Terms of Service page (`/terms-of-service`).

Content is managed from the **Terms of Service Settings** Single DocType. The
values below are fallbacks used only when the settings are empty.
"""

from ecommerce import legal

no_cache = 1

DEFAULT_CONTENT = """
<h2>1. Acceptance of Terms</h2>
<p>By accessing or using this storefront, you agree to be bound by these Terms of
Service and all applicable laws and regulations.</p>

<h2>2. Accounts</h2>
<p>You are responsible for maintaining the confidentiality of your account
credentials and for all activity that occurs under your account.</p>

<h2>3. Orders &amp; Pricing</h2>
<p>All orders are subject to acceptance and availability. Prices are confirmed at
checkout and may change without notice. We reserve the right to refuse or cancel
any order.</p>

<h2>4. Shipping &amp; Returns</h2>
<p>Delivery timelines are estimates. Returns and refunds are handled according to
our standard wholesale policy — contact our team for assistance.</p>

<h2>5. Limitation of Liability</h2>
<p>We are not liable for any indirect or consequential damages arising from the use
of our products or services, to the fullest extent permitted by law.</p>

<h2>6. Contact Us</h2>
<p>Questions about these Terms can be directed to our team through the Contact Us
page.</p>
"""


def get_context(context):
	return legal.build_context(context, "Terms of Service Settings", {
		"hero_heading": "Terms of Service",
		"hero_description": "The terms that govern your use of our storefront.",
		"content": DEFAULT_CONTENT,
	})
