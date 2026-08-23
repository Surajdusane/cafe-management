# Data Dictionary — Cafe Management System

This document lists every table that exists in the SQLite database (`data/cafe.db`), with field-level detail. It is updated after each phase.

## Current Status (Phase 7 — Billing)

**Domain tables created so far: 5.** Phase 6–7 added `orders` (order header + bill + payment state) and `order_items` (snapshotted order lines).

| Table          | Purpose                                  | Phase |
| -------------- | ---------------------------------------- | ----- |
| cafe_settings  | Cafe profile, tax %, currency, receipt   | 2     |
| categories     | Menu categories                          | 3     |
| menu_items     | Menu items with price, image, flags      | 4     |
| orders         | Order headers with bill and payment      | 6–7   |
| order_items    | Order line items with price snapshots    | 6     |

## Table: cafe_settings

Single-row configuration table (singleton). The row with `id = 1` is created automatically the first time settings are read or saved.

| Field Name     | Data Type    | Description                                    | Primary Key | Foreign Key | Nullable | Example                     |
| -------------- | ------------ | ---------------------------------------------- | ----------- | ----------- | -------- | --------------------------- |
| id             | INTEGER      | Singleton row identifier, always 1             | Yes         | No          | No       | 1                           |
| cafe_name      | VARCHAR(100) | Display name of the cafe                       | No          | No          | No       | Brew & Bean Cafe            |
| address        | VARCHAR(255) | Physical address of the cafe                   | No          | No          | Yes      | 12 Station Road, Pune       |
| phone          | VARCHAR(15)  | Contact mobile number (10 digits)              | No          | No          | Yes      | 9876543210                  |
| email          | VARCHAR(100) | Contact email address                          | No          | No          | Yes      | hello@brewbean.in           |
| logo_url       | VARCHAR(300) | URL/path of the cafe logo image                | No          | No          | Yes      | /static/images/logo.png     |
| tax_percent    | FLOAT        | Default tax percentage applied on bills (0–100)| No          | No          | No       | 5.5                         |
| currency       | VARCHAR(8)   | Currency symbol used across reports/bills      | No          | No          | No       | ₹                           |
| receipt_footer | VARCHAR(200) | Message printed at the bottom of receipts      | No          | No          | Yes      | Thank you for visiting!     |
| updated_at     | DATETIME     | Timestamp of the last update (auto-managed)    | No          | No          | Yes      | 2026-08-23 09:47:11         |

**Validation rules enforced by the API (Pydantic):** `cafe_name`, `currency` required; `tax_percent` between 0 and 100; `phone` must match a 10-digit Indian mobile pattern when provided; `email` must be a valid email format when provided; strings are trimmed and empty optional values are stored as NULL.

## Table: categories

Menu categories that group items (Coffee, Tea, Snacks…). Created in Phase 3.

| Field Name   | Data Type    | Description                                  | Primary Key | Foreign Key | Nullable | Example                 |
| ------------ | ------------ | -------------------------------------------- | ----------- | ----------- | -------- | ----------------------- |
| id           | INTEGER      | Auto-increment identifier                    | Yes         | No          | No       | 1                       |
| name         | VARCHAR(80)  | Category display name, unique (any case)     | No          | No          | No       | Coffee                  |
| description  | VARCHAR(255) | Short description shown to customers         | No          | No          | Yes      | Espresso-based hot      |
| is_active    | BOOLEAN      | Active flag; inactive rows are hidden        | No          | No          | No       | 1                       |
| created_at   | DATETIME     | Row creation timestamp (auto)                | No          | No          | No       | 2026-08-23 10:20:13     |
| updated_at   | DATETIME     | Last update timestamp (auto)                 | No          | No          | Yes      | 2026-08-23 11:02:44     |

**Constraints & rules:** UNIQUE on `name` (`uq_categories_name`); the API additionally rejects duplicates case-insensitively with HTTP 409; a category cannot be deleted while menu items reference it.

## Table: menu_items

Dishes/drinks sold by the cafe. Created in Phase 4.

| Field Name    | Data Type    | Description                                    | Primary Key | Foreign Key       | Nullable | Example                    |
| ------------- | ------------ | ---------------------------------------------- | ----------- | ----------------- | -------- | -------------------------- |
| id            | INTEGER      | Auto-increment identifier                      | Yes         | No                | No       | 1                          |
| category_id   | INTEGER      | Owning category                                | No          | Yes → categories  | No       | 1                          |
| name          | VARCHAR(120) | Item display name, unique within its category  | No          | No                | No       | Cappuccino                 |
| description   | VARCHAR(500) | Short description shown to customers           | No          | No                | Yes      | Espresso with steamed milk |
| price         | FLOAT        | Selling price; must be > 0, rounded to 2 dp    | No          | No                | No       | 120.0                      |
| image_url     | VARCHAR(300) | URL/path of the item photo                     | No          | No                | Yes      | /static/images/latte.png   |
| is_vegetarian | BOOLEAN      | Vegetarian flag                                | No          | No                | No       | 1                          |
| is_popular    | BOOLEAN      | Highlighted as popular                         | No          | No                | No       | 0                          |
| is_available  | BOOLEAN      | In stock / orderable                           | No          | No                | No       | 1                          |
| created_at    | DATETIME     | Row creation timestamp (auto)                  | No          | No                | No       | 2026-08-23 10:25:00        |
| updated_at    | DATETIME     | Last update timestamp (auto)                   | No          | No                | Yes      | 2026-08-23 11:10:12        |

**Constraints & rules:** FK `category_id → categories.id` enforced by SQLite (`PRAGMA foreign_keys=ON`); UNIQUE on `(category_id, name)` (`uq_menu_items_category_name`) plus a case-insensitive API check returning HTTP 409; `price > 0`; names/descriptions are trimmed and empty optional values stored as NULL.

## Table: orders

One row per customer order. The bill lives here too: the order number doubles as the bill number and all money values are calculated once by the server when the order is placed. Created in Phase 6, payment fields completed in Phase 7.

| Field Name      | Data Type    | Description                                              | Primary Key | Foreign Key | Nullable | Example            |
| --------------- | ------------ | -------------------------------------------------------- | ----------- | ----------- | -------- | ------------------ |
| id              | INTEGER      | Auto-increment identifier                                | Yes         | No          | No       | 1                  |
| order_number    | VARCHAR(20)  | Human-friendly number `ORD-xxxx`, derived from id        | No          | No          | No       | ORD-0001           |
| order_type      | VARCHAR(10)  | "Dine-in" or "Takeaway"                                  | No          | No          | No       | Dine-in            |
| table_number    | INTEGER      | Table 1–999; always NULL for takeaways                   | No          | No          | Yes      | 4                  |
| status          | VARCHAR(12)  | Pending / Preparing / Ready / Completed / Cancelled      | No          | No          | No       | Preparing          |
| subtotal        | FLOAT        | Sum of all line totals (2 dp)                            | No          | No          | No       | 250.0              |
| discount_amount | FLOAT        | Flat rupee discount; ≥ 0 and ≤ subtotal                  | No          | No          | No       | 10.0               |
| tax_percent     | FLOAT        | Tax rate snapshot taken from cafe_settings at order time | No          | No          | No       | 5.0                |
| tax_amount      | FLOAT        | (subtotal − discount) × tax_percent / 100                | No          | No          | No       | 12.0               |
| total           | FLOAT        | subtotal − discount + tax — the grand total              | No          | No          | No       | 252.0              |
| payment_method  | VARCHAR(10)  | Cash / UPI / Card / Other; NULL until paid               | No          | No          | Yes      | UPI                |
| payment_status  | VARCHAR(10)  | "Unpaid" or "Paid"; set by the billing API only          | No          | No          | No       | Paid               |
| paid_at         | DATETIME     | When the payment was recorded                            | No          | No          | Yes      | 2026-08-23 13:02:11|
| created_at      | DATETIME     | Order placement timestamp (auto)                         | No          | No          | No       | 2026-08-23 13:00:00|
| updated_at      | DATETIME     | Last change timestamp (auto)                             | No          | No          | Yes      | 2026-08-23 13:02:11|

**Constraints & rules:** UNIQUE on `order_number`; dine-in requires a table number while takeaways force it to NULL; quantity/discount rules live in the Pydantic schema; cancelled orders become immutable; only cancelled orders may be deleted; paid orders can never be cancelled.

## Table: order_items

One row per ordered dish line, belonging to exactly one order. Created in Phase 6.

| Field Name   | Data Type    | Description                                          | Primary Key | Foreign Key                    | Nullable | Example          |
| ------------ | ------------ | ---------------------------------------------------- | ----------- | ------------------------------ | -------- | ---------------- |
| id           | INTEGER      | Auto-increment identifier                            | Yes         | No                             | No       | 1                |
| order_id     | INTEGER      | Owning order                                         | No          | Yes → orders                   | No       | 1                |
| menu_item_id | INTEGER      | Source dish; SET NULL if the dish is deleted later   | No          | Yes → menu_items (ON DELETE SET NULL) | Yes | 3           |
| item_name    | VARCHAR(120) | Dish name snapshot at order time                     | No          | No                             | No       | Cappuccino       |
| unit_price   | FLOAT        | Price snapshot at order time                         | No          | No                             | No       | 120.0            |
| quantity     | INTEGER      | Units ordered; integer 1–999                         | No          | No                             | No       | 2                |
| line_total   | FLOAT        | quantity × unit_price (2 dp)                         | No          | No                             | No       | 240.0            |

**Constraints & rules:** deleting an order removes its lines (ORM cascade `all, delete-orphan`); snapshots guarantee historical bills never change when the menu changes; the API rejects the same dish twice on one order — raise its quantity instead.

## Planned Tables (not yet created)

| Table                  | Purpose                                   | Phase |
| ---------------------- | ----------------------------------------- | ----- |
| suppliers              | Supplier master                           | 8     |
| inventory_items        | Raw materials with stock levels           | 9     |
| inventory_transactions | Stock add/reduce history                  | 9     |
| purchases              | Purchase headers                          | 10    |
| purchase_items         | Purchase line items                       | 10    |
| employees              | Employee master                           | 11    |
| salaries               | Salary payments                           | 12    |
| expenses               | Operating expenses                        | 13    |

---
*Last updated: Phase 6–7 completion (orders + order_items added).*
*Previous: Phase 5 completion (Customer Digital Menu; no schema change).*
