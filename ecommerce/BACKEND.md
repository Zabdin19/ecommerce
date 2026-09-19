# DollarBasket — Backend / API Layer

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

## Cart engine

`webshop` is **not** installed, so there is no ERPNext Shopping Cart / Website Item.
The cart uses two compatible stores:

- Guests use **`Ecommerce Cart`** + **`Ecommerce Cart Item`**, keyed by an
  HttpOnly `ecom_cart_token` cookie.
- Signed-in customers use their latest draft ERPNext Sales Order.
- Customer login merges the guest cart into that customer's draft Sales Order.
- The separate `ecommerce_customer_token` session never grants Frappe Desk access.

The online total is the item subtotal. Shipping and payment arrangements are
explicitly marked for confirmation because no Shipping Rule or payment gateway
is configured in this app.

## Whitelisted endpoints

All return JSON. Cart endpoints allow guests; checkout/account require login.

| Method | Auth | Args | Returns |
|---|---|---|---|
| `ecommerce.api.get_cart` | guest | – | cart dict |
| `ecommerce.api.add_to_cart` | guest | `item_code, qty=1` | cart dict |
| `ecommerce.api.update_cart_item` | guest | `item_code, qty` | cart dict |
| `ecommerce.api.remove_cart_item` | guest | `item_code` | cart dict |
| `ecommerce.api.clear_cart` | guest | – | cart dict |
| `ecommerce.api.cart.apply_coupon` | guest | `code` | `{ok, message}` |
| `ecommerce.api.submit_cart_order` | customer | `address, shipping_method, payment_method` | `{ok, order}` |
| `ecommerce.api.register_customer` | guest | `first_name, last_name, email, phone, password` | `{ok, message, redirect}` |
| `ecommerce.www.home.subscribe` | guest | `email` | `{ok, message}` |

**cart dict** = `{ items:[{item_code,name,sku,variant,qty,unit_value,unit,total,image}],
item_count, shipping_value, summary:{subtotal,shipping,total} }`

## Page → data source

| Route | Controller | Source |
|---|---|---|
| `/storefront` (`/`) | `storefront.py` → `home.py` | Ecommerce Homepage Settings + `products.get_best_sellers` |
| `/all-products` | `all_products.py` | `products.list_products` (Item + Item Price + Bin), Item Group, Brand. Params: `q, item_group, brand, sort, page` |
| `/product` | `product.py` | `products.get_product_detail` (Item, price, stock, related). Param: `item` |
| `/cart` | `cart.py` | `cart.get_cart_data` |
| `/checkout` | `checkout.py` | `checkout.get_checkout_context` (live cart) |
| `/my-account` | `my_account.py` | `account.get_dashboard` (Customer, Sales Order, Address). Login required |
| `/sign-in` | `sign_in.py` | Independent ecommerce customer session |
| `/register` | `register.py` | Customer + Ecommerce Customer Account |

## Required site configuration

- **Selling price list:** the Selling Settings price list or `Standard Selling` fallback.
- **Company:** the global default company, used for Sales Orders.
- **Warehouse:** first non-group warehouse of the company (Sales Order needs a delivery warehouse).
- **Products:** sourced from Item where `disabled=0` and `is_sales_item=1`.
- **Website identity:** Website Settings is migrated to DollarBasket and uses the
  `/storefront` route to avoid ERPNext's built-in `home` template collision.

## Notes / follow-ups

- Coupon codes are not exposed in the storefront because the legacy demo coupon
  endpoint does not alter Sales Order pricing.
- No review source, wholesale price rules, customer-specific discounts, credit
  terms, shipping rules, or payment gateway are implemented yet.
