# Data Dictionary — Cafe Management System

This document lists every table that exists in the SQLite database (`data/cafe.db`), with field-level detail. It is updated after each phase.

## Current Status (Phase 10 — Purchases)

**Domain tables created so far: 10.** Phase 10 added `purchases` (purchase headers with server-calculated totals) and `purchase_items` (purchased material lines that automatically increase inventory).

| Table                   | Purpose                                       | Phase |
| ----------------------- | --------------------------------------------- | ----- |
| cafe_settings           | Cafe profile, tax %, currency, receipt        | 2     |
| categories              | Menu categories                               | 3     |
| menu_items              | Menu items with price, image, flags           | 4     |
| orders                  | Order headers with bill and payment           | 6–7   |
| order_items             | Order line items with price snapshots         | 6     |
| suppliers               | Supplier master records                       | 8     |
| inventory_items         | Raw materials with stock levels               | 9     |
| inventory_transactions  | Stock movement history                        | 9     |
| purchases               | Purchase headers with totals and payment      | 10    |
| purchase_items          | Purchased material lines                      | 10    |

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

## Table: suppliers

Businesses the cafe buys raw materials from. Created in Phase 8.

| Field Name         | Data Type    | Description                                        | Primary Key | Foreign Key | Nullable | Example                |
| ------------------ | ------------ | -------------------------------------------------- | ----------- | ----------- | -------- | ---------------------- |
| id                 | INTEGER      | Auto-increment identifier                          | Yes         | No          | No       | 1                      |
| name               | VARCHAR(100) | Supplier display name, unique (any case)           | No          | No          | No       | Gokul Dairy            |
| contact_person     | VARCHAR(100) | Person to call                                     | No          | No          | Yes      | Ramesh Patel           |
| phone              | VARCHAR(15)  | 10-digit Indian mobile number (validated)          | No          | No          | Yes      | 9876543210             |
| email              | VARCHAR(100) | Valid email address (stored lowercase)             | No          | No          | Yes      | orders@gokuldairy.in   |
| address            | VARCHAR(255) | Shop / warehouse address                           | No          | No          | Yes      | 12 Market Yard, Pune   |
| materials_supplied | VARCHAR(255) | Free-text list of what they supply                 | No          | No          | Yes      | Milk, Paneer, Butter   |
| is_active          | BOOLEAN      | Active flag; inactive rows hidden when filtered    | No          | No          | No       | 1                      |
| created_at         | DATETIME     | Row creation timestamp (auto)                      | No          | No          | No       | 2026-08-23 14:00:00    |
| updated_at         | DATETIME     | Last update timestamp (auto)                       | No          | No          | Yes      | 2026-08-23 15:10:22    |

**Constraints & rules:** UNIQUE on `name` (`uq_suppliers_name`) plus a case-insensitive API check returning HTTP 409; `phone` must match the 10-digit pattern and `email` must be valid when provided; strings are trimmed and empty optionals stored as NULL. Deleting a supplier is always allowed — linked raw materials keep all data with their `supplier_id` cleared.

## Table: inventory_items

Raw materials with their live stock level. Created in Phase 9. The level changes only through movements recorded in `inventory_transactions`.

| Field Name       | Data Type    | Description                                          | Primary Key | Foreign Key                          | Nullable | Example                  |
| ---------------- | ------------ | ---------------------------------------------------- | ----------- | ------------------------------------ | -------- | ------------------------ |
| id               | INTEGER      | Auto-increment identifier                            | Yes         | No                                   | No       | 1                        |
| name             | VARCHAR(120) | Material name, unique (any case)                     | No          | No                                   | No       | Milk                     |
| category         | VARCHAR(80)  | Free-text grouping (Dairy, Vegetables…)              | No          | No                                   | No       | Dairy                    |
| unit             | VARCHAR(12)  | Kg / Gram / Litre / Millilitre / Piece / Packet / Box| No          | No                                   | No       | Litre                    |
| current_quantity | FLOAT        | Live stock level; ≥ 0; changed only via movements    | No          | No                                   | No       | 2.0                      |
| minimum_stock    | FLOAT        | Low-stock threshold; ≥ 0                             | No          | No                                   | No       | 3.0                      |
| purchase_price   | FLOAT        | Cost per unit; ≥ 0, rounded to 2 dp                  | No          | No                                   | No       | 56.0                     |
| supplier_id      | INTEGER      | Preferred supplier; cleared if the supplier is deleted | No        | Yes → suppliers (ON DELETE SET NULL) | Yes      | 1                        |
| is_active        | BOOLEAN      | Active flag                                          | No          | No                                   | No       | 1                        |
| notes            | VARCHAR(255) | Storage tips, brand preference…                      | No          | No                                   | Yes      | Keep refrigerated        |
| created_at       | DATETIME     | Row creation timestamp (auto)                        | No          | No                                   | No       | 2026-08-23 14:05:00      |
| updated_at       | DATETIME     | Last change timestamp (auto)                         | No          | No                                   | Yes      | 2026-08-23 16:40:11      |

**Constraints & rules:** UNIQUE on `name` (`uq_inventory_items_name`); quantities round to 3 decimals and prices to 2; negative values rejected (422); `unit` restricted to the fixed list; unknown `supplier_id` refused with HTTP 404. Derived flag: low stock = `current_quantity <= minimum_stock`. PUT updates descriptive fields only — never the quantity.

## Table: inventory_transactions

One row per stock movement — the audit trail behind every quantity change. Created in Phase 9.

| Field Name       | Data Type    | Description                                                   | Primary Key | Foreign Key                              | Nullable | Example             |
| ---------------- | ------------ | ------------------------------------------------------------- | ----------- | ---------------------------------------- | -------- | ------------------- |
| id               | INTEGER      | Auto-increment identifier                                     | Yes         | No                                       | No       | 1                   |
| item_id          | INTEGER      | Material that moved                                           | No          | Yes → inventory_items (ON DELETE CASCADE)| No       | 1                   |
| transaction_type | VARCHAR(12)  | "Stock In" / "Stock Out" / "Adjustment"                       | No          | No                                       | No       | Stock Out           |
| quantity         | FLOAT        | Amount moved (> 0) for In/Out; new counted total (≥ 0) for Adjustment | No | No                                 | No       | 8.0                 |
| balance_after    | FLOAT        | Stock level once the movement was applied (snapshot)          | No          | No                                       | No       | 2.0                 |
| note             | VARCHAR(200) | Free-text remark                                              | No          | No                                       | Yes      | Morning delivery    |
| created_at       | DATETIME     | Movement timestamp (auto)                                     | No          | No                                       | No       | 2026-08-23 16:40:11 |

**Constraints & rules:** In/Out require quantity > 0 while Adjustment requires ≥ 0 (schema-enforced); Stock Out uses an atomic guarded UPDATE (`WHERE current_quantity >= quantity`) so concurrent removals cannot oversell; a failed movement writes nothing, every successful one snapshots `balance_after`; deleting a material deletes its history (cascade).

## Table: purchases

One row per recorded supplier purchase. All money values are calculated once by the server when the purchase is recorded; recording a purchase also increases inventory in the same database transaction. Created in Phase 10.

| Field Name      | Data Type    | Description                                                | Primary Key | Foreign Key                        | Nullable | Example            |
| --------------- | ------------ | ---------------------------------------------------------- | ----------- | ---------------------------------- | -------- | ------------------ |
| id              | INTEGER      | Auto-increment identifier                                  | Yes         | No                                 | No       | 1                  |
| purchase_number | VARCHAR(20)  | Human-friendly number `PUR-xxxx`, derived from id          | No          | No                                 | No       | PUR-0001           |
| supplier_id     | INTEGER      | Supplier; SET NULL if the supplier is deleted later        | No          | Yes → suppliers (ON DELETE SET NULL)| Yes      | 1                  |
| supplier_name   | VARCHAR(100) | Supplier name snapshot at purchase time                    | No          | No                                 | No       | Gokul Dairy        |
| purchase_date   | DATE         | Delivery/invoice date; defaults to today                   | No          | No                                 | No       | 2026-08-23         |
| subtotal        | FLOAT        | Sum of all line totals (2 dp, server-calculated)           | No          | No                                 | No       | 940.0              |
| total           | FLOAT        | Grand total (= subtotal for purchases)                     | No          | No                                 | No       | 940.0              |
| payment_status  | VARCHAR(10)  | "Unpaid" or "Paid"                                         | No          | No                                 | No       | Unpaid             |
| notes           | VARCHAR(255) | Free-text remark (invoice number…)                         | No          | No                                 | Yes      | Invoice INV-77     |
| created_at      | DATETIME     | Row creation timestamp (auto)                              | No          | No                                 | No       | 2026-08-23 18:00:00|
| updated_at      | DATETIME     | Last change timestamp (auto)                               | No          | No                                 | Yes      | 2026-08-23 18:05:12|

**Constraints & rules:** UNIQUE on `purchase_number`; the API refuses unknown suppliers with HTTP 404 and inactive materials with HTTP 409; each material may appear once per purchase; totals are computed exclusively server-side; purchases are record-only — no edit/delete endpoints. Deleting a supplier keeps purchases readable (`supplier_id` cleared, name snapshot retained).

## Table: purchase_items

One row per purchased material line, belonging to exactly one purchase. Created in Phase 10.

| Field Name        | Data Type    | Description                                              | Primary Key | Foreign Key                                       | Nullable | Example    |
| ----------------- | ------------ | -------------------------------------------------------- | ----------- | ------------------------------------------------- | -------- | ---------- |
| id                | INTEGER      | Auto-increment identifier                                | Yes         | No                                                | No       | 1          |
| purchase_id       | INTEGER      | Owning purchase                                          | No          | Yes → purchases (ON DELETE CASCADE)               | No       | 1          |
| inventory_item_id | INTEGER      | Source raw material; SET NULL if the material is deleted | No          | Yes → inventory_items (ON DELETE SET NULL)        | Yes      | 3          |
| item_name         | VARCHAR(120) | Material name snapshot at purchase time                  | No          | No                                                | No       | Milk       |
| unit              | VARCHAR(12)  | Unit snapshot at purchase time                           | No          | No                                                | No       | Litre      |
| quantity          | FLOAT        | Units purchased; > 0, rounded to 3 dp                    | No          | No                                                | No       | 2.5        |
| unit_cost         | FLOAT        | Cost per unit agreed with the supplier; ≥ 0, 2 dp        | No          | No                                                | No       | 56.0       |
| line_total        | FLOAT        | quantity × unit_cost (2 dp, server-calculated)           | No          | No                                                | No       | 140.0      |

**Constraints & rules:** deleting a purchase removes its lines (cascade); snapshots keep history readable after renames/deletions; every successful line also writes one `Stock In` row in `inventory_transactions` (note `Purchase PUR-xxxx`) and increases `current_quantity` — all within the same transaction as the header.

## Planned Tables (not yet created)

| Table                  | Purpose                                   | Phase |
| ---------------------- | ----------------------------------------- | ----- |
| employees              | Employee master                           | 11    |
| salaries               | Salary payments                           | 12    |
| expenses               | Operating expenses                        | 13    |

---
*Last updated: Phase 10 completion (purchases + purchase_items added).*
*Previous: Phase 8–9 completion (suppliers + inventory_items + inventory_transactions added).*
