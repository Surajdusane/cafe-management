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

## Error Handling

| Status | Cause                              | Body                                  |
| ------ | ---------------------------------- | ------------------------------------- |
| 404    | Unknown route or missing resource  | `{ "success": false, "message": ... }`|
| 422    | Request body/query validation fail | envelope with `errors[]`              |
| 500    | Unhandled server exception         | `{ "success": false, "message": "Internal server error" }` |

Unhandled exceptions return a generic message; internals are never exposed to the client.

## Page Routes (HTML)

Served as `text/html` from `app/templates/`. Navigation links are injected by `static/js/common.js`.

| Route            | Template            |
| ---------------- | ------------------- |
| `/`              | index.html          |
| `/menu`          | menu.html           |
| `/customer-menu` | customer-menu.html  |
| `/orders`        | orders.html         |
| `/billing`       | billing.html        |
| `/inventory`     | inventory.html      |
| `/purchases`     | purchases.html      |
| `/suppliers`     | suppliers.html      |
| `/employees`     | employees.html      |
| `/salaries`      | salaries.html       |
| `/expenses`      | expenses.html       |
| `/reports`       | reports.html        |
| `/settings`      | settings.html       |

## Static Assets

Everything under `static/` is served at `/static/...`.

- `/static/css/main.css`, `/static/css/dashboard.css`, `/static/css/responsive.css`
- `/static/js/api.js`, `/static/js/common.js`, `/static/js/validation.js`, `/static/js/dashboard.js`
- `/static/images/favicon.svg`

## Frontend API Utility

`static/js/api.js` wraps `fetch`:

```js
API.get("/api/health")
API.post("/api/items", payload)
API.put("/api/items/1", payload)
API.delete("/api/items/1")
```

It parses the envelope, throws `ApiError(message, status, errors)` on failure and maps network failures to a friendly message. Toast notifications are provided by `UI.toast(message, type)` in `common.js`.

---
*Domain endpoints (categories, menu items, orders, billing, etc.) will be documented here as each phase is implemented.*

*Last updated: Phase 2 completion.*
