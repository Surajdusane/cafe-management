# API Documentation — Cafe Management System

Base URL (development): `http://127.0.0.1:8000`

Interactive Swagger UI is available at `/docs` and ReDoc at `/redoc`.

## Response Envelope Convention

All JSON API responses follow one envelope so the frontend can handle them uniformly.

### Success

```json
{
  "success": true,
  "data": { }
}
```

### Error

```json
{
  "success": false,
  "message": "Human readable error message",
  "errors": [
    { "field": "price", "message": "value could not be parsed" }
  ]
}
```

`errors` appears only for validation failures (HTTP 422).

## Endpoints

### GET /api/health

Health check. Verifies the API process and executes `SELECT 1` against SQLite.

**Response 200**

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "app_name": "Cafe Management System",
    "version": "0.1.0",
    "database": "connected"
  }
}
```

**Response 503** (database unreachable)

```json
{
  "success": true,
  "data": {
    "status": "degraded",
    "app_name": "Cafe Management System",
    "version": "0.1.0",
    "database": "error"
  }
}
```

### GET /api/meta/tables

Returns the list of tables currently present in the database. Useful during development to confirm migrations/initialization.

```json
{ "success": true, "data": { "tables": [] } }
```

### GET /api/settings

Returns the cafe settings. Creates the singleton row with default values on first call, so the response is never empty.

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "cafe_name": "My Cafe",
    "address": null,
    "phone": null,
    "email": null,
    "logo_url": null,
    "tax_percent": 0.0,
    "currency": "₹",
    "receipt_footer": null,
    "updated_at": "2026-08-23T09:47:11"
  }
}
```

### PUT /api/settings

Replaces the cafe settings (full update). The server independently validates every field; strings are trimmed and empty optional values are stored as `null`.

**Request body**

| Field           | Type          | Required | Rules                                        |
| --------------- | ------------- | -------- | -------------------------------------------- |
| `cafe_name`     | string        | yes      | 1–100 characters                             |
| `address`       | string / null | no       | max 255 characters                           |
| `phone`         | string / null | no       | exactly 10 digits, Indian mobile pattern     |
| `email`         | string / null | no       | valid email format, stored lowercase         |
| `logo_url`      | string / null | no       | max 300 characters                           |
| `tax_percent`   | number        | yes      | 0 ≤ value ≤ 100                              |
| `currency`      | string        | yes      | 1–8 characters                               |
| `receipt_footer`| string / null | no       | max 200 characters                           |

```json
{
  "cafe_name": "Brew & Bean Cafe",
  "address": "12 Station Road, Pune",
  "phone": "9876543210",
  "email": "hello@brewbean.in",
  "logo_url": "/static/images/logo.png",
  "tax_percent": 5.5,
  "currency": "₹",
  "receipt_footer": "Thank you for visiting!"
}
```

**Response 200**

Same shape as `GET /api/settings`, plus `"message": "Settings saved successfully."`.

**Response 422** (validation failure)

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": [
    { "field": "tax_percent", "message": "Input should be less than or equal to 100" },
    { "field": "phone", "message": "Enter a valid 10-digit mobile number." }
  ]
}
```

### GET /api/categories

Lists menu categories ordered by name, each with a live `item_count`.

| Query parameter    | Type   | Default | Notes                       |
| ------------------ | ------ | ------- | --------------------------- |
| `search`           | string | –       | matches name/description    |
| `include_inactive` | bool   | `true`  | set `false` for active only |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Coffee",
        "description": null,
        "is_active": true,
        "item_count": 6,
        "created_at": "2026-08-23T10:02:11",
        "updated_at": null
      }
    ],
    "count": 1
  }
}
```

### POST /api/categories

Creates a category. `name` is required (1–80 chars); `description` optional (≤255); `is_active` defaults to `true`.

**Response 201** — created category. **Response 409** — a category with the same name already exists.

### GET /api/categories/{category_id}

Returns one category. **Response 404** if missing.

### PUT /api/categories/{category_id}

Full replace using the same body rules as create. **Responses:** 200 · 404 · 409 (duplicate name).

### DELETE /api/categories/{category_id}

Deletes an empty category. **Response 409** when items still use it ("Move or delete its items first").

### GET /api/menu/items

Lists menu items ordered by name, newest last, each embedding a brief category summary.

| Query parameter  | Type    | Default | Notes                        |
| ---------------- | ------- | ------- | ---------------------------- |
| `search`         | string  | –       | matches name/description     |
| `category_id`    | int     | –       | filter to one category       |
| `available_only` | bool    | –       | `true` hides sold-out items  |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 3,
        "category_id": 1,
        "name": "Cappuccino",
        "description": "Espresso with steamed milk",
        "price": 120.0,
        "image_url": "/static/images/favicon.svg",
        "is_vegetarian": true,
        "is_popular": false,
        "is_available": true,
        "created_at": "2026-08-23T10:04:00",
        "updated_at": null,
        "category": { "id": 1, "name": "Coffee", "is_active": true }
      }
    ],
    "count": 1
  }
}
```

### POST /api/menu/items

Creates a menu item. Validation: `category_id` must exist (gt 0), `name` 1–120 chars, `price > 0` (rounded to 2 decimals), `description` ≤500, `image_url` ≤300; `is_vegetarian` defaults `true`, `is_popular`/`is_available` default per schema.

**Responses:** 201 created · 404 unknown category · 409 duplicate item name within the same category (case-insensitive) · 422 validation failure.

### GET /api/menu/items/{item_id}

Returns one item. **Response 404** if missing.

### PUT /api/menu/items/{item_id}

Full replace with the same validation as create (duplicate check excludes the item itself). **Responses:** 200 · 404 · 409 · 422.

### DELETE /api/menu/items/{item_id}

Deletes the item. Returns `"message": "Menu item deleted."`. **Response 404** if missing.

### GET /api/public/menu

The public digital-menu feed consumed by the shareable `/menu/cafe` page. No authentication, safe to share with customers.

Returns cafe branding plus every **active** category that has at least one item. Sold-out items stay listed (`is_available: false`) so customers see availability honestly. The payload deliberately contains no ids, timestamps, admin flags or billing configuration — only what the page displays.

```json
{
  "success": true,
  "data": {
    "cafe": {
      "name": "Brew & Bean Cafe",
      "address": "12 Station Road, Pune",
      "phone": "9876543210",
      "email": "hello@brewbean.in",
      "logo_url": "/static/images/logo.png",
      "currency": "₹"
    },
    "categories": [
      {
        "name": "Coffee",
        "description": null,
        "items": [
          {
            "name": "Cappuccino",
            "description": "Espresso with steamed milk",
            "price": 120.0,
            "image_url": "/static/images/favicon.svg",
            "is_vegetarian": true,
            "is_popular": true,
            "is_available": true
          },
          {
            "name": "Chocolate Cake",
            "description": null,
            "price": 110.0,
            "image_url": null,
            "is_vegetarian": false,
            "is_popular": false,
            "is_available": false
          }
        ]
      }
    ]
  }
}
```

## Error Handling

| Status | Cause                              | Body                                  |
| ------ | ---------------------------------- | ------------------------------------- |
| 404    | Unknown route or missing resource  | `{ "success": false, "message": ... }`|
| 422    | Request body/query validation fail | envelope with `errors[]`              |
| 500    | Unhandled server exception         | `{ "success": false, "message": "Internal server error" }` |

Unhandled exceptions return a generic message; internals are never exposed to the client.

## Page Routes (HTML)

Served as `text/html` from `app/templates/`. Navigation links are injected by `static/js/common.js`.

| Route            | Template            | Access  |
| ---------------- | ------------------- | ------- |
| `/`              | index.html          | admin   |
| `/menu`          | menu.html           | admin   |
| `/customer-menu` | customer-menu.html  | admin — share page for the public link |
| **`/menu/cafe`** | public-menu.html    | **public** — customer digital menu |
| `/orders`        | orders.html         | admin   |
| `/billing`       | billing.html        | admin   |
| `/inventory`     | inventory.html      | admin   |
| `/purchases`     | purchases.html      | admin   |
| `/suppliers`     | suppliers.html      | admin   |
| `/employees`     | employees.html      | admin   |
| `/salaries`      | salaries.html       | admin   |
| `/expenses`      | expenses.html       | admin   |
| `/reports`       | reports.html        | admin   |
| `/settings`      | settings.html       | admin   |

The public page loads only `public-menu.css`, `api.js` and `public-menu.js`; the admin shell (`common.js`) is intentionally never served to customers.

## Static Assets

Everything under `static/` is served at `/static/...`.

- `/static/css/main.css`, `/static/css/dashboard.css`, `/static/css/menu.css`, `/static/css/responsive.css`, `/static/css/public-menu.css`
- `/static/js/api.js`, `/static/js/common.js`, `/static/js/validation.js`, `/static/js/dashboard.js`, `/static/js/categories.js`, `/static/js/menu-items.js`, `/static/js/settings.js`, `/static/js/customer-menu.js`, `/static/js/public-menu.js`
- `/static/images/favicon.svg`

## Frontend API Utility

`static/js/api.js` wraps `fetch`:

```js
API.get("/api/health")
API.post("/api/items", payload)
API.put("/api/items/1", payload)
API.delete("/api/items/1")
```

It parses the envelope, throws `ApiError(message, status, errors)` on failure and maps network failures to a friendly message. Toast notifications are provided by `UI.toast(message, type)` in `common.js`. The public menu page reuses `api.js` but not `common.js`.

---
*Last updated: Phase 5 completion (Customer Digital Menu). Categories and menu-item endpoints documented together with their phases (3–4).*
