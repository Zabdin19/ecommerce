# Copyright (c) 2024, Zain-ul-Abdin and contributors
# For license information, please see license.txt

"""Cache-busting URLs for this app's static assets.

Everything under ``/assets/`` is served with a long ``Cache-Control: max-age``
(12 hours from the dev server, typically a year from the production nginx
config). Because ``/assets/ecommerce/css/landing.css`` is a stable URL, a
browser that has seen it once keeps reusing its cached copy after a deploy, so
the site appears unchanged until someone hard-refreshes.

Stamping the URL with the file's modification time changes the URL whenever the
file actually changes, which makes the browser fetch the new copy while still
allowing it to cache aggressively in between deploys.
"""

import os

import frappe


def asset_url(path):
	"""Return ``path`` with a ``?v=`` stamp derived from the file's mtime.

	Falls back to the app version if the file cannot be located, so a bad path
	degrades to the un-stamped behaviour instead of raising during a render.
	"""
	# Only bundled app assets are versioned this way. Admin uploads live under
	# /files/ and are handed back untouched.
	if not path or not path.startswith("/assets/"):
		return path

	stamp = None
	parts = [p for p in path[len("/assets/"):].split("/") if p and p != ".."]
	if len(parts) >= 2:
		app, rest = parts[0], parts[1:]
		try:
			full_path = os.path.join(frappe.get_app_path(app, "public"), *rest)
			stamp = str(int(os.path.getmtime(full_path)))
		except Exception:
			stamp = None

	if not stamp:
		from ecommerce import __version__

		stamp = __version__

	separator = "&" if "?" in path else "?"
	return f"{path}{separator}v={stamp}"
