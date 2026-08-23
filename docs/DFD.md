# Data Flow Diagrams (DFD) — Cafe Management System

The DFDs grow as phases are implemented. Processes shown in solid detail exist today; dashed/planned elements arrive in later phases.

## Context-Level DFD (Level 0)

The whole system is a single process interacting with external entities.

```text
                    ┌────────────────────┐
                    │      Admin /       │
                    │   Cafe staff       │
                    └─────────┬──────────┘
             settings,        │                menus, lists,
             category & item  ▼                reports (future)
              data  ┌───────────────────────┐
        ┌──────────▶│                       │──────────┐
        │           │   CAFE MANAGEMENT     │          ▼
        │           │      SYSTEM           │   ┌────────────┐
        └───────────│   (FastAPI + SQLite)  │   │  Customer  │
   confirmations &  │                       │   │ (Phase 5+) │
   error messages   └───────────┬───────────┘   └────────────┘
                        ▲        │        ▲
             stock &    │        │        │     purchases,
             supplier   │        ▼        │     salaries, expenses
             data       │   data/cafe.db  │     data (Phases 6–13)
                        │   (SQLite file) │
                        └── stored data ──┘
```

**External entities (current):**
* **Admin/Cafe staff** — enters and manages cafe settings, menu categories and menu items, orders and payments, suppliers, stock movements and supplier purchases through the browser.
* **Customer** — receives a shareable digital menu link (fully wired in Phase 5).

**Data stores (current):** `data/cafe.db` holding `cafe_settings`, `categories`, `menu_items`, `orders`, `order_items`, `suppliers`, `inventory_items`, `inventory_transactions`, `purchases`, `purchase_items`.

## Level-1 DFD

Implemented processes only. Each numbered process maps to real modules in the codebase.

```text
Admin/Staff
    │
    │ form input (JSON via fetch)
    ▼
┌───────────────────────────┐   validate payload    ┌──────────────────────────┐
│ P1  Manage Cafe Settings  │──────────────────────▶│ D1 cafe_settings         │
│     routers/settings.py   │◀──────────────────────│ (singleton row id = 1)   │
└───────────────────────────┘   saved profile       └──────────────────────────┘

Admin/Staff
    │
    ▼
┌───────────────────────────┐  name unique? active? ┌──────────────────────────┐
│ P2  Manage Categories     │──────────────────────▶│ D2 categories            │
│     routers/categories.py │◀──────────────────────│ id, name, description,   │
└───────────────────────────┘  list + item counts    │ is_active, timestamps    │
    │              ▲                                 └──────────────────────────┘
    │ delete guard │ "N items still use it"                 │ category_id
    ▼              │                                        ▼
┌───────────────────────────┐  category exists? price>0? dup in category?
│ P3  Manage Menu Items     │──────────────────────────────────────────────┐
│     routers/menu.py       │                                              ▼
└───────────────────────────┘                               ┌──────────────────────────┐
    │                                                       │ D3 menu_items            │
    │  items + nested category summary                      │ FK → D2, unique per cat. │
    ▼                                                       └──────────────────────────┘
Browser renders tables, modals, toasts (static/js/categories.js, menu-items.js)

Admin/Staff
    │ order: type, table, items[], discount
    ▼
┌───────────────────────────┐  item exists? available? qty 1–999?  ┌──────────────────────────┐
│ P4  Take Orders           │─────────────────────────────────────▶│ D3 menu_items (read)     │
│     routers/orders.py     │◀─────── names + prices snapshot ─────│                          │
└───────────┬───────────────┘                                      └──────────────────────────┘
            │ server calculates subtotal − discount + tax
            ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ D4 orders / D5 order_items   ORD-xxxx number, totals snapshot, status, payment state  │
└───────────────────────────────────────────────────────────────────────────────────────┘
            ▲ status updates (Preparing → Ready → Completed / Cancelled)
            │
Admin/Staff
    │ payment: Cash | UPI | Card | Other
    ▼
┌───────────────────────────┐  already paid? cancelled?            ┌──────────────────────────┐
│ P5  Bill & Receive        │─────────────────────────────────────▶│ D4 orders                │
│     routers/billing.py    │◀─────── marks Paid + paid_at ────────│ payment columns          │
└───────────┬───────────────┘                                      └──────────────────────────┘
            │ bill detail + cafe branding (name, currency, footer from D1)
            ▼
     Printable receipt (browser print)

Customer (Phase 5): reads branding from D1 and published menu rows from D2/D3 via
/api/public/menu — read-only, no ids or admin fields.

Admin/Staff
    │ supplier: name, contact, phone, email, materials supplied
    ▼
┌───────────────────────────┐  name unique? phone/email format?   ┌──────────────────────────┐
│ P6  Manage Suppliers      │────────────────────────────────────▶│ D6 suppliers             │
│     routers/suppliers.py  │◀──────────────── rows + material counts ─│ id, contact, materials │
└───────────┬───────────────┘                                     └────────────┬─────────────┘
            │ supplier_id (optional preferred link)                             │
            ▼                                                                   │
┌───────────────────────────┐  unit valid? qty ≥ 0? supplier exists?            │
│ P7  Track Inventory       │───────────────────────────────────────────────────┘
│     routers/inventory.py  │
└───────────┬───────────────┘
            │ Stock In (+q) / Stock Out (−q, atomic guard qty ≤ balance) / Adjustment (=new total)
            ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ D7 inventory_items / D8 inventory_transactions   level snapshot `balance_after`       │
└───────────────────────────────────────────────────────────────────────────────────────┘
            ▲ low-stock flag: level ≤ minimum_stock → warning on page & dashboard
            │
Admin/Staff
    │ purchase: supplier, date, items[{material, qty, unit cost}], payment status
    ▼
┌───────────────────────────┐  supplier exists? materials active?  ┌──────────────────────────┐
│ P8  Record Purchases      │  qty > 0? cost ≥ 0? no duplicates?   │ D6 suppliers (read)      │
│     routers/purchases.py  │─────────────────────────────────────▶│ D7 inventory_items (read)│
└───────────┬───────────────┘                                      └──────────────────────────┘
            │ server calculates line totals + grand total, assigns PUR-xxxx
            │ ONE transaction:
            ├──▶ D9 purchases / D10 purchase_items   header + material lines
            └──▶ D7 inventory_items (+qty) with a "Stock In" row in D8 per line
            ▲ failed validation rolls everything back — stock never half-updates
            │
Planned (not yet implemented):
P9 Employees & Salaries (Phases 11–12), P10 Expenses (Phase 13), Reports (Phase 14)
```

### Data dictionary of flows

| Flow                          | From → To            | Contents                                             |
| ----------------------------- | -------------------- | ---------------------------------------------------- |
| Settings form data            | Staff → P1           | cafe_name, address, phone, email, tax %, currency…   |
| Saved settings                | P1 ↔ D1              | singleton row read/update                            |
| Category payload              | Staff → P2           | name, description, is_active                         |
| Category list + counts        | P2 → Browser         | items[] each with live item_count                    |
| Delete guard message          | P2 → Browser         | HTTP 409 "items still use it"                        |
| Menu-item payload             | Staff → P3           | category_id, name, price, flags, image_url           |
| Item validation               | P3 → Browser         | 404 unknown category · 409 duplicate · 422 field errors |
| Item list                     | P3 → Browser         | items[] with embedded brief category                 |
| Order payload                 | Staff → P4           | order_type, table_number?, items[{menu_item_id, qty}], discount |
| Order validation              | P4 ↔ D3              | existence + availability of every dish; price snapshot |
| Calculated bill               | P4 → D4 / Browser    | subtotal, discount, tax %, tax, total (server-computed) |
| Status change                 | Staff → P4           | Pending → Preparing → Ready → Completed / Cancelled   |
| Payment payload               | Staff → P5           | payment_method: Cash / UPI / Card / Other             |
| Receipt data                  | P5 → Browser         | bill lines + totals + cafe name/currency/footer      |
| Supplier payload              | Staff → P6           | name, contact_person, phone, email, address, materials_supplied, is_active |
| Supplier validation           | P6 → Browser         | 409 duplicate name · 422 phone/email/length errors    |
| Supplier list                 | P6 → Browser         | items[] each with live inventory_item_count           |
| Material payload              | Staff → P7           | name, category, unit, opening qty, minimum stock, price, supplier_id? |
| Movement payload              | Staff → P7           | transaction_type: Stock In / Stock Out / Adjustment; quantity; note? |
| Stock validation & update     | P7 ↔ D7/D8           | unit enum + ≥ 0 checks; atomic guarded decrement; balance_after snapshot |
| Low-stock warning             | P7 → Browser         | is_low_stock flag per item + summary counters         |
| Movement history              | P7 → Browser         | rows with type, quantity, balance_after, note (newest first) |
| Purchase payload              | Staff → P8           | supplier_id, purchase_date?, items[{inventory_item_id, quantity, unit_cost}], payment_status?, notes? |
| Purchase validation           | P8 ↔ D6/D7           | supplier exists (404); materials exist + active (404/409); qty > 0; cost ≥ 0; no duplicate lines |
| Calculated purchase totals    | P8 → D9/D10/Browser  | line_total = qty × cost; subtotal = total = Σ lines (server-computed) |
| Automatic stock update        | P8 → D7/D8           | +quantity per material + "Stock In" history row noting `Purchase PUR-xxxx` — same transaction as the header |
| Purchase history & filters    | P8 → Browser         | rows newest first; search by number/supplier, supplier, payment status, date range; summary totals |

---
*Last updated: Phase 10 completion (Purchase recording process added).*
*Previous: Phase 8–9 completion (Supplier and Inventory processes added).*
