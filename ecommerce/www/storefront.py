"""Controller alias for the Ecommerce storefront.

The unique route avoids ERPNext's built-in ``home`` template taking priority
over this app's homepage.
"""

from ecommerce.www.home import get_context, no_cache

__all__ = ["get_context", "no_cache"]
