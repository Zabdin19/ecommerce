# Ecommerce — Backend / API Layer

This app powers a custom storefront (server-rendered Jinja pages under `ecommerce/www/`)
backed by a thin API layer in `ecommerce/api/`. Page controllers call the API for
server render; the same whitelisted methods are used by the frontend JS for actions.

## Architecture

```
ecommerce/
  api/
    common.py    price list / price / stock / money helpers
    products.py  catalog list/search/filter, categories, brands, product detail, best sellers
    cart.py      cart engine (custom DocType) + whitelisted add/update/remove/clear/get/coupon
    checkout.py  checkout context + place_order (creates Sales Order)
    account.py   resolve customer, dashboard data (orders, address, stats)
    auth.py      B2B registration (User + Customer + Contact)
  www/*.py       page controllers -> call api.*
  website_context.py  shared header/footer chrome (+ live cart badge count)
  ecommerce/doctype/
    ecommerce_cart / ecommerce_cart_item   custom cart storage
```

## Cart engine (chosen: custom)

`webshop` is **not** installed, so there is no ERPNext Shopping Cart / Website Item.
The cart is a custom **`Ecommerce Cart`** (parent) + **`Ecommerce Cart Item`** (child):

- Logged-in users: one cart keyed by `user`.
- Guests: one cart keyed by a `cart_token` stored in the `ecom_cart_token` cookie.
- `on_login` (`ecommerce.api.cart.merge_guest_cart_on_login`) folds a guest cart into
  the user's cart at login.
- All writes use `ignore_permissions` (guests must mutate their own cart).

Totals: `subtotal + flat shipping ($45 when non-empty) + VAT 5%`. Constants live in
`api/cart.py` (`SHIPPING_VALUE`, `TAX_RATE`).

## Whitelisted endpoints

All return JSON. Cart endpoints allow guests; checkout/account require login.

| Method | Auth | Args | Returns |
|---|---|---|---|
| `ecommerce.api.cart.get_cart` | guest | – | cart dict |
| `ecommerce.api.cart.add_to_cart` | guest | `item_code, qty=1` | cart dict |
| `ecommerce.api.cart.update_cart_item` | guest | `item_code, qty` | cart dict |
| `ecommerce.api.cart.remove_cart_item` | guest | `item_code` | cart dict |
| `ecommerce.api.cart.clear_cart` | guest | – | cart dict |
| `ecommerce.api.cart.apply_coupon` | guest | `code` | `{ok, message}` |
| `ecommerce.api.checkout.place_order` | login | `address, shipping_method, payment_method` | `{ok, order, redirect}` |
| `ecommerce.api.auth.register` | guest | `first_name, last_name, email, phone, password` | `{ok, message, redirect}` |
| `ecommerce.www.home.subscribe` | guest | `email` | `{ok, message}` |

**cart dict** = `{ items:[{item_code,name,sku,variant,qty,unit_value,unit,total,image}],
item_count, shipping_value, tax_rate, summary:{subtotal,shipping,tax_label,tax,total} }`

## Page → data source

| Route | Controller | Source |
|---|---|---|
| `/home` | `home.py` | Website Settings custom fields + `products.get_best_sellers` |
| `/all-products` | `all_products.py` | `products.list_products` (Item + Item Price + Bin), Item Group, Brand. Params: `q, item_group, brand, sort, page` |
| `/product` | `product.py` | `products.get_product_detail` (Item, price, stock, related). Param: `item` |
| `/cart` | `cart.py` | `cart.get_cart_data` |
| `/checkout` | `checkout.py` | `checkout.get_checkout_context` (live cart) |
| `/my-account` | `my_account.py` | `account.get_dashboard` (Customer, Sales Order, Address). Login required |
| `/sign-in` | `sign_in.py` | Frappe `login` endpoint (JS) |
| `/register` | `register.py` | `auth.register` (JS) |

## Required site config (and current values on site2.localhost)

- **Selling price list:** `Standard Selling` (USD). Override via `api/common.py:DEFAULT_PRICE_LIST`.
- **Company:** global default (`Destro (Demo)`), used for Sales Order.
- **Warehouse:** first non-group warehouse of the company (Sales Order needs a delivery warehouse).
- **Tax:** storefront VAT is a flat 5% display value (no Sales Taxes template is applied to the SO).
- **Ratings/reviews:** no review data exists — ratings are a deterministic placeholder
  (`products._rating`) and the Reviews tab shows an empty state. Swap for a real
  Item-review source when available.
- **Products:** sourced from `Item` where `disabled=0` and `is_sales_item=1` (10 demo
  Items: SKU001–SKU010). There is no `show_in_website` flag (that lives in webshop);
  add one as a custom field + fixture if you want to gate which Items appear.

## Notes / follow-ups

- Coupons (`apply_coupon`) validate a demo list (`WELCOME10`, `BULK15`) and store the
  code on the cart but do not yet alter Sales Order pricing.
- The "Shipping protection" toggle and shipping-method selection are display-only;
  `place_order` creates a draft Sales Order with cart items at cart prices.
- `ensure_customer` falls back to the first Customer on the site if a logged-in user
  has no linked Customer (keeps demo checkout working for Administrator).
