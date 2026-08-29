# Cafe Management System

A final-year project documentation for a web-based Cafe Management System developed with Python (FastAPI), SQLite and Vanilla JavaScript.

---

## Revision History

| Version | Date       | Change                                              |
| ------- | ---------- | --------------------------------------------------- |
| 1.0     | 2026-08-23 | Initial documentation · Phase 1 Foundation complete |
| 1.1     | 2026-08-23 | Proper uv project setup (pyproject.toml, uv.lock, cafe-server script) |
| 1.2     | 2026-08-23 | Phase 2 Cafe Settings implemented (API + UI + tests) |
| 1.3     | 2026-08-23 | Phases 3–4 Menu Management implemented (categories + menu items CRUD) |
| 1.4     | 2026-08-23 | Phase 5 Customer Digital Menu implemented (public /menu/cafe page + API + tests) |
| 1.5     | 2026-08-23 | Phases 6–7 Orders & Billing implemented (orders CRUD + workflow, server-calculated bills, payments, printable receipt) |
| 1.6     | 2026-08-23 | Phases 8–9 Suppliers & Inventory implemented (supplier CRUD, raw materials with units/min stock/supplier link, atomic Stock In/Out/Adjustment movements with history and low-stock warnings) |
| 1.7     | 2026-08-23 | Phase 10 Purchase Management implemented (multi-item purchases with server-calculated totals, automatic inventory update in one transaction, purchase history with search/date/supplier/payment filters) |
| 1.8     | 2026-08-29 | Phases 11–14 Employees, Salaries, Expenses & Reports implemented (employee CRUD with salary-delete guard; monthly salary records with server-calculated net salary; expense recording with category/payment-method allowlists and filters; report module with seven tabs — sales, orders, inventory, purchases, salaries, expenses and estimated profit) |

---

## Chapter 1 — Company Profile

This project is developed as an academic final-year submission for the BCA / BBA Computer Application program. The "client" context is a small-to-medium cafe that currently manages its daily operations manually.

**Developer:** Final-year student project team
**Project duration:** One academic semester
**Deliverable:** A working cafe management web application plus complete project documentation

The system is built to be demonstrated and explained in a viva; therefore the architecture stays deliberately simple and every module is understandable at student level.

## Chapter 2 — System Analysis

### Study of Present System

In the present system the cafe typically works with:

* A printed or handwritten menu
* Paper order pads carried by waiters
* Handwritten bills calculated on a calculator
* Notebooks for stock, purchases and supplier dues
* Registers for employee attendance and salaries
* Manual end-of-day sales totalling

### Problems in Present System

* Bills are slow to calculate and prone to arithmetic errors
* No instant view of today's sales or pending orders
* Stock is tracked loosely; items run out without warning
* Supplier purchase history is scattered across notebooks
* Salary calculations take time and invite disputes
* No historical data available for reports or decisions

### Introduction to Proposed System

The proposed Cafe Management System is a local web application running on the cafe's computer. Staff manage menu, orders, billing, inventory, suppliers, employees, salaries and expenses through a browser interface backed by a FastAPI server and a single-file SQLite database.

Development follows 17 phases (see Development Phases). Phases 1–14 are complete: Foundation, Cafe Settings, Categories, Menu Items, the Customer Digital Menu, Orders, Billing, Suppliers, Inventory, Purchases, Employees, Salaries, Expenses and Reports. The live dashboard (Phase 15) and the final documentation pass remain.

### Scope of Proposed System

* Centralized management of menu, orders, billing, stock, suppliers, staff and expenses
* Centralized cafe profile configuration (name, address, tax, currency, receipt footer)
* Automatic bill calculation with tax and discount
* Raw-material inventory with units, minimum levels and a full movement history (Stock In / Stock Out / Adjustment)
* Automatic inventory increase when purchases are recorded (Phase 10)
* Basic reports: sales, orders, inventory, purchases, salaries, expenses and estimated profit
* A public customer-facing digital menu page
* Single-cafe, single-computer deployment (no cloud)

### Benefits of Proposed System

* Faster, error-free billing
* Real-time view of sales and low-stock warnings
* Every stock movement recorded with its balance, ending notebook stock-tracking
* Purchase records automatically update inventory
* Salary computation with bonus/deduction history
* Reports generated instantly from recorded data
* Reduces paperwork and manual registers

## Chapter 3 — Requirement Analysis

### Functional Requirements

| #  | Requirement                                         | Status            |
| -- | --------------------------------------------------- | ----------------- |
| 1  | Application serves admin UI with sidebar navigation | Implemented       |
| 2  | SQLite database initialized automatically           | Implemented       |
| 3  | Health API reporting app + database status          | Implemented       |
| 4  | Consistent JSON success/error response envelope     | Implemented       |
| 5  | Reusable client utilities (API wrapper, toasts, validation) | Implemented |
| 6  | Cafe settings management                            | Implemented       |
| 7  | Category CRUD                                       | Implemented       |
| 8  | Menu item CRUD with images and availability         | Implemented       |
| 9  | Public customer digital menu                        | Implemented       |
| 10 | Order creation and status tracking                  | Implemented       |
| 11 | Billing with tax/discount and printable receipt     | Implemented       |
| 12 | Supplier CRUD with search and material counts       | Implemented       |
| 13 | Inventory with stock movements and low-stock alert  | Implemented       |
| 14 | Purchases updating inventory automatically          | Implemented       |
| 15 | Employee CRUD                                       | Implemented       |
| 16 | Salary runs (base + bonus − deduction)              | Implemented       |
| 17 | Expense recording                                   | Implemented       |
| 18 | Reports and estimated profit summary                | Implemented       |
| 19 | Live dashboard statistics                           | Planned (Phase 15)|

### Non-Functional Requirements

* **Usability:** clean modern UI usable on desktop/tablet; customer menu mobile-friendly
* **Performance:** local SQLite queries respond in milliseconds for expected data volumes
* **Security:** parameterized SQLAlchemy queries, Pydantic validation, no raw SQL from user input
* **Reliability:** consistent error envelope; server remains source of truth for calculations
* **Maintainability:** modular structure (models/schemas/routers/services), documented per phase
* **Portability:** single-folder deployment; only Python + uv required

### Feasibility Study

* **Technical feasibility:** built entirely with free, well-documented open-source tools (Python, FastAPI, SQLAlchemy, SQLite)
* **Economic feasibility:** zero software licensing cost; runs on existing cafe hardware
* **Operational feasibility:** forms mirror existing paper processes; minimal training needed

### Hardware Requirements

* Any PC/laptop with 4 GB RAM (8 GB recommended)
* 200 MB free disk space
* Optional printer for receipts

### Software Requirements

* Windows / Linux / macOS
* Python 3.11+
* uv package manager
* Modern browser (Chrome/Edge/Firefox)

## Chapter 4 — System Design

Design artefacts are maintained in the `docs/` folder:

* `docs/ERD.md` — Entity Relationship Diagram (added as entities are designed, starting Phase 2–3)
* `docs/DFD.md` — Context and Level-1 Data Flow Diagrams
* `docs/DATA_DICTIONARY.md` — field-level dictionary per table
* `docs/API_DOCUMENTATION.md` — endpoint reference

### Current Architecture (Phases 2–14)

```text
Browser (HTML/CSS/JS)
    |  fetch() via static/js/api.js
    v
FastAPI application (app/main.py)
    |-- Page routes -> app/templates/*.html
    |     `-- /menu/cafe -> public-menu.html (public, no admin shell)
    |-- Static files -> static/css, js, images
    |-- /api/health -> database check
    |-- /api/settings (GET/PUT) -> routers/settings.py -> settings_service
    |-- /api/categories (CRUD)  -> routers/categories.py -> category_service
    |-- /api/menu/items (CRUD)  -> routers/menu.py -> menu_item_service
    |-- /api/orders (create/list/detail/status/delete) -> routers/orders.py -> order_service
    |-- /api/bills (list/detail/pay) -> routers/billing.py -> billing_service
    |-- /api/public/menu (GET)  -> routers/public_menu.py -> public_menu_service
    |-- /api/suppliers (CRUD + search) -> routers/suppliers.py -> supplier_service
    |-- /api/inventory (items CRUD, stock movements, history, summary)
    |                            -> routers/inventory.py -> inventory_service
    |-- /api/purchases (record/list/detail/payment-status)
    |                            -> routers/purchases.py -> purchase_service
    |-- /api/employees (list/create/detail/update/delete + search/role filters)
    |                            -> routers/employees.py -> employee_service
    |-- /api/salaries (list/create/detail/update/delete + employee/month/status filters)
    |                            -> routers/salaries.py -> salary_service
    |-- /api/expenses (list/create/detail/update/delete + /options + filters)
    |                            -> routers/expenses.py -> expense_service
    |-- /api/reports (sales/orders/inventory/purchases/salaries/expenses/profit — all GET)
    |                            -> routers/reports.py -> report_service
    `-- Error handlers -> unified JSON envelope (400/404/409/422/500)
    v
SQLAlchemy models (app/models) -> data/cafe.db (SQLite, PRAGMA foreign_keys=ON)
```

The `cafe_settings` table is a singleton (`id = 1`) created automatically on first read. Billing reads `tax_percent`, `currency` and `receipt_footer` from it: the tax rate is snapshotted onto every order at creation time so later settings changes never rewrite historical bills.

Menu data model: `Category 1:N MenuItem` (`menu_items.category_id`). Category names are unique; item names are unique **within** their category. Deleting a non-empty category is refused with HTTP 409. SQLite foreign-key enforcement is switched on for every connection, so referential integrity is guaranteed at the database level as well.

Order data model: `Order 1:N OrderItem` (`order_items.order_id`, ORM cascade). Each line snapshots the dish name and unit price (`order_items.menu_item_id` is `ON DELETE SET NULL`), so bills survive menu edits and deletions. The order number (`ORD-0001`, derived from the primary key) doubles as the bill number. Money formula — calculated exclusively server-side in `compute_totals()`: `taxable = subtotal − discount`; `tax = taxable × tax_percent/100`; `total = taxable + tax`. Orders are immutable after placement except status and payment; a wrong order is cancelled (and optionally deleted) and re-taken.

Public menu flow: the customer page `/menu/cafe` fetches `/api/public/menu`, which composes cafe branding from `cafe_settings` plus active non-empty categories and their items. The response contains only display fields — no ids, timestamps or admin flags — so nothing internal reaches the customer's browser.

Supplier data model (Phase 8): `Supplier` is a standalone master table; names are unique. Deleting a supplier is always allowed and simply clears the preferred-supplier link on raw materials (`inventory_items.supplier_id` is `ON DELETE SET NULL`) — materials, stock levels and histories stay intact.

Inventory data model (Phase 9): `InventoryItem 1:N InventoryTransaction` (ORM cascade). Material names are unique. `current_quantity` changes **only** through movements: *Stock In* adds units (> 0), *Stock Out* removes units (> 0, refused with HTTP 409 when insufficient), and *Adjustment* sets the level to a physically counted total (≥ 0). Stock Out uses a guarded SQL UPDATE (`WHERE current_quantity >= quantity`), so two simultaneous removals can never oversell the same stock — atomic at the database level. Every movement writes a history row snapshotting the balance afterwards. PUT updates descriptive fields only and never touches quantities. Low stock means `current_quantity <= minimum_stock` (so out-of-stock is always flagged). A non-zero opening stock at creation automatically writes the first "Opening stock" movement.

Purchase data model (Phase 10): `Purchase 1:N PurchaseItem` (`purchase_items.purchase_id`, cascade). The purchase number (`PUR-0001`, derived from the primary key) identifies it on screens; `supplier_name`, `item_name` and `unit` are snapshotted so history stays readable after renames or deletions (`purchases.supplier_id` and `purchase_items.inventory_item_id` are both `ON DELETE SET NULL`). Money formula — calculated exclusively server-side: `line_total = quantity × unit_cost` on rounded inputs; `subtotal = total = Σ line totals`. Recording a purchase is ONE logical database operation: header, lines, a guarded SQL quantity increase per material and one "Stock In" movement row per line all commit together, so a failed purchase never leaves stock half-updated. Purchases are record-only ledger entries — no edit or delete — which keeps the audit trail intact.

Employee/Salary data model (Phases 11–12): `Employee 1:N Salary` (`salaries.employee_id`, `ON DELETE RESTRICT`). `base_salary` on the employee is only a reference value interpreted by `salary_type` (Monthly/Daily/Hourly); each `Salary` row snapshots the base salary actually used and stores a server-calculated `net_salary = base + bonus − deduction` so later edits to an employee never rewrite history. The pair `(employee_id, salary_month)` is UNIQUE — one record per employee per month, duplicates rejected with HTTP 409. An employee who still has salary records cannot be deleted (HTTP 409) so payment history used by reports can never disappear.

Expense data model (Phase 13): `Expense` is a **standalone** entity — a dated money outflow with no foreign keys. `category` is restricted to the cafe's configured list (Electricity, Gas, Rent, Maintenance, Cleaning, Internet, Miscellaneous) and `payment_method` to Cash/UPI/Card/Other; `amount` must be > 0 and rounded to 2 decimals. Title may repeat (two electricity bills are allowed) and any expense can always be deleted without breaking other records.

Reports (Phase 14) introduce **no new tables** — `report_service` recomputes every figure live from recorded data (pure read-only aggregations). Sales are defined as the total of *paid* orders; the estimated profit summary (`Sales − Purchases − Salaries − Expenses`) is explicitly labelled an estimate because salaries are matched by month, not by an exact day.

## Chapter 5 — I/O Screens

Screens implemented in Phase 1 (screenshots to be captured for final submission):

| Screen                | Route            | Notes                                              |
| --------------------- | ---------------- | -------------------------------------------------- |
| Dashboard shell       | `/`              | Sidebar, top bar, status chips, placeholder stats  |
| Menu Management       | `/menu`          | **Implemented (Phases 3–4)** — category + item tables, modals, filters, image thumbs |
| Customer Menu (share) | `/customer-menu` | **Implemented (Phase 5)** — copyable public link, live stats, privacy notes |
| Public digital menu   | `/menu/cafe`     | **Implemented (Phase 5)** — customer-facing, mobile-first, no admin UI |
| Orders                | `/orders`        | **Implemented (Phase 6)** — order table with filters, new-order modal (type/table/cart/live totals), detail modal, status workflow |
| Billing               | `/billing`       | **Implemented (Phase 7)** — collection stat cards, bills table, payment recording, printable receipt |
| Suppliers             | `/suppliers`     | **Implemented (Phase 8)** — supplier table with search, contact details, material counts, add/edit/delete modal |
| Inventory             | `/inventory`     | **Implemented (Phase 9)** — stat cards, materials table with stock/min/cost/supplier/low-stock badges, filters, stock movement + history modals, recent movements feed |
| Purchases             | `/purchases`     | **Implemented (Phase 10)** — stat cards (total purchased / outstanding / count), purchases table with search + supplier/payment/date filters, new-purchase modal with material picker and live totals, detail modal, mark paid/unpaid |
| Employees             | `/employees`     | **Implemented (Phase 11)** — employee table with search/role filters and an active toggle, add/edit/delete modal, live salary-count column |
| Salaries              | `/salaries`      | **Implemented (Phase 12)** — stat cards (records shown / total paid / unpaid), salary-history table with employee/month/status filters, add/edit modal with live net preview |
| Expenses              | `/expenses`      | **Implemented (Phase 13)** — stat cards, expense-history table with search + category/method/date filters, add/edit modal |
| Reports               | `/reports`       | **Implemented (Phase 14)** — seven report tabs with date filters, mode dropdowns, summary cards, a plain-JS sales bar chart and a Print button |
| Settings              | `/settings`      | **Implemented (Phase 2)** — two-card form: cafe profile + billing/receipt, logo preview, loading skeleton, inline validation, save/discard actions |

### Orders Screen Behaviour (Phase 6)

The orders page (`/orders`, `data-page="orders"`) shows every order newest first with columns for number, type (dine-in rows carry a table chip), item count, total, status badge, payment badge and placed time. Toolbar: debounced search by order number plus status, type and payment filters.

**New order modal** — a segmented Dine-in/Takeaway toggle shows the table-number field only for dine-in; an item picker lists available dishes with prices (sold-out items hidden) and an add button merges duplicates into one line; the cart supports quantity steppers and removal; a dark totals box recalculates subtotal/discount/tax/grand-total live as lines or the discount change. Client validation mirrors the server: table required for dine-in (1–999), quantity integers 1–999, discount ≥ 0 and never above the subtotal. The client totals are UX only — the server recalculates everything on POST.

**Status workflow** — row actions offer View / Cancel / Delete; Cancel is hidden for completed and cancelled orders, Delete appears only for cancelled ones. The detail modal renders meta info, item lines and the money breakdown read-only plus a status dropdown (Pending → Preparing → Ready → Completed). Server rules: cancelled orders are frozen, paid orders cannot be cancelled.

### Billing Screen Behaviour (Phase 7)

The billing page (`/billing`) opens with three stat cards — Billed, Collected and Outstanding — computed server-side from `GET /api/bills` summary over the filtered result set. The bills table adds money columns (subtotal, discount, tax with its rate, grand total), payment method and status badges per row.

**Payments** — "Mark paid" opens a modal with four method buttons (Cash / UPI / Card / Other); choosing one calls `POST /api/bills/{id}/pay`. Paid bills can never be double-charged (409) and cancelled orders refuse payment.

**Printable receipt** — "Receipt" fetches bill detail including cafe branding (name, address, phone, currency, footer from Settings) and renders a thermal-style paper slip: header, dashed separators, line items with quantity × price, tax/discount/total block and footer message. "Print receipt" triggers the browser print dialog; print CSS hides everything except the paper and constrains it to 80 mm for receipt printers.

### Suppliers Screen Behaviour (Phase 8)

The suppliers page (`/suppliers`) lists every supplier alphabetically with contact person + phone, materials supplied, a live count of linked raw materials and an Active/Inactive badge. Toolbar: debounced server-side search across name, contact person, materials and phone, plus a "Show inactive" toggle.

"+ Add supplier" / "Edit" open one modal form — name (required, ≤100, unique ignoring case), contact person, 10-digit mobile with pattern validation, email with format validation, address, comma-separated materials list and an Active checkbox. Duplicates are pre-checked client-side against the loaded list and enforced by the server with HTTP 409. Delete asks for confirmation and explains the behaviour: linked raw materials simply lose the supplier link while their stock and history stay intact.

### Inventory Screen Behaviour (Phase 9)

The inventory page (`/inventory`) opens with three stat cards — Raw materials, Low stock items and Active suppliers — computed from `GET /api/inventory/items`' summary block.

**Raw materials table** shows each material with its category, current quantity in its unit, minimum stock, purchase cost per unit, preferred supplier and status badges ("Low stock"/"Out of stock" plus Active/Inactive). Toolbar filters: debounced search, category dropdown (fed from `/api/inventory/categories`), supplier dropdown and a "Low stock only" toggle.

**Add/Edit material modal** — name (required, unique), free-text category with datalist suggestions (Dairy, Vegetables, Beverages…), unit select (Kg/Gram/Litre/Millilitre/Piece/Packet/Box), opening stock (create only; saved as the first "Opening stock" movement), minimum stock (≥0) that drives the warning, purchase price per unit (≥0), supplier select, notes. Editing never changes the stock level — quantities move only through movements.

**Stock movement modal** ("Stock" row action) — segmented Stock In / Stock Out / Adjustment buttons switch the quantity label and rules live: In/Out demand > 0; Adjustment takes the counted new total (0 allowed). The header shows the current balance vs minimum. A failed Stock Out (insufficient stock) surfaces the server's 409 message and changes nothing.

**Movement history** — per-material history via the "History" action (type, quantity, balance after, note) and a global "Recent stock movements" section listing the latest 25 movements across all materials with type filter, colour-coded ±/= amounts and refresh button.

### Purchases Screen Behaviour (Phase 10)

The purchases page (`/purchases`) opens with three stat cards — Total purchased, Outstanding (unpaid) and Purchases recorded — computed server-side from `GET /api/purchases`' summary block over the filtered result set.

**Purchases table** shows each purchase newest first: number (`PUR-xxxx`), supplier name, purchase date, item count, total and a Paid/Unpaid badge. Row actions: View (detail modal) and Mark paid / Mark unpaid (toggle via `PUT .../payment-status`). Toolbar filters: debounced search across purchase number and supplier name, supplier dropdown, payment-status dropdown and from/to date inputs — all applied server-side.

**New purchase modal** — supplier select (required), date input defaulting to today, and a material picker fed from active raw materials: choosing a material pre-fills its purchase price as the unit cost; quantity and cost inputs are validated client-side (> 0 and ≥ 0). Added lines appear in an editable cart whose per-line amounts and grand total recalculate live (client totals are UX only — the server recalculates everything on POST). Notes are optional. Submitting calls `POST /api/purchases`; the success toast reports the generated number and that inventory was updated. Duplicate materials are refused in the picker ("adjust its quantity below"), mirroring the server's rule.

**Detail modal** — read-only meta list (supplier, date, payment badge, recorded time, notes) plus the material lines (quantity × unit cost = amount) and the total added to inventory.

### Expenses Screen Behaviour (Phase 13)

The expenses page (`/expenses`) opens with three stat cards — Expenses, Total spent and Categories used — computed from `GET /api/expenses`' `summary` block over the filtered result set.

**Expense history table** lists every expense newest first (by date, then id): title, category badge, formatted amount, paid-on date, payment method and notes, with Edit and Delete row actions. Toolbar filters: debounced search across title and notes, category dropdown, payment-method dropdown and from/to date inputs — all applied server-side. "Clear filters" resets the toolbar and reloads.

**Add/Edit modal** — title (required, ≤120; duplicates are allowed deliberately), category select fed from the category allowlist, amount (>0, decimal), date input (defaults to today), payment-method select (defaults Cash) and optional notes (≤255). Client validation mirrors the server: `required`, `maxLength` and `positiveNumber` rules from `validation.js`; per-field server errors are mapped back onto the form. Delete uses a confirm dialog and is always allowed (an expense carries no foreign keys). The choices for the category and method dropdowns are fetched from `GET /api/expenses/options` so the UI never hard-codes them.

### Reports Screen Behaviour (Phase 14)

The reports page (`/reports`) is a read-only dashboard: it displays data and never edits anything. A filter bar sits above a row of seven tabs — **Sales, Orders, Inventory, Purchases, Salaries, Expenses, Profit** — each with its own report section that is shown/hidden client-side.

* **Filter bar** — From/To date inputs, a mode dropdown whose options change per tab, Apply filters, Reset dates and a Print button. Only the active tab's data is fetched, on tab switch or filter apply.
* **Sales** — Daily/Weekly/Monthly mode dropdown; summary cards (Sales total, Paid orders, Average order), a bar chart rendered in plain JavaScript on a `<canvas>` and a period/orders/sales table.
* **Orders** — no mode select; summary cards plus two side-by-side tables: orders by status and by date.
* **Inventory** — mode dropdown (Current stock / Low stock only / Stock movements); summary cards (Active materials, Low stock, Stock value); the current/low tables show stock with a low-stock badge, while the movements view swaps table columns to type, quantity, balance, note and time.
* **Purchases** — mode dropdown (By date / By supplier); records and total summary plus a grouped table.
* **Salaries** — no mode select; summary cards (Records, Total paid) plus a month/records/total table, newest month first.
* **Expenses** — mode dropdown (By category / By date); records and total summary plus the grouped table.
* **Profit** — the Estimated Profit summary (Sales − Purchases − Salaries − Expenses) rendered as a four-cell grid with an amber note that salary matching is by month, so the figure is an approximation, not an exact ledger balance.
* **Print** — window.print(); print CSS hides the sidebar, top bar, filters and tabs and renders the active report section with visible table borders for paper.

Loading skeleton rows and a "Could not load report" error state cover each tab; empty ranges show an empty-state row instead of a table.

### Customer Digital Menu Behaviour (Phase 5)

Public page at `/menu/cafe`, shareable from the admin `/customer-menu` page:

* **Branding from settings** — cafe name, logo (with monogram fallback), address and tap-to-call phone; page title and Open-Graph tags update for nice link previews
* **Mobile-first layout** — single column on phones, two-column section grid on wide screens; sticky horizontally-scrollable category chip bar
* **Menu content** — active categories with at least one item; each item shows image (or cup fallback), name with veg/non-veg square-dot marker, description, price in the cafe's currency using dotted bistro-style price leaders
* **Popular indicator** — "★ Popular" tag; **availability** — sold-out items stay visible but greyed with a "Sold out" tag
* **Search/filter** — debounced client-side search across names and descriptions with a results count; category chips filter sections
* **States** — skeleton loading, friendly empty state ("Menu coming soon") when nothing is published, error state with retry
* **No admin surface** — the page never loads `common.js`; no sidebar, edit/delete controls or internal database fields are served to customers

### Settings Screen Behaviour (Phase 2)

* Loads saved values from `GET /api/settings`; fields are disabled with a skeleton loader until data arrives
* Client-side validation (`static/js/validation.js`): required name/currency/tax, phone pattern, email pattern, max lengths, tax range 0–100
* Server-side validation mirrors the same rules via Pydantic and returns per-field errors which the page maps back onto the form
* Success/error toasts; "Discard changes" reloads saved values; live logo preview with fallback
* Responsive two-column layout collapsing to one column under 900px

### Menu Management Screen Behaviour (Phases 3–4)

Two sections on one page (`/menu`, `data-page="menu"`):

**Categories** — table of name, description, live item count and an Active/Inactive badge. Toolbar search (debounced, server-side `?search=`) plus a "Show inactive" toggle (`include_inactive=false`). "+ Add category" opens a modal form (name required ≤80, description optional ≤255, active checkbox). Duplicate names are pre-checked client-side against the loaded list (case-insensitive) and enforced by the server with HTTP 409.

**Menu items** — table with image thumbnail (fallback icon on error), name with Veg/Non-veg and Popular ★ badges, category, formatted price and Available/Sold-out status. Toolbar: debounced search, category dropdown filter and availability filter. The item modal offers category select (inactive categories suffixed), name, price (>0), description, image URL with live preview, and Vegetarian/Popular/Available checkboxes.

Shared behaviour: skeleton loading rows, empty states that distinguish "no data" from "no match for filters", confirm dialogs before deletes (with the entity name HTML-escaped), toasts for every outcome, inline mapping of per-field server errors back onto form inputs, Escape/overlay-click closes modals, and creating/deleting a category refreshes the items section via a `categories:changed` DOM event so counts stay accurate.

UI notes: espresso-and-paper theme, Fraunces/Inter typography, grouped navigation (Overview / Sales / Stock & Supply / People / Money & Insight / System), toast notifications, confirm dialogs, empty states, responsive sidebar collapsing under 1024px.

## Chapter 6 — Reports

The Reports module (Phase 14) provides pre-built, read-only reports. Every figure is recomputed live from the recorded database — nothing is stored on the reports side — so the totals always match the underlying orders, purchases, salaries and expenses. Sales means the total of **paid** orders (collected revenue).

| Report             | Grouping / mode                                  | Shows                                                    |
| ------------------ | ------------------------------------------------ | -------------------------------------------------------- |
| Sales              | Daily / Weekly / Monthly                         | Sales total, order count, average order per period; a bar chart and table (daily = last 14 days, weekly = rolling last 7 days, monthly = per `YYYY-MM`) |
| Orders             | By status and by date (date-filtered)            | Order count and total per status (Pending → Preparing → Ready → Completed → Cancelled) and per day |
| Inventory          | Current stock / Low stock only / Stock movements | Active materials with stock, minimum, cost and value; items at or below minimum; the latest 300 stock movements |
| Purchases          | By supplier / By date (date-filtered)            | Purchase count and total per supplier or per day          |
| Salaries           | By month (whole history)                         | Net salary paid per month and overall total               |
| Expenses           | By category / By date (date-filtered)            | Expense count and total per category (highest first) or per day |
| Profit             | Date-filterable                                  | Estimated Profit summary: Sales − Purchases − Salaries − Expenses, with each component shown |

**Estimated Profit** is explicitly labelled an *estimated* management summary, not an exact ledger balance: salaries are keyed by month (`YYYY-MM`), so they are matched by the months covered by the selected date range rather than by an exact day. Purchases and expenses are matched on their recorded dates.

Reports are served by the seven `GET /api/reports/*` endpoints (period and mode choices are pattern-validated with HTTP 422 on bad values) and rendered on the `/reports` page described in Chapter 5. The dashboard (Phase 15) will reuse these same read-only aggregations.

## Chapter 7 — Coding

### Technology

* Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2
* SQLite via `data/cafe.db`
* HTML/CSS/Vanilla JS frontend; uv as package manager

### Key Files

| File                              | Responsibility                                          |
| --------------------------------- | ------------------------------------------------------- |
| `app/main.py`                     | App factory, lifespan init, page routes, error handlers |
| `app/core/config.py`              | Paths, app name/version, database URL                   |
| `app/core/database.py`            | Engine, SessionLocal, Base, get_db(), init_db()         |
| `app/models/cafe_setting.py`      | CafeSetting model (singleton row)                       |
| `app/models/category.py`          | Category model + 1:N items relationship                 |
| `app/models/menu_item.py`         | MenuItem model (FK to categories, per-category unique)  |
| `app/models/order.py`             | Order + OrderItem models (bill fields, snapshots, cascades) |
| `app/models/supplier.py`          | Supplier model (unique name, inventory link)            |
| `app/models/inventory.py`         | InventoryItem + InventoryTransaction (movements, history) |
| `app/models/purchase.py`          | Purchase + PurchaseItem models (totals, snapshots, cascades) |
| `app/schemas/cafe_setting.py`     | Pydantic request/response schemas + validation          |
| `app/schemas/category.py`         | Category create/update/read schemas                     |
| `app/schemas/menu_item.py`        | Menu item schemas; price > 0, rounding, trims           |
| `app/schemas/order.py`            | Order create/status/payment/read schemas; qty & discount rules |
| `app/schemas/supplier.py`         | Supplier schemas; phone/email pattern validation        |
| `app/schemas/inventory.py`        | Material/movement schemas; unit enum, ≥0 rules, type-conditional qty |
| `app/schemas/purchase.py`         | Purchase schemas; qty > 0, cost ≥ 0, no duplicate lines |
| `app/services/settings_service.py`| Get-or-create singleton, update logic                   |
| `app/services/category_service.py`| Category CRUD, duplicate check, delete guard            |
| `app/services/menu_item_service.py`| Item CRUD, FK validation, per-category duplicate check |
| `app/services/order_service.py`   | Order creation with server totals, status workflow, delete guard |
| `app/services/billing_service.py` | Bill list + summary totals, payment recording           |
| `app/services/supplier_service.py`| Supplier CRUD, duplicate check, material counts         |
| `app/services/inventory_service.py`| Material CRUD, atomic stock movements, history, summary |
| `app/services/purchase_service.py`| Purchase recording with atomic stock update, filters, summary |
| `app/routers/settings.py`         | GET/PUT /api/settings                                   |
| `app/routers/categories.py`       | CRUD /api/categories (+search, include_inactive)        |
| `app/routers/menu.py`             | CRUD /api/menu/items (+filters)                         |
| `app/routers/orders.py`           | Orders API: list/create/detail/status/delete            |
| `app/routers/billing.py`          | Bills API: list/detail/pay                              |
| `app/routers/suppliers.py`        | Suppliers API: CRUD + search                            |
| `app/routers/inventory.py`        | Inventory API: items CRUD, /stock movements, history    |
| `app/routers/purchases.py`        | Purchases API: record/list/detail/payment-status        |
| `app/models/employee.py`          | Employee model + 1:N salaries relationship              |
| `app/models/salary.py`            | Salary model (UNIQUE employee/month, server net snapshot) |
| `app/models/expense.py`           | Expense model + EXPENSE_CATEGORIES / PAYMENT_METHODS constants |
| `app/schemas/employee.py`         | Employee schemas; mobile/email/role/date validation     |
| `app/schemas/salary.py`           | Salary schemas; YYYY-MM month, net ≥ 0 rule             |
| `app/schemas/expense.py`          | Expense schemas; category/method allowlists, amount > 0 |
| `app/services/employee_service.py`| Employee CRUD, live salary counts, delete guard (409)   |
| `app/services/salary_service.py`  | Salary CRUD, net calculation, duplicate-month guard (409) |
| `app/services/expense_service.py` | Expense CRUD, filters, summary totals                   |
| `app/services/report_service.py`  | Read-only report aggregations (all seven views)         |
| `app/routers/employees.py`        | Employees API: CRUD + search/role filters               |
| `app/routers/salaries.py`         | Salaries API: CRUD + employee/month/status filters      |
| `app/routers/expenses.py`         | Expenses API: CRUD, /options, filters                   |
| `app/routers/reports.py`          | Reports API: seven GET endpoints, validated modes       |
| `static/js/employees.js`          | Employees table, search/role filters, add/edit modal    |
| `static/js/salaries.js`           | Salary history + filters + live net preview             |
| `static/js/expenses.js`           | Expense history + filters + add/edit modal              |
| `static/js/reports.js`            | Report tabs, plain-JS bar chart, print                  |
| `static/css/expenses.css`         | Expenses page extras (date inputs, search width)        |
| `static/css/reports.css`          | Report tabs, summary cards, chart, profit grid, print CSS |
| `static/js/api.js`                | Fetch wrapper with ApiError                             |
| `static/js/common.js`             | Shell injection, navigation, toasts, confirm dialogs    |
| `static/js/validation.js`         | Reusable form validators                                |
| `static/js/categories.js`         | Categories table + modal logic                          |
| `static/js/menu-items.js`         | Items table, filters + modal logic                      |
| `static/css/menu.css`             | Menu page styles (toolbar, thumbs, badges, modal-lg)    |
| `static/js/settings.js`           | Settings form load/save/validation                      |
| `app/schemas/public_menu.py`      | Public display-only response schemas                    |
| `app/services/public_menu_service.py` | Composes branding + active categories/items         |
| `app/routers/public_menu.py`      | GET /api/public/menu (public feed)                      |
| `static/js/customer-menu.js`      | Share page: link copy + live stats                      |
| `static/js/public-menu.js`        | Public menu rendering, search, states                   |
| `static/css/public-menu.css`      | Standalone customer-menu theme                          |
| `static/js/orders.js`             | New-order modal, cart with live totals, status workflow |
| `static/js/billing.js`            | Bills table, stat cards, payment modal, receipt render  |
| `static/css/orders.css`           | Orders & Billing styles incl. printable receipt CSS     |
| `static/js/suppliers.js`          | Suppliers table, search, add/edit modal                 |
| `static/js/inventory.js`          | Materials table + filters, stock movement & history modals |
| `static/css/inventory.css`        | Inventory stat cards, movement badges, segmented control|
| `static/js/purchases.js`          | Purchase table + filters, material cart with live totals |
| `static/css/purchases.css`        | Purchases page extras (picker cost field, date inputs)  |
| `tests/`                          | pytest suite (startup, database, settings, categories, menu items, public menu, orders, billing, suppliers, inventory, purchases, employees, salaries, expenses, reports) |

### Error Envelope

All API errors return `{ "success": false, "message": ..., "errors": [...] }`; validation failures use HTTP 422 with per-field messages.

## Chapter 8 — Software System Testing

Automated tests (`uv run pytest`) — **358 collected on 2026-08-29**: startup 19, database 5, settings 15, categories 22, menu items 32, public menu 9, orders 37, billing 19, suppliers 27, inventory 42, purchases 21, employees 35, salaries 31, expenses 27, reports 17. On this machine the run completed as **357 passed, 1 blocked**; the single failure (`test_init_db_creates_database_file`) is an environmental Windows file-lock — a running cafe-server process holds `data/cafe.db`, so the test that unlinks the database file cannot obtain exclusive access. It passes in isolation when no server holds the database.

| Test Case                          | Input                    | Expected Result                     | Status |
| ---------------------------------- | ------------------------ | ----------------------------------- | ------ |
| Health endpoint                    | GET /api/health          | 200, status ok, database connected  | Pass   |
| Every page route loads             | GET each of 13 routes    | 200 text/html                       | Pass   |
| Unknown API route                  | GET /api/nope            | 404 JSON error envelope             | Pass   |
| Static assets served               | GET css/js/favicon       | 200 correct content type            | Pass   |
| Database file created at startup   | lifespan init_db()       | data/cafe.db exists                 | Pass   |
| Session executes query             | SELECT 1 via session     | Returns 1                           | Pass   |
| Implemented tables registered      | Base.metadata            | cafe_settings, categories, menu_items, orders, order_items, suppliers, inventory_items, inventory_transactions, purchases, purchase_items, employees, salaries, expenses present | Pass |
| No unexpected domain tables        | Base.metadata            | payments / invoices / recipes / pytorch_models absent       | Pass |

### Settings Module Test Cases (Phase 2)

| Test Case                        | Input                                  | Expected Result                       | Status |
| -------------------------------- | -------------------------------------- | ------------------------------------- | ------ |
| Read settings (first run)        | GET /api/settings                      | 200, defaults created, envelope ok    | Pass   |
| Valid full update                | All fields with correct values         | 200, values echoed and saved          | Pass   |
| Whitespace trimming              | `"  Spaced Cafe  "`, empty optionals   | Trimmed; empty optionals stored NULL  | Pass   |
| Blank cafe name                  | `cafe_name: "   "`                     | 422 with field error                  | Pass   |
| Missing cafe name                | Field absent                           | 422 with field error                  | Pass   |
| Name over 100 chars              | 101 characters                         | 422 with field error                  | Pass   |
| Negative tax                     | `tax_percent: -1`                      | 422 with field error                  | Pass   |
| Tax above 100                    | `tax_percent: 100.5`                   | 422 with field error                  | Pass   |
| Invalid phone                    | `"12345"`                              | 422, "valid 10-digit mobile" message  | Pass   |
| Invalid email                    | `"not-an-email"`                       | 422, email format message             | Pass   |
| Empty currency                   | `currency: ""`                         | 422 with field error                  | Pass   |
| Footer over 200 chars            | 201 characters                         | 422 with field error                  | Pass   |
| Failed update keeps old data     | Invalid PUT after valid PUT            | Saved values unchanged                | Pass   |
| Persistence across restart       | PUT → dispose engine/new client        | Values still returned after restart   | Pass   |

### Categories Module Test Cases (Phase 3)

Tests use a unique per-run name tag, so reruns never collide with leftover data.

| Test Case                        | Input                                  | Expected Result                       | Status |
| -------------------------------- | -------------------------------------- | ------------------------------------- | ------ |
| Create with valid data           | name/description/is_active             | 201, row echoed, item_count 0         | Pass   |
| Whitespace trimmed               | `"  Snacks  "`                         | Stored as "Snacks"                    | Pass   |
| Empty description becomes null   | `description: "   "`                   | Stored NULL                           | Pass   |
| Get single / list sorted         | GET by id, GET list                    | 200; list alphabetical with counts    | Pass   |
| Full update (PUT)                | New values incl. is_active false       | 200 updated values returned           | Pass   |
| Search matches description       | `?search=bakery`                       | Matching category returned            | Pass   |
| Search matches name              | Tagged partial name                    | Matching category returned            | Pass   |
| Hide inactive filter             | include_inactive=false                 | Inactive rows hidden                  | Pass   |
| Blank/missing/81-char name       | Invalid payloads (parametrised)        | 422 with field errors                 | Pass   |
| Description over 255 chars       | 256 characters                         | 422 with field errors                 | Pass   |
| Bad flag type                    | `is_active: "yes-please"`              | 422 with field errors                 | Pass   |
| Duplicate name exact/case        | Same and different case                | 409 both times                        | Pass   |
| Update keeps own name            | PUT same name to self                  | 200 allowed                           | Pass   |
| Failed create leaves count       | Duplicate POST after valid ones        | List count unchanged                  | Pass   |
| Delete empty category            | DELETE then GET                        | 200 then 404                          | Pass   |
| Recreate after delete            | POST same name again                   | 201                                   | Pass   |
| Missing id get/update/delete     | id 999999                              | 404 envelope each time                | Pass   |

### Menu Items Module Test Cases (Phase 4)

| Test Case                        | Input                                  | Expected Result                       | Status |
| -------------------------------- | -------------------------------------- | -------------------------------------- | ------ |
| Create with valid data           | All fields                             | 201, nested category summary present  | Pass   |
| Defaults applied                 | Only category/name/price               | veg=true, popular=false, available=true | Pass |
| Price rounded                    | price 99.999                           | Stored 100.0                          | Pass   |
| Full update (PUT)                | New name/price/flags                   | 200 updated values returned           | Pass   |
| Move to another category         | PUT with new category_id               | 200, new category echoed              | Pass   |
| Same name in second category     | Identical names, different categories  | 201 both                              | Pass   |
| Search name/description          | ?search=…                              | Matching items only                   | Pass   |
| Category filter                  | ?category_id=…                         | Only that category's items            | Pass   |
| Availability filter              | available_only=true                    | No sold-out items in result           | Pass   |
| Unknown category                 | category_id 999999                     | 404 "Create it first" message         | Pass   |
| Missing/zero/negative/non-int id | Parametrised invalid category ids      | 422 with field errors                 | Pass   |
| Blank/missing/121-char name      | Parametrised invalid names             | 422 with field errors                 | Pass   |
| Zero/negative/text price         | price 0, -50, "expensive"              | 422 with field errors                 | Pass   |
| Overlong description/image URL   | 501 / 301 characters                   | 422 with field errors                 | Pass   |
| Duplicate in same category       | Exact and upper-case name              | 409 both times                        | Pass   |
| Duplicate check excludes self    | PUT unchanged name                     | 200 allowed                           | Pass   |
| Delete then get                  | DELETE then GET                        | 200 then 404                          | Pass   |
| Failed duplicate leaves count    | Duplicate POST                         | List count unchanged                  | Pass   |
| Row persisted in SQLite          | Direct session query after API create  | Row found with correct values         | Pass   |
| Referential integrity            | Items without valid category           | None exist (FK pragma + ORM cascade)  | Pass   |

Manual verification (live uvicorn): server started against a temporary SQLite file; initial GET created defaults; valid PUT saved; server process was killed and restarted; GET returned the saved values — persistence across a real application restart confirmed. An invalid PUT (tax 150) returned HTTP 422.

UI testing (manual): settings form loads with skeleton then populated fields; inline errors appear for invalid phone/email/tax; success toast on save; discard reloads saved values; layout collapses to a single column under 900px viewport width.

### Customer Digital Menu Test Cases (Phase 5)

| Test Case                          | Input                                   | Expected Result                                    | Status |
| ---------------------------------- | --------------------------------------- | -------------------------------------------------- | ------ |
| Public page served                 | GET /menu/cafe                          | 200 HTML with public assets only                   | Pass   |
| No admin shell for customers       | Page source inspection                  | No `common.js`, no `data-page` admin markers       | Pass   |
| Public feed envelope               | GET /api/public/menu                    | 200, `{cafe, categories}` shape                    | Pass   |
| Branding from settings             | PUT settings then GET feed              | Name/address/phone/logo/currency echoed            | Pass   |
| Inactive category hidden           | Category with `is_active: false`        | Section absent from feed                           | Pass   |
| Empty category hidden              | Active category with zero items         | Section absent from feed                           | Pass   |
| Sold-out item stays visible        | Item with `is_available: false`         | Present in feed, flagged, price intact             | Pass   |
| Popular/veg flags pass through     | Popular veg item                        | Flags true in feed                                 | Pass   |
| No internal fields exposed         | Inspect feed JSON                       | Only display keys; no ids/timestamps               | Pass   |
| Alphabetical ordering              | Multiple categories/items               | Sections and items sorted case-insensitively       | Pass   |

Live smoke test (uvicorn on a free port): `/menu/cafe` returned 200 and served `public-menu.js`/`public-menu.css`; the page HTML contained no admin shell references; `/api/public/menu` returned the success envelope. Against a database without published items the feed correctly reports zero sections, which triggers the page's "Menu coming soon" empty state; section/item payloads and flags are verified by the automated tests above.

### Orders Module Test Cases (Phase 6)

Tests run against known settings (tax 5%) and a private category with ₹100/₹50 items; the original settings are restored afterwards.

| Test Case                          | Input                                    | Expected Result                              | Status |
| ---------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Create dine-in order               | 2×₹100 + 1×₹50, ₹10 discount             | 201; subtotal 250, tax 12, total 252 (server-calculated) | Pass |
| Order number auto-generated        | POST order                               | `ORD-xxxx` matching pattern                  | Pass   |
| Takeaway without table             | order_type Takeaway                      | 201, table_number null                       | Pass   |
| Takeaway ignores table number      | table_number sent with takeaway          | Forced to null                               | Pass   |
| Dine-in without table              | table_number absent                      | 422 "Table number is required"               | Pass   |
| Invalid order type                 | "Delivery"                               | 422                                          | Pass   |
| Money rounding                     | 3 × ₹19.99 with 5% tax                   | subtotal 59.97, tax 3.0, total 62.97         | Pass   |
| Empty/missing/zero-id item lines   | Parametrised invalid item lists          | 422 with field errors                        | Pass   |
| Invalid quantities                 | 0, −2, 1.5, "two", true, 1000            | 422 each                                     | Pass   |
| Unknown menu item                  | menu_item_id 999999                      | 404 "not found" message                      | Pass   |
| Unavailable dish ordered           | Sold-out item                            | 409 "currently marked unavailable"           | Pass   |
| Duplicate lines for one dish       | Same id twice                            | 422 (raise quantity instead)                 | Pass   |
| Invalid discounts                  | −5, "free", true                         | 422 each                                     | Pass   |
| Discount above subtotal            | ₹51 discount on ₹50 subtotal             | 400 "cannot be greater than the order subtotal" | Pass |
| Zero discount allowed              | discount_amount 0                        | 201, stored 0.0                              | Pass   |
| Full status lifecycle              | Pending → Preparing → Ready → Completed  | 200 at each step with message                | Pass   |
| Invalid status values              | "Cooking", "", "pending"                 | 422 each                                     | Pass   |
| Cancelled orders frozen            | Reopen attempt after cancel              | 409 "Cancelled orders cannot be changed"     | Pass   |
| Delete guard                       | DELETE active order                      | 409 until cancelled, then 200 then 404       | Pass   |
| List newest first with counts      | GET /api/orders                          | item_count ≥ 1 on created rows               | Pass   |
| Filters status/type/payment        | Query params                             | Only matching rows returned                  | Pass   |
| Search by number fragment          | Last 4 digits of ORD-xxxx                | Target found                                 | Pass   |
| Detail includes snapshot lines     | GET /api/orders/{id}                     | item_name/unit_price/line_total present      | Pass   |
| Missing order 404s                 | GET/PUT-status/DELETE id 999999          | Error envelope each time                     | Pass   |
| Failed create changes nothing      | POST empty items                         | List count unchanged                         | Pass   |
| Persistence in SQLite              | Direct session query                     | Row + items stored with exact totals         | Pass   |

### Billing Module Test Cases (Phase 7)

Runs against tax 10% with a ₹150 item for hand-checkable maths.

| Test Case                          | Input                                    | Expected Result                              | Status |
| ---------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Pay with every method              | Cash / UPI / Card / Other                | 200; Paid + method echoed                    | Pass   |
| paid_at stamped                    | POST pay                                 | Timestamp not null                           | Pass   |
| Double payment blocked             | Second POST pay                          | 409 "already paid"                           | Pass   |
| Cancelled bill cannot be paid      | Pay after cancel                         | 409 "cancelled"                              | Pass   |
| Unknown bill payment               | id 999999                                | 404 envelope                                 | Pass   |
| Invalid methods                    | "Bitcoin", "", "cash"                    | 422 each                                     | Pass   |
| Paid order cannot be cancelled     | PUT status Cancelled after pay           | 409 message mentioning refund policy         | Pass   |
| Tax & discount maths               | ₹300 − ₹30 discount @ 10%                | tax 27.0, total 297.0                        | Pass   |
| Server-calculated discounted total | ₹150 − ₹25 takeaway                      | total 137.5                                  | Pass   |
| Summary totals consistent          | GET /api/bills                           | billed = Σ totals; collected/outstanding correct | Pass |
| Payment filters                    | payment_status / payment_method          | Only matching bills returned                 | Pass   |
| Search by bill number              | Number fragment                          | Target bill found                            | Pass   |
| Receipt branding block             | GET /api/bills/{id}                      | cafe name/currency/footer from settings      | Pass   |
| Missing bill detail                | GET /api/bills/999999                    | 404 success=false envelope                   | Pass   |

Live smoke test (uvicorn against a temporary SQLite file): `/orders` and `/billing` pages served their full markup; an order placed through the API returned `ORD-0001` with subtotal 240, tax 11.5, total 241.5 (2×₹120 − ₹10 @ 5%); payment via UPI set Paid with a timestamp; the bill detail carried the receipt branding block; the summary cards matched billed=collected=241.5, outstanding=0; quantity 0 was rejected over the wire.

UI testing (manual): new-order modal shows/hides the table field with the type toggle, merges duplicate dishes into one line, live totals track cart and discount changes; billing stat cards update with filters; the receipt modal renders the paper slip and print CSS isolates it during printing.

### Suppliers Module Test Cases (Phase 8)

Tests use a unique per-run name tag, so reruns never collide with leftover data.

| Test Case                          | Input                                    | Expected Result                              | Status |
| ---------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Create with valid data             | All supplier fields                      | 201, row echoed, inventory_item_count 0      | Pass   |
| Whitespace trimmed, empties null   | Padded/blank optional fields             | Trimmed; blanks stored NULL                  | Pass   |
| Email lowercased                   | `BIG123@Vendor.IN`                       | Stored lowercase                             | Pass   |
| Get single / list sorted           | GET by id, GET list                      | 200; alphabetical with material counts       | Pass   |
| Full update (PUT)                  | New values incl. is_active false         | 200 updated values returned                  | Pass   |
| Search by name/contact/materials   | Partial terms                            | Matching suppliers returned                  | Pass   |
| Hide inactive filter               | include_inactive=false                   | Inactive rows hidden                         | Pass   |
| Invalid payloads (parametrised)    | Blank/101-char name, bad phone/email, bool flag, overlong fields | 422 with field errors each | Pass |
| Duplicate name exact/case          | Same and different case                  | 409 both times                               | Pass   |
| Update keeps own name              | PUT unchanged name to self               | 200 allowed                                  | Pass   |
| Delete then get                    | DELETE then GET                          | 200 then 404                                 | Pass   |
| Missing id get/update/delete       | id 999999                                | 404 envelope each time                       | Pass   |

### Inventory Module Test Cases (Phase 9)

| Test Case                          | Input                                    | Expected Result                              | Status |
| ---------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Create with opening stock          | Milk 12.5 L                              | 201; qty 12.5 + first "Opening stock" movement | Pass |
| Zero opening stock                 | initial_quantity 0                       | 201; no history rows yet                     | Pass   |
| Rounding                           | qty/min 3 dp, price 2 dp                 | 1.0004→1.0, 250.0004→250.0, 1.999→2.0        | Pass   |
| Duplicate name case-insensitive    | "Tea Powder" / "TEA POWDER"              | 409 both                                     | Pass   |
| PUT never touches stock            | Full update of a stocked item            | Quantity unchanged                           | Pass   |
| Stock In adds units                | +2.5 on 5 L                              | 7.5; history row balance_after 7.5           | Pass   |
| Stock Out removes units            | −4 from 10                               | 6; history row written                       | Pass   |
| Insufficient stock atomic          | Remove 5 from 3                          | 409 "Not enough stock"; qty unchanged; no history row in DB | Pass |
| Adjustment sets absolute level     | Counted total 14 then 0                  | Level set exactly; zero allowed              | Pass   |
| Low-stock thresholds               | qty above/at/below minimum               | False / True / True flags                    | Pass   |
| Filters search/category/supplier/low-stock-only | Query params                | Only matching rows; summary counts correct   | Pass   |
| History endpoint newest first      | item_id + type filters                   | Newest first; filter respected               | Pass   |
| Distinct categories endpoint       | Created materials                        | Sorted unique category list                  | Pass   |
| Invalid creates (parametrised)     | Blank name/category, unknown unit, negative qty/min/price/supplier id, text qty, boolean number, overlong notes | 422 each | Pass |
| Invalid movements (parametrised)   | Bad/empty/missing type, zero/negative In-Out, negative Adjustment, boolean qty, 201-char note | 422 each | Pass |
| Unknown supplier on create/update  | supplier_id 999999                       | 404 "Create it first"                        | Pass   |
| Unknown item on all routes         | id 999999 get/put/delete/stock           | 404 envelope each                            | Pass   |
| Delete cascades history            | DELETE item after movements              | Transaction rows gone (direct DB check)      | Pass   |
| Supplier delete clears link only   | DELETE supplier of a stocked material    | Item keeps stock/history; supplier NULL      | Pass   |
| Persisted in SQLite                | Direct session query after API create    | Exact values found                           | Pass   |

Live smoke test (uvicorn on a free port against a temporary SQLite file): `/suppliers` and `/inventory` pages served their markup with their page scripts wired; a supplier and a material (Milk, 10 L opening stock) were created through the API; an 8 L Stock Out returned "New balance: 2.0 Litre", flipping the low-stock flag (minimum 3).

### Purchases Module Test Cases (Phase 10)

Tests use a unique per-run name tag, so reruns never collide with leftover data.

| Test Case                          | Input                                    | Expected Result                              | Status |
| ---------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Successful multi-item purchase     | Supplier + 2 materials                   | 201; PUR-xxxx number; totals server-calculated; date defaults today; Unpaid | Pass |
| Explicit date + paid status        | purchase_date, payment_status, notes     | Values echoed on the created purchase        | Pass   |
| Inventory update + history         | 4 L purchased on 10 L stock              | Level 14; newest "Stock In" row notes `Purchase PUR-xxxx`, balance_after 14 | Pass |
| Multiple materials in one purchase | 3 lines                                  | Every material's level increased correctly   | Pass   |
| Total rounding                     | qty 3.33341 × cost 10.558                | qty→3.333, cost→10.56, line/total→35.20      | Pass   |
| Unknown supplier                   | supplier_id 999999                       | 404; nothing created; stock unchanged        | Pass   |
| Unknown material atomic rollback   | 1 valid + 1 missing line                 | 404; valid material's stock unchanged; no purchase row left | Pass |
| Inactive material                  | Purchasing an inactive material          | 409 "marked inactive"                        | Pass   |
| Invalid item lists (parametrised)  | Empty cart, zero/negative qty, negative cost, duplicate material, missing id/cost | 422 each | Pass |
| Invalid scalars (parametrised)     | supplier_id 0/True/"abc", bad date, bad payment status, overlong notes, boolean qty | 422 each | Pass |
| List filters                       | search number/supplier, supplier_id, payment_status, date range | Only matching rows; summary counts correct | Pass |
| Detail + missing id                | GET detail / id 999999                   | 200 full detail with snapshots / 404 envelope | Pass  |
| Payment status toggle              | Mark Paid → Unpaid → invalid value       | Echoed each way; 422 for invalid             | Pass   |
| Supplier delete keeps history      | DELETE supplier of a recorded purchase   | Purchase remains; supplier_id NULL; name snapshot kept; total intact | Pass |
| Persisted in SQLite                | Direct session query after API create    | Exact header + line values found             | Pass   |

Smoke check: `/purchases` page served its markup with `purchases.js` wired; `/api/purchases` returned the summary envelope (`count`, `total_amount`, `unpaid_count`, `unpaid_amount`) on the live server.

### Employees Module Test Cases (Phase 11)

| Test Case                              | Input                                    | Expected Result                              | Status |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Successful create                      | Valid name/mobile/email/role/date/salary | 201; values echoed (email lowercased)        | Pass   |
| Salary-count accuracy                  | Create employee then add salary records  | `salary_count` reflects the additions        | Pass   |
| Search & role filter                   | search term, `role=Chef`, `include_inactive=false` | Only matching rows, ordered by name  | Pass |
| Invalid mobile (parametrised)          | 5 / 11 digit, non-digit, spaces          | 422 each                                    | Pass   |
| Invalid email format                   | "not-an-email"                           | 422                                          | Pass   |
| Role not in allowlist                  | "Owner"                                  | 422                                          | Pass   |
| Future joining date                    | tomorrow                                 | 422                                          | Pass   |
| Negative / boolean base salary         | `-100` / `true`                          | 422 each                                     | Pass   |
| Unknown id on all routes               | id 999999 get/put/delete                 | 404 envelope each                            | Pass   |
| Delete guard with salaries             | DELETE after salary records exist        | 409 "Delete their salary history first"      | Pass   |
| Persisted in SQLite                    | Direct session query after API create    | Exact values found                           | Pass   |

### Salaries Module Test Cases (Phase 12)

| Test Case                              | Input                                    | Expected Result                              | Status |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Successful create                       | Employee + `2026-08` + base 25000        | 201; net = base + bonus − deduction          | Pass   |
| Server-computed net (bonus/deduction)   | 25000 + 2000 − 500                       | 26500 stored (never client-supplied)         | Pass   |
| Omitted base falls back                 | Provide only employee + month            | base copied from employee's current base     | Pass   |
| Duplicate month per employee            | Second record for same `2026-08`         | 409                                          | Pass   |
| Deduction exceeds base + bonus          | 25000 − 30000                            | 422 (net cannot be negative)                 | Pass   |
| Bad month format                        | `2026-8`, `aug-2026`, year 1999/2101     | 422 each                                     | Pass   |
| Unknown employee                        | employee_id 999999                       | 404                                          | Pass   |
| Paid default date                       | POST with `payment_status: Paid`         | payment_date defaults to today               | Pass   |
| List filters                            | employee_id / month / payment_status     | Only matching rows, newest month first       | Pass   |
| Persisted in SQLite                     | Direct session query after API create    | Exact net/month/employee found               | Pass   |

### Expenses Module Test Cases (Phase 13)

| Test Case                              | Input                                    | Expected Result                              | Status |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Successful create                       | Valid title/category/amount/date/method   | 201 "Expense recorded."; defaults applied    | Pass   |
| Defaults                                | Omit expense_date & payment_method       | expense_date = today; payment_method = Cash  | Pass   |
| Valid category accepted                 | Each of the 7 allowlist categories       | 201 for each                                 | Pass   |
| Category not in allowlist               | "Advertisin" / empty                     | 422 each                                     | Pass   |
| Negative / zero / boolean amount        | `-5`, `0`, `true`                        | 422 each                                     | Pass   |
| Amount rounding                         | `12.345`                                 | stored as `12.35`                            | Pass   |
| Overlong title / notes                  | 121-char title, 256-char notes           | 422 each                                     | Pass   |
| Duplicate title allowed                 | Reuse an existing title ("Rent")         | 201 (paid twice is legitimate)               | Pass   |
| Payment method not in allowlist         | "Cheque"                                 | 422                                          | Pass   |
| Invalid date values                     | `2026-2-30`, `abcd`                      | 422 each (automatic date parsing)            | Pass   |
| List filters                            | search / category / payment_method / start_date / end_date | Only matching rows; `summary` totals match granularity of the filters | Pass |
| Empty date range returns empty          | start = end, no matching expenses        | 200; `items: []`, `count: 0`, total 0        | Pass   |
| /api/expenses/options                   | GET                                      | 200; categories + payment_methods lists      | Pass   |
| Unknown id on all routes                | id 999999 get/put/delete                 | 404 envelope each                            | Pass   |
| Persisted in SQLite                     | Direct session query after API create    | Exact values found                           | Pass   |

Smoke check: `/expenses` page served its markup with `expenses.js` wired; the dashboard and reports tabs could open the expense record on the live server.

### Reports Module Test Cases (Phase 14)

| Test Case                              | Input                                    | Expected Result                              | Status |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------- | ------ |
| Sales daily / weekly / monthly         | Three orders across days; switch period  | Each period sums only paid orders; labels/amounts/order-counts line up | Pass |
| Unpaid orders excluded                 | Unpaid + paid orders in range            | `sales_total` counts paid only               | Pass   |
| Date range respected                   | start_date = end_date                    | Only that day's orders appear                | Pass   |
| Bad period / mode values (parametrised)| `period=yearly`, `report_type=bogus`, `group_by=bogus` | 422 each                                    | Pass |
| Inventory current / low / movements   | report_type each                         | current lists materials + low flag; low lists only ≤ minimum; movements returns latest transactions | Pass |
| Purchases by supplier / by date        | group_by each with dates                 | Grouped rows, count + total per group        | Pass   |
| Salaries by month                      | Records across several months            | Total = Σ net_salary; newest month first     | Pass   |
| Expenses by category / by date         | group_by each                            | Grouped count + total; categories highest-first | Pass |
| Profit arithmetic                      | Known sales/purchases/salaries/expenses  | estimated_profit = sales − purchases − salaries − expenses exactly | Pass |
| Empty database / no filters            | Fresh DB, no params                      | 200 with zeroed summary — never a crash      | Pass   |
| Persisted data reflected live          | Create order/purchase/salary/expense, then fetch report | New values appear without any stored report table | Pass |

Smoke check: `/reports` page served its markup with `reports.js` wired; each tab returned a 200 envelope from `/api/reports/*` on the live server, and the Profit tab rendered the four-component Estimated Profit grid.

## Chapter 9 — Implementation

### Installation

```bash
uv sync
uv run cafe-server
```

Open http://127.0.0.1:8000. The database creates itself on first run. For auto-reload during development use `uv run uvicorn app.main:app --reload`. Non-uv users can `pip install -r requirements.txt`.

### User Training

Current UI requires no training beyond navigation; module-specific training will be documented as phases complete.

### Limitations

* Employee/salary/expense modules currently cover recording and reporting only; attendance/time-sheets and automated payslip generation are out of scope
* Salaries in the Profit report are matched by month, not by an exact day, so the Estimated Profit is an approximation (explicitly labelled in the UI)
* Expenses record a single flat amount per entry — no tax breakup, instalments or attachments
* Purchases are record-only: mistakes cannot be edited or deleted — the audit trail stays intact by design
* Purchase payments track only Paid/Unpaid; partial payments and supplier ledgers are out of scope
* Stock usage is recorded manually via Stock Out; recipes do not deduct ingredients automatically
* Deleting a raw material also deletes its movement history (by design, keeps the demo database clean)
* Orders cannot be edited after placement — cancel and re-take instead (keeps bills audit-proof)
* No refunds in-system; refunds for paid orders are handled manually outside the software
* Single computer / single cafe deployment
* No authentication yet (planned as simple admin/staff login)

### Future Enhancements

QR-code menu access, online ordering/payments, multi-branch support, cloud backup, WhatsApp notifications, GST invoices, role-based access.

## Chapter 10 — Bibliography

* FastAPI documentation — https://fastapi.tiangolo.com/
* SQLAlchemy 2.0 documentation — https://docs.sqlalchemy.org/
* SQLite documentation — https://www.sqlite.org/docs.html
* Pydantic documentation — https://docs.pydantic.dev/
* uv documentation — https://docs.astral.sh/uv/
* MDN Web Docs (HTML/CSS/JavaScript) — https://developer.mozilla.org/

## Glossary

| Term        | Meaning                                                     |
| ----------- | ----------------------------------------------------------- |
| CRUD        | Create, Read, Update, Delete operations                     |
| ORM         | Object Relational Mapper (SQLAlchemy maps classes to tables)|
| REST API    | HTTP interface returning JSON                               |
| Envelope    | Standard JSON wrapper for success/error responses           |
| Lifespan    | FastAPI startup/shutdown hook used to initialize the DB     |
| Estimated Profit | Sales − Purchases − Salaries − Expenses; an approximate management figure (salaries matched by month) |

## Development Phases Roadmap

| Phase | Module                          | Status      |
| ----- | ------------------------------- | ----------- |
| 1     | Project Foundation              | Implemented |
| 2     | Cafe Settings                   | Implemented |
| 3–4   | Categories & Menu Items         | Implemented |
| 5     | Customer Digital Menu           | Implemented |
| 6     | Orders                          | Implemented |
| 7     | Billing                         | Implemented |
| 8     | Suppliers                       | Implemented |
| 9     | Inventory                       | Implemented |
| 10    | Purchases                       | Implemented |
| 11    | Employees                       | Implemented |
| 12    | Salaries                        | Implemented |
| 13    | Expenses                        | Implemented |
| 14    | Reports                         | Implemented |
| 15    | Live Dashboard                  | Planned     |
| 16–17 | System Testing & Final Docs     | Planned     |

