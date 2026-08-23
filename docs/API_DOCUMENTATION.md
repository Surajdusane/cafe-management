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
