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
             category & item  ▼                reports
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
             data       │   data/cafe.db  │     data (Phases 6–14)
                         │   (SQLite file) │
                         └── stored data ──┘
```

**External entities (current):**
* **Admin/Cafe staff** — enters and manages cafe settings, menu categories and menu items, orders and payments, suppliers, stock movements, supplier purchases, employees, salaries and expenses through the browser; reads the pre-built reports.
* **Customer** — receives a shareable digital menu link (fully wired in Phase 5).

**Data stores (current):** `data/cafe.db` holding `cafe_settings`, `categories`, `menu_items`, `orders`, `order_items`, `suppliers`, `inventory_items`, `inventory_transactions`, `purchases`, `purchase_items`, `employees`, `salaries`, `expenses`.

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
Admin/Staff
    │ employee: name, mobile, role, salary type/rate | salary: month, bonus, deduction
    ▼
┌───────────────────────────┐  role/salary-type in fixed list?  ┌──────────────────────────┐
│ P9  Manage Employees &    │  unique month per employee (409)? │ D11 employees             │
│     Salaries              │──────────────────────────────────▶│                          │
│     routers/employees.py, │◀──────── rows + salary counts ────│ D12 salaries             │
│     routers/salaries.py   │  net = base + bonus − deduction   │                          │
└───────────┬───────────────┘  (server-calculated)              └──────────────────────────┘
            │ salary_count per employee; delete blocked (409) while salaries exist
            │
Admin/Staff
    │ expense: title, category, amount, date, payment method, notes
    ▼
┌───────────────────────────┐  category/method in fixed list?   ┌──────────────────────────┐
│ P10 Record Expenses       │  amount > 0?                      │ D13 expenses             │
│     routers/expenses.py   │──────────────────────────────────▶│ id, title, category,     │
└───────────┬───────────────┘◀──────── newest first + summary ──│ amount, expense_date,    │
            │                                                   │ payment_method, notes    │
            │
Admin/Staff
    │ tab + date range + mode (daily/weekly/monthly, by supplier/category…)
    ▼
┌───────────────────────────┐  read-only aggregations over recorded data ──────────────────┐
│ P11 Generate Reports      │  Sales (paid orders) · Orders · Inventory · Purchases ·      │
│     routers/reports.py    │  Salaries · Expenses · Estimated Profit                      │
└───────────────────────────┘  ───────────────────────────────────────────────────────────┘
            │ no writes — every figure recomputed live from D1, D4–D13
            ▼
     Summary cards + tables + bar chart (static/js/reports.js, printable)

Admin/Staff
    │ loads "/" (landing page)
    ▼
┌───────────────────────────┐  read-only daily/weekly aggregations ────────────────┐
│ P12 View Dashboard        │  today's sales (paid) · today's orders · pending    │
│     routers/dashboard.py  │  orders · unpaid bills · menu items · low stock ·   │
└───────────────────────────┘  employees · monthly expenses · 7-day sales trend · │
            │ no writes — recomputed live from D1–D13                            │
            ▼ Top sellers (ignore cancelled) · recent orders (D4/D5)
     Stat cards + canvas bar chart + ranking (static/js/dashboard.js)
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
| Employee payload              | Staff → P9           | name, mobile, email, address, role, joining_date, salary_type, base_salary, is_active |
| Salary payload                | Staff → P9           | employee_id, salary_month, base_salary?, bonus, deduction, payment_status, payment_date?, notes |
| Salary validation & net       | P9 → D11/D12/Browser | role/salary-type allowlists, 10-digit mobile, 409 duplicate month; net = base + bonus − deduction (server) |
| Salary list & filters         | P9 → Browser         | newest month first; filter by employee, month, payment status; stat-card totals |
| Employee delete guard         | P9 → Browser         | HTTP 409 while salary records exist                            |
| Expense payload               | Staff → P10          | title, category, amount, expense_date?, payment_method, notes  |
| Expense validation            | P10 → Browser        | 422 category/method not in allowlist, amount ≤ 0, overlong fields |
| Expense list & filters        | P10 → Browser        | newest first; search + category/method/date filters; summary totals (count, total, categories) |
| Report request                | Staff → P11          | report tab + date range + mode (period / report_type / group_by) |
| Report data                   | P11 → Browser        | read-only series/tables: sales, orders, inventory, purchases, salaries, expenses, estimated profit |
| Dashboard request             | Staff → P12          | opens `/` (page load)                                        |
| Dashboard data                | P12 → Browser        | 8 stat-card figures, 7-day sales trend, top sellers (ignoring cancelled orders), recent orders — all live reads, no writes |

---
*Last updated: Phase 17 completion (final review — processes unchanged, verified against the running application; P12 Dashboard and P14 Reports remain read-only).*
*Previous: Phase 15 completion (read-only Dashboard process P12 added; low-stock warning noted on the dashboard).*
