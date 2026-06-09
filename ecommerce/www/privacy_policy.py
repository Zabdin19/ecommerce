# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Controller for the Privacy Policy page (`/privacy-policy`).

Content is managed from the **Privacy Policy Settings** Single DocType. The
values below are fallbacks used only when the settings are empty.
"""

from ecommerce import legal

no_cache = 1

DEFAULT_CONTENT = """
<h2>1. Information We Collect</h2>
<p>We collect information you provide directly to us when you create an account,
place an order, or contact our support team — including your name, business email,
phone number, and shipping details.</p>

<h2>2. How We Use Your Information</h2>
<p>Your information is used to process orders, provide customer support, manage your
account, and send important service updates. We never sell your personal data.</p>

<h2>3. Data Security</h2>
<p>We use industry-standard safeguards to protect your information. Passwords are
stored using secure one-way hashing and are never kept in plain text.</p>

<h2>4. Cookies</h2>
<p>We use cookies to keep you signed in, remember your cart, and improve your
browsing experience. You can disable cookies in your browser settings.</p>

<h2>5. Contact Us</h2>
<p>If you have questions about this Privacy Policy, please reach out to our team
through the Contact Us page.</p>
"""


def get_context(context):
	return legal.build_context(context, "Privacy Policy Settings", {
		"hero_heading": "Privacy Policy",
		"hero_description": "How we collect, use, and protect your information.",
		"content": DEFAULT_CONTENT,
	})
