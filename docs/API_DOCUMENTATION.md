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

### GET /api/orders

Lists orders newest first, each with an `item_count`. The full item lines are returned by the single-order endpoint.

| Query parameter  | Type   | Notes                                        |
| ---------------- | ------ | -------------------------------------------- |
| `search`         | string | matches `order_number`                       |
| `order_status`   | string | Pending / Preparing / Ready / Completed / Cancelled |
| `order_type`     | string | Dine-in / Takeaway                           |
| `payment_status` | string | Unpaid / Paid                                |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "order_number": "ORD-0001",
        "order_type": "Dine-in",
        "table_number": 4,
        "status": "Pending",
        "item_count": 2,
        "subtotal": 250.0,
        "discount_amount": 10.0,
        "tax_percent": 5.0,
        "tax_amount": 12.0,
        "total": 252.0,
        "payment_method": null,
        "payment_status": "Unpaid",
        "created_at": "2026-08-23T13:00:00"
      }
    ],
    "count": 1
  }
}
```

### POST /api/orders

Creates an order. **The server calculates all money values** — the client sends only the type, optional table, item references and a discount.

**Request body**

| Field            | Type    | Required | Rules                                                     |
| ---------------- | ------- | -------- | --------------------------------------------------------- |
| `order_type`     | string  | yes      | `"Dine-in"` or `"Takeaway"`                               |
| `table_number`   | int     | for Dine-in | 1–999; forced to null for takeaways                     |
| `items`          | array   | yes      | 1–50 entries of `{menu_item_id: int>0, quantity: int 1–999}` |
| `discount_amount`| number  | no       | ≥ 0, ≤ subtotal (checked against real prices), default 0   |

```json
{
  "order_type": "Dine-in",
  "table_number": 4,
  "items": [
    { "menu_item_id": 3, "quantity": 2 },
    { "menu_item_id": 7, "quantity": 1 }
  ],
  "discount_amount": 10
}
```

Server-side business rules:

* every `menu_item_id` must exist (**404**) and be marked available (**409**);
* the same dish may appear on one line only — raise its quantity instead (**422**);
* dine-in requires a table number (**422**);
* discount above the subtotal is refused with **400**;
* totals are computed as `taxable = subtotal − discount`, `tax = taxable × tax_percent/100` (rate snapshotted from settings), `total = taxable + tax`.

**Response 201** — full order detail including snapshot item lines (`item_name`, `unit_price`, `quantity`, `line_total`). Errors: 404 · 409 · 400 · 422.

### GET /api/orders/{order_id}

Full order detail with item lines and audit timestamps. **404** if missing.

### PUT /api/orders/{order_id}/status

Moves the order through its workflow.

```json
{ "status": "Preparing" }
```

Rules: cancelled orders are frozen (**409** on any change); a paid order cannot be cancelled (**409**) — refunds happen outside the system. **Response 200** with updated detail.

### DELETE /api/orders/{order_id}

Hard-deletes an order **only when it is Cancelled** (otherwise **409**). Completed history is never deletable.

### GET /api/bills

The orders table seen through a money lens, plus collection totals for dashboard cards.

| Query parameter  | Type   | Notes                        |
| ---------------- | ------ | ---------------------------- |
| `search`         | string | matches bill/order number    |
| `payment_status` | string | Unpaid / Paid                |
| `payment_method` | string | Cash / UPI / Card / Other    |

```json
{
  "success": true,
  "data": {
    "items": [ { "...same shape as order summary..." : "" } ],
    "count": 1,
    "summary": {
      "count": 1,
      "billed_total": 252.0,
      "collected_total": 252.0,
      "outstanding_total": 0.0
    }
  }
}
```

### GET /api/bills/{order_id}

Bill detail used by the printable receipt: everything about the order plus the cafe branding block.

```json
{
  "success": true,
  "data": {
    "bill": { "order_number": "ORD-0001", "items": [], "subtotal": 250.0, "discount_amount": 10.0, "tax_percent": 5.0, "tax_amount": 12.0, "total": 252.0, "payment_status": "Paid", "paid_at": "2026-08-23T13:02:11", "...": "..." },
    "cafe": {
      "cafe_name": "Brew & Bean Cafe",
      "address": "12 Station Road, Pune",
      "phone": "9876543210",
      "logo_url": null,
      "currency": "₹",
      "receipt_footer": "Thank you for visiting!"
    }
  }
}
```

### POST /api/bills/{order_id}/pay

Records a payment — the only way a bill becomes Paid.

```json
{ "payment_method": "UPI" }
```

Sets `payment_status = "Paid"`, stores the method and stamps `paid_at`. **Responses:** 200 · 404 unknown bill · 409 already paid or cancelled order · 422 invalid method.

### GET /api/suppliers

Lists suppliers ordered by name, each with a live `inventory_item_count`.

| Query parameter    | Type   | Default | Notes                       |
| ------------------ | ------ | ------- | --------------------------- |
| `search`           | string | –       | matches name / contact person / materials / phone |
| `include_inactive` | bool   | `true`  | set `false` for active only |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Gokul Dairy",
        "contact_person": "Ramesh Patel",
        "phone": "9876543210",
        "email": "orders@gokuldairy.in",
        "address": "12 Market Yard, Pune",
        "materials_supplied": "Milk, Paneer, Butter",
        "is_active": true,
        "inventory_item_count": 3,
        "created_at": "2026-08-23T14:00:00",
        "updated_at": null
      }
    ],
    "count": 1
  }
}
```

### POST /api/suppliers

Creates a supplier. Validation: `name` required (1–100 chars, unique ignoring case → 409 on duplicate); optional `contact_person` ≤100; `phone` must match the 10-digit Indian mobile pattern when provided; `email` must be a valid format and is stored lowercase; `address`/`materials_supplied` ≤255; strings trimmed, empty optionals stored as `null`.

**Response 201** — created supplier. **Responses:** 201 · 409 duplicate name · 422 validation failure.

### GET /api/suppliers/{supplier_id}

Returns one supplier. **Response 404** if missing.

### PUT /api/suppliers/{supplier_id}

Full replace using the same body rules as create (duplicate check excludes the supplier itself). **Responses:** 200 · 404 · 409 · 422.

### DELETE /api/suppliers/{supplier_id}

Deletes the supplier. Raw materials keep all data — their preferred-supplier link is cleared automatically. Returns `"message": "Supplier deleted."`. **Response 404** if missing.

### GET /api/inventory/items

Lists raw materials ordered by name with stock levels, supplier summaries and computed low-stock flags. The response also carries a summary block used by the page's stat cards.

| Query parameter    | Type   | Default | Notes                                     |
| ------------------ | ------ | ------- | ----------------------------------------- |
| `search`           | string | –       | matches name/category                     |
| `category`         | string | –       | exact category match                      |
| `supplier_id`      | int    | –       | filter to one supplier                    |
| `low_stock_only`   | bool   | `false` | only items where qty ≤ minimum            |
| `include_inactive` | bool   | `true`  | set `false` for active only               |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Milk",
        "category": "Dairy",
        "unit": "Litre",
        "current_quantity": 2.0,
        "minimum_stock": 3.0,
        "purchase_price": 56.0,
        "supplier_id": 1,
        "is_active": true,
        "notes": null,
        "created_at": "2026-08-23T14:05:00",
        "updated_at": "2026-08-23T16:40:11",
        "supplier": { "id": 1, "name": "Gokul Dairy", "is_active": true },
        "is_low_stock": true,
        "transaction_count": 2
      }
    ],
    "count": 1,
    "summary": { "total_items": 4, "active_items": 3, "low_stock_items": 1, "total_suppliers": 2 }
  }
}
```

### GET /api/inventory/categories

Distinct material categories, sorted — feeds the page filter dropdown and datalist.

```json
{ "success": true, "data": { "categories": ["Beverages", "Dairy", "Spices"] } }
```

### POST /api/inventory/items

Creates a raw material. Validation: `name` required 1–120 (unique ignoring case → 409); `category` required ≤80; `unit` one of `Kg, Gram, Litre, Millilitre, Piece, Packet, Box`; `initial_quantity` ≥ 0 (default 0); `minimum_stock` ≥ 0 (default 0); `purchase_price` ≥ 0 (default 0); `supplier_id`, when sent, must exist (**404** otherwise); quantities round to 3 decimals, price to 2. A non-zero opening quantity automatically writes the first history row (`Stock In`, note "Opening stock").

```json
{
  "name": "Milk",
  "category": "Dairy",
  "unit": "Litre",
  "initial_quantity": 10,
  "minimum_stock": 3,
  "purchase_price": 56,
  "supplier_id": 1
}
```

**Response 201** — item detail including its transactions list. **Responses:** 201 · 404 unknown supplier · 409 duplicate name · 422 validation failure.

### GET /api/inventory/items/{item_id}

Full detail including up to 20 recent movements (newest first). **404** if missing.

### PUT /api/inventory/items/{item_id}

Replaces descriptive fields (same rules as create minus opening quantity). The stock level is intentionally **not** editable here — use stock movements so history stays complete. **Responses:** 200 · 404 · 409 · 422.

### DELETE /api/inventory/items/{item_id}

Deletes the material together with its movement history (cascade). **Response 404** if missing.

### POST /api/inventory/items/{item_id}/stock

Records one stock movement atomically and writes its history row.

```json
{ "transaction_type": "Stock Out", "quantity": 8, "note": "Morning usage" }
```

| Field             | Type   | Rules                                                                 |
| ----------------- | ------ | --------------------------------------------------------------------- |
| `transaction_type`| string | `"Stock In"` \| `"Stock Out"` \| `"Adjustment"`                        |
| `quantity`        | number | In/Out: > 0 (amount moved); Adjustment: ≥ 0 (new counted total)       |
| `note`            | string | optional, ≤200 chars                                                  |

Server behaviour:

* **Stock In** adds units; **Stock Out** subtracts them through an atomic guarded UPDATE — insufficient stock returns **409** ("Not enough stock…") and changes nothing; **Adjustment** sets the absolute level.
* every successful movement returns the refreshed item plus the written transaction row (with `balance_after`) and a human-readable message.

**Response 200**

```json
{
  "success": true,
  "data": {
    "item": { "...refreshed material summary...": "" },
    "transaction": {
      "id": 5, "item_id": 1, "transaction_type": "Stock Out", "quantity": 8.0,
      "balance_after": 2.0, "note": "Morning usage", "created_at": "2026-08-23T16:40:11"
    }
  },
  "message": "8.0 Litre removed from 'Milk'. New balance: 2.0 Litre."
}
```

Errors: 404 unknown item · 409 insufficient stock · 422 validation failure.

### GET /api/inventory/transactions

Global movement history, newest first.

| Query parameter    | Type   | Default | Notes                                |
| ------------------ | ------ | ------- | ------------------------------------ |
| `item_id`          | int    | –       | history of one material              |
| `transaction_type` | string | –       | Stock In / Stock Out / Adjustment    |
| `limit`            | int    | 100     | 1–500 rows                           |

Each row carries `item_name` alongside the movement fields shown above.

### GET /api/purchases

Purchase history, newest first (by purchase date, then id), with a `summary` block for the page's stat cards.

| Query parameter  | Type   | Default | Notes                                        |
| ---------------- | ------ | ------- | -------------------------------------------- |
| `search`         | string | –       | matches purchase number or supplier name     |
| `supplier_id`    | int    | –       | filter to one supplier                       |
| `payment_status` | string | –       | `Unpaid` \| `Paid`                            |
| `start_date`     | date   | –       | ISO `YYYY-MM-DD`, inclusive lower bound      |
| `end_date`       | date   | –       | ISO `YYYY-MM-DD`, inclusive upper bound      |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 7,
        "purchase_number": "PUR-0007",
        "supplier_id": 1,
        "supplier_name": "Gokul Dairy",
        "purchase_date": "2026-08-23",
        "subtotal": 940.0,
        "total": 940.0,
        "payment_status": "Unpaid",
        "notes": null,
        "created_at": "2026-08-23T18:00:00",
        "item_count": 2
      }
    ],
    "count": 1,
    "summary": { "count": 1, "total_amount": 940.0, "unpaid_count": 1, "unpaid_amount": 940.0 }
  }
}
```

Invalid `start_date`/`end_date` values return 422 automatically.

### POST /api/purchases

Records a purchase and increases inventory as ONE logical database operation. Validation: `supplier_id` required and must exist (**404** otherwise); every material must exist (**404**) and be active (**409**); each material may appear once (**422** on duplicates); quantities > 0 (≤ 999999); unit costs ≥ 0; at least 1 and at most 50 items; `purchase_date` optional ISO date (defaults to today); `payment_status` optional `Unpaid`/`Paid` (default Unpaid); `notes` ≤ 255.

The client never sends totals: the server rounds quantities to 3 decimals and costs to 2, computes `line_total = quantity × unit_cost`, `subtotal = total = Σ line totals`, assigns the `PUR-xxxx` number from the primary key, adds each material's quantity through a guarded SQL UPDATE and writes one `Stock In` history row per line (`note: "Purchase PUR-xxxx"`). A single commit covers everything — a failure anywhere leaves stock untouched.

```json
{
  "supplier_id": 1,
  "purchase_date": "2026-08-23",
  "items": [
    { "inventory_item_id": 1, "quantity": 2.5, "unit_cost": 56 },
    { "inventory_item_id": 3, "quantity": 1, "unit_cost": 799.99 }
  ],
  "notes": "Invoice INV-77"
}
```

**Response 201**

```json
{
  "success": true,
  "data": { "...full purchase with items[]...": "" },
  "message": "Purchase PUR-0007 recorded. Inventory updated for 2 material(s)."
}
```

Errors: 404 unknown supplier/material · 409 inactive material · 422 validation failure.

### GET /api/purchases/{purchase_id}

Full detail including material lines and timestamps. **Response 404** if missing.

### PUT /api/purchases/{purchase_id}/payment-status

Marks a purchase paid or reverts it to unpaid.

```json
{ "payment_status": "Paid" }
```

**Response 200** — updated purchase. **Responses:** 200 · 404 unknown purchase · 422 invalid status value.

### GET /api/employees

Lists employees ordered by name, each with a live `salary_count` (number of salary records).

| Query parameter    | Type   | Default | Notes                                        |
| ------------------ | ------ | ------- | -------------------------------------------- |
| `search`           | string | –       | matches name / mobile / email / role         |
| `role`             | string | –       | Manager / Cashier / Chef / Waiter / Helper / Cleaner (any other value → 422) |
| `include_inactive` | bool   | `true`  | set `false` for active only                  |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Priya Sharma",
        "mobile": "9876543210",
        "email": "priya@cafe.in",
        "address": "21 Station Road, Pune",
        "role": "Chef",
        "joining_date": "2025-06-01",
        "salary_type": "Monthly",
        "base_salary": 25000.0,
        "is_active": true,
        "salary_count": 2,
        "created_at": "2026-08-23T18:00:00",
        "updated_at": null
      }
    ],
    "count": 1
  }
}
```

### POST /api/employees

Creates an employee. Validation: `name` required 1–100 chars; `mobile` must match the 10-digit Indian mobile pattern; `email` when given must be a valid format (stored lowercase); `role` one of Manager / Cashier / Chef / Waiter / Helper / Cleaner; `joining_date` cannot be in the future; `salary_type` one of Monthly / Daily / Hourly; `base_salary` ≥ 0 rounded to 2 decimals (booleans rejected); `is_active` defaults `true`. Strings are trimmed and empty optionals stored as `null`.

**Responses:** 201 created · 422 validation failure. Message: "Employee created."

### GET /api/employees/{employee_id}

Returns one employee. **Response 404** if missing.

### PUT /api/employees/{employee_id}

Full replace using the same body rules as create. **Responses:** 200 · 404 · 422.

### DELETE /api/employees/{employee_id}

Deletes the employee. **Response 409** while salary records exist ("Delete their salary history first") so payment history can never disappear silently. **Response 404** if missing.

### GET /api/salaries

Salary history ordered newest month first, each row embedding a brief `employee` summary.

| Query parameter  | Type   | Default | Notes                                     |
| ---------------- | ------ | ------- | ----------------------------------------- |
| `employee_id`    | int    | –       | > 0, filter to one employee               |
| `month`          | string | –       | `YYYY-MM` (pattern enforced, else 422)    |
| `payment_status` | string | –       | Paid / Unpaid                             |

### POST /api/salaries

Creates one salary record. The net salary is **always calculated by the server**: `net = base + bonus − deduction`. If `base_salary` is omitted the employee's current base salary is copied in at save time.

| Field            | Type          | Required | Rules                                                            |
| ---------------- | ------------- | -------- | ---------------------------------------------------------------- |
| `employee_id`    | int           | yes      | > 0; must exist (**404** otherwise)                              |
| `salary_month`   | string        | yes      | `YYYY-MM` format, year 2000–2100                                 |
| `base_salary`    | number / null | no       | ≥ 0, ≤ 99,999,999; falls back to the employee's current base     |
| `bonus`          | number        | no       | ≥ 0, default 0, rounded to 2 dp                                  |
| `deduction`      | number        | no       | ≥ 0, default 0, ≤ base + bonus (net can never be negative → 422) |
| `payment_status` | string        | no       | `"Paid"` / `"Unpaid"`, default `"Unpaid"`                        |
| `payment_date`   | date / null   | no       | defaults to today when marked Paid without a date                |
| `notes`          | string / null | no       | ≤ 255 chars, trimmed                                             |

**Responses:** 201 created · 404 unknown employee · 409 one record per employee per month already exists · 422 validation failure. Message: "Salary record created."

### GET /api/salaries/{salary_id}

Returns one salary record with its `employee` summary. **Response 404** if missing.

### PUT /api/salaries/{salary_id}

Full replace with the same body rules as create; the net salary is recalculated server-side and the duplicate-month check excludes the record itself. **Responses:** 200 · 404 · 409 · 422.

### DELETE /api/salaries/{salary_id}

Deletes the salary record (frees the employee for deletion). **Responses:** 200 "Salary record deleted." · 404.

### GET /api/expenses/options

Fixed choice lists so the UI never hard-codes them.

```json
{
  "success": true,
  "data": {
    "categories": ["Electricity", "Gas", "Rent", "Maintenance", "Cleaning", "Internet", "Miscellaneous"],
    "payment_methods": ["Cash", "UPI", "Card", "Other"]
  }
}
```

### GET /api/expenses

Expense history ordered newest first (by `expense_date`, then id), with a `summary` block for the page's stat cards.

| Query parameter   | Type   | Default | Notes                                    |
| ----------------- | ------ | ------- | ---------------------------------------- |
| `search`          | string | –       | matches title or notes                   |
| `category`        | string | –       | exact category match                     |
| `payment_method`  | string | –       | Cash / UPI / Card / Other                |
| `start_date`      | date   | –       | ISO `YYYY-MM-DD`, inclusive lower bound  |
| `end_date`        | date   | –       | ISO `YYYY-MM-DD`, inclusive upper bound  |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 3,
        "title": "March electricity bill",
        "category": "Electricity",
        "amount": 2500.0,
        "expense_date": "2026-08-20",
        "payment_method": "Cash",
        "notes": "Bill no. 8841",
        "created_at": "2026-08-23T18:00:00",
        "updated_at": null
      }
    ],
    "count": 1,
    "summary": { "count": 1, "total_amount": 2500.0, "categories": 1 }
  }
}
```

Invalid date values return 422 automatically.

### POST /api/expenses

Creates an expense. Validation: `title` required 1–120 chars (**may repeat** — duplicates are allowed deliberately); `category` must be one of Electricity / Gas / Rent / Maintenance / Cleaning / Internet / Miscellaneous; `amount` > 0 (≤ 99,999,999), rounded to 2 decimals, booleans rejected; `expense_date` optional (defaults to today); `payment_method` one of Cash / UPI / Card / Other (default Cash); `notes` ≤ 255, trimmed.

**Response 201** — created expense. **Response 422** — validation failure. Message: "Expense recorded."

### GET /api/expenses/{expense_id}

Returns one expense. **Response 404** if missing.

### PUT /api/expenses/{expense_id}

Full replace with the same body rules as create. **Responses:** 200 · 404 · 422.

### DELETE /api/expenses/{expense_id}

Deletes the expense (always allowed — an expense carries no foreign keys). **Responses:** 200 "Expense deleted." · 404.

### GET /api/reports/sales

Series of **paid-order** sales bucketed by period. Every figure is recomputed live from the database — reports are read-only.

| Query parameter | Type   | Default   | Notes                                                        |
| --------------- | ------ | --------- | ------------------------------------------------------------ |
| `period`        | string | `daily`   | `daily` \| `weekly` \| `monthly` (else 422)                  |
| `start_date`    | date   | –         | ISO `YYYY-MM-DD`; absent → last 14 days (daily) / last 7 days (weekly) |
| `end_date`      | date   | –         | ISO `YYYY-MM-DD`, inclusive                                 |

```json
{
  "success": true,
  "data": {
    "period": "monthly",
    "period_label": "Monthly",
    "start_date": null,
    "end_date": null,
    "summary": { "sales_total": 252.0, "orders": 1, "avg_order": 252.0 },
    "series": { "labels": ["Aug 26"], "amounts": [252.0], "orders": [1] }
  }
}
```

`daily` renders one point per calendar day in the selected range; `weekly` is a rolling last-7-day daily view; `monthly` buckets orders into `YYYY-MM` labels.

### GET /api/reports/orders

Order breakdown by status and by date within the date range (defaults to the last 14 days when dates are absent).

| Query parameter | Type   | Default | Notes                                       |
| --------------- | ------ | ------- | ------------------------------------------- |
| `start_date`    | date   | –       | ISO `YYYY-MM-DD`, inclusive lower bound     |
| `end_date`      | date   | –       | ISO `YYYY-MM-DD`, inclusive upper bound     |

```json
{
  "success": true,
  "data": {
    "start_date": "2026-08-10",
    "end_date": "2026-08-23",
    "summary": { "count": 3, "total": 706.0 },
    "by_status": [
      { "status": "Pending", "count": 1, "total": 250.0 },
      { "status": "Completed", "count": 2, "total": 456.0 }
    ],
    "by_date": [
      { "date": "2026-08-23", "label": "23 Aug", "count": 3, "total": 706.0 }
    ]
  }
}
```

### GET /api/reports/inventory

| Query parameter | Type   | Default   | Notes                                                        |
| --------------- | ------ | --------- | ------------------------------------------------------------ |
| `report_type`   | string | `current` | `current` \| `low` \| `movements` (else 422)                 |

`current` lists active materials with stock, minimum, cost and a computed low-stock flag; `low` lists only materials at or below their minimum; `movements` returns the latest 300 `inventory_transactions` rows (item name, type, quantity, balance after, note, timestamp) newest first.

```json
{
  "success": true,
  "data": {
    "report_type": "current",
    "summary": { "active_items": 3, "low_stock": 1, "total_value": 1120.0 },
    "items": [
      {
        "id": 1, "name": "Milk", "category": "Dairy", "unit": "Litre",
        "current_quantity": 2.0, "minimum_stock": 3.0, "purchase_price": 56.0,
        "is_low_stock": true, "is_active": true
      }
    ]
  }
}
```

### GET /api/reports/purchases

Purchase totals grouped by supplier or by date, date-filtered.

| Query parameter | Type   | Default    | Notes                                          |
| --------------- | ------ | ---------- | ---------------------------------------------- |
| `group_by`      | string | `date`     | `supplier` \| `date` (else 422)                |
| `start_date`    | date   | –          | ISO `YYYY-MM-DD`, inclusive lower bound        |
| `end_date`      | date   | –          | ISO `YYYY-MM-DD`, inclusive upper bound        |

Response `data`: `group_by`, `start_date`, `end_date`, `summary { count, total }` and `items[]` — grouped rows with `name` (supplier) or `date`/`label` (day) plus `count` and `total`.

### GET /api/reports/salaries

Monthly salary expense across the whole history (no filters). Response `data`:

```json
{
  "summary": { "total": 52400.0, "records": 4 },
  "items": [
    { "month": "2026-08", "count": 2, "total": 26200.0 }
  ]
}
```

Newest month first. `total` uses the recorded `net_salary`.

### GET /api/reports/expenses

Expense totals grouped by category or by date, date-filtered.

| Query parameter | Type   | Default      | Notes                                 |
| --------------- | ------ | ------------ | ------------------------------------- |
| `group_by`      | string | `category`   | `category` \| `date` (else 422)       |
| `start_date`    | date   | –            | ISO `YYYY-MM-DD`, inclusive           |
| `end_date`      | date   | –            | ISO `YYYY-MM-DD`, inclusive           |

Response `data`: `group_by`, `start_date`, `end_date`, `summary { count, total }` and `items[]` — grouped rows with `category` or `date`/`label` plus `count` and `total`, categories sorted highest total first.

### GET /api/reports/profit

Estimated profit summary: **Sales − Purchases − Salaries − Expenses**, each component returned so the client never has to trust a stored number. The figure is explicitly labelled an estimate because salaries are matched by month, not by an exact day.

| Query parameter | Type   | Default | Notes                                      |
| --------------- | ------ | ------- | ------------------------------------------ |
| `start_date`    | date   | –       | ISO `YYYY-MM-DD`, inclusive lower bound    |
| `end_date`      | date   | –       | ISO `YYYY-MM-DD`, inclusive upper bound    |

```json
{
  "success": true,
  "data": {
    "start_date": null,
    "end_date": null,
    "components": { "sales": 252.0, "purchases": 0.0, "salaries": 0.0, "expenses": 2500.0 },
    "estimated_profit": -2248.0,
    "labelled_note": "Estimated management summary — salaries are matched by month, not by an exact day."
  }
}
```

### GET /api/dashboard

Live landing-page numbers for the admin dashboard (Phase 15). Everything is recomputed at request time from recorded data — nothing is stored on the dashboard side. Definitions mirror the rest of the system: **today's sales** = paid orders created today, **pending orders** = open (Pending/Preparing/Ready) orders, **unpaid bills** = outstanding value of unpaid non-cancelled orders, **low stock** = active materials at or below their minimum, **monthly expenses** = running costs since the 1st of this month. **Top sellers** ignore cancelled orders. The **sales trend** is a rolling 7-day window of paid totals.

```json
{
  "success": true,
  "data": {
    "cafe": { "name": "Cafe Desk", "currency": "₹" },
    "date": "2026-08-29",
    "stats": {
      "today_sales": 1550.0,
      "today_orders": 4,
      "pending_orders": 2,
      "unpaid_bills": 620.0,
      "menu_items": 36,
      "low_stock": 3,
      "employees": 8,
      "monthly_expenses": 18500.0
    },
    "sales_trend": {
      "labels": ["Sat 23", "Sun 24", "Mon 25", "Tue 26", "Wed 27", "Thu 28", "Fri 29"],
      "amounts": [0, 0, 340.0, 780.0, 620.0, 1150.0, 1550.0],
      "orders": [0, 0, 2, 4, 3, 5, 4]
    },
    "top_items": [ { "name": "Cappuccino", "quantity": 42 } ],
    "recent_orders": [ {
      "id": 1,
      "order_number": "ORD-0001",
      "order_type": "Dine-in",
      "table_number": 3,
      "status": "Completed",
      "total": 620.0,
      "payment_status": "Paid",
      "payment_method": "Cash",
      "created_at": "2026-08-29T14:12:00"
    } ]
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

- `/static/css/main.css`, `/static/css/dashboard.css`, `/static/css/menu.css`, `/static/css/orders.css`, `/static/css/inventory.css`, `/static/css/purchases.css`, `/static/css/expenses.css`, `/static/css/reports.css`, `/static/css/responsive.css`, `/static/css/public-menu.css`
- `/static/js/api.js`, `/static/js/common.js`, `/static/js/validation.js`, `/static/js/dashboard.js`, `/static/js/categories.js`, `/static/js/menu-items.js`, `/static/js/orders.js`, `/static/js/billing.js`, `/static/js/suppliers.js`, `/static/js/inventory.js`, `/static/js/purchases.js`, `/static/js/employees.js`, `/static/js/salaries.js`, `/static/js/expenses.js`, `/static/js/reports.js`, `/static/js/settings.js`, `/static/js/customer-menu.js`, `/static/js/public-menu.js`
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
*Last updated: Phase 17 completion (final review — endpoint surface unchanged from Phase 15, verified against the running application and the 368-test suite).*
*Previous: Phase 15 completion (dashboard endpoint `GET /api/dashboard` added).*
