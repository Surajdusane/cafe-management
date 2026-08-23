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

Development follows 17 phases (see Development Phases). Phases 1–7 are complete: Foundation, Cafe Settings, Categories, Menu Items, the Customer Digital Menu, Orders and Billing.

### Scope of Proposed System

* Centralized management of menu, orders, billing, stock, suppliers, staff and expenses
* Centralized cafe profile configuration (name, address, tax, currency, receipt footer)
* Automatic bill calculation with tax and discount
* Automatic inventory increase when purchases are recorded
* Basic reports: sales, orders, inventory, purchases, salaries, expenses and estimated profit
* A public customer-facing digital menu page
* Single-cafe, single-computer deployment (no cloud)

### Benefits of Proposed System

* Faster, error-free billing
* Real-time view of sales and low-stock warnings
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
| 12 | Supplier CRUD                                       | Planned (Phase 8) |
| 13 | Inventory with stock movements and low-stock alert  | Planned (Phase 9) |
| 14 | Purchases updating inventory automatically          | Planned (Phase 10)|
| 15 | Employee CRUD                                       | Planned (Phase 11)|
| 16 | Salary runs (base + bonus − deduction)              | Planned (Phase 12)|
| 17 | Expense recording                                   | Planned (Phase 13)|
| 18 | Reports and estimated profit summary                | Planned (Phase 14)|
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

### Current Architecture (Phases 2–7)

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
    `-- Error handlers -> unified JSON envelope (400/404/409/422/500)
    v
SQLAlchemy models (app/models) -> data/cafe.db (SQLite, PRAGMA foreign_keys=ON)
```

The `cafe_settings` table is a singleton (`id = 1`) created automatically on first read. Billing reads `tax_percent`, `currency` and `receipt_footer` from it: the tax rate is snapshotted onto every order at creation time so later settings changes never rewrite historical bills.

Menu data model: `Category 1:N MenuItem` (`menu_items.category_id`). Category names are unique; item names are unique **within** their category. Deleting a non-empty category is refused with HTTP 409. SQLite foreign-key enforcement is switched on for every connection, so referential integrity is guaranteed at the database level as well.

Order data model: `Order 1:N OrderItem` (`order_items.order_id`, ORM cascade). Each line snapshots the dish name and unit price (`order_items.menu_item_id` is `ON DELETE SET NULL`), so bills survive menu edits and deletions. The order number (`ORD-0001`, derived from the primary key) doubles as the bill number. Money formula — calculated exclusively server-side in `compute_totals()`: `taxable = subtotal − discount`; `tax = taxable × tax_percent/100`; `total = taxable + tax`. Orders are immutable after placement except status and payment; a wrong order is cancelled (and optionally deleted) and re-taken.

Public menu flow: the customer page `/menu/cafe` fetches `/api/public/menu`, which composes cafe branding from `cafe_settings` plus active non-empty categories and their items. The response contains only display fields — no ids, timestamps or admin flags — so nothing internal reaches the customer's browser.

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
| Suppliers             | `/suppliers`     | Placeholder card (Phase 8)                         |
| Inventory             | `/inventory`     | Placeholder card (Phase 9)                         |
| Purchases             | `/purchases`     | Placeholder card (Phase 10)                        |
| Employees             | `/employees`     | Placeholder card (Phase 11)                        |
| Salaries              | `/salaries`      | Placeholder card (Phase 12)                        |
| Expenses              | `/expenses`      | Placeholder card (Phase 13)                        |
| Reports               | `/reports`       | Placeholder card (Phase 14)                        |
| Settings              | `/settings`      | **Implemented (Phase 2)** — two-card form: cafe profile + billing/receipt, logo preview, loading skeleton, inline validation, save/discard actions |

### Orders Screen Behaviour (Phase 6)

The orders page (`/orders`, `data-page="orders"`) shows every order newest first with columns for number, type (dine-in rows carry a table chip), item count, total, status badge, payment badge and placed time. Toolbar: debounced search by order number plus status, type and payment filters.

**New order modal** — a segmented Dine-in/Takeaway toggle shows the table-number field only for dine-in; an item picker lists available dishes with prices (sold-out items hidden) and an add button merges duplicates into one line; the cart supports quantity steppers and removal; a dark totals box recalculates subtotal/discount/tax/grand-total live as lines or the discount change. Client validation mirrors the server: table required for dine-in (1–999), quantity integers 1–999, discount ≥ 0 and never above the subtotal. The client totals are UX only — the server recalculates everything on POST.

**Status workflow** — row actions offer View / Cancel / Delete; Cancel is hidden for completed and cancelled orders, Delete appears only for cancelled ones. The detail modal renders meta info, item lines and the money breakdown read-only plus a status dropdown (Pending → Preparing → Ready → Completed). Server rules: cancelled orders are frozen, paid orders cannot be cancelled.

### Billing Screen Behaviour (Phase 7)

The billing page (`/billing`) opens with three stat cards — Billed, Collected and Outstanding — computed server-side from `GET /api/bills` summary over the filtered result set. The bills table adds money columns (subtotal, discount, tax with its rate, grand total), payment method and status badges per row.

**Payments** — "Mark paid" opens a modal with four method buttons (Cash / UPI / Card / Other); choosing one calls `POST /api/bills/{id}/pay`. Paid bills can never be double-charged (409) and cancelled orders refuse payment.

**Printable receipt** — "Receipt" fetches bill detail including cafe branding (name, address, phone, currency, footer from Settings) and renders a thermal-style paper slip: header, dashed separators, line items with quantity × price, tax/discount/total block and footer message. "Print receipt" triggers the browser print dialog; print CSS hides everything except the paper and constrains it to 80 mm for receipt printers.

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

No reports exist yet. Planned from Phase 14: daily/weekly/monthly sales, order status summary, current stock and low stock, purchases by supplier/date, monthly salary expense, expenses by category/date, estimated profit (Sales − Purchases − Salaries − Expenses).

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
| `app/schemas/cafe_setting.py`     | Pydantic request/response schemas + validation          |
| `app/schemas/category.py`         | Category create/update/read schemas                     |
| `app/schemas/menu_item.py`        | Menu item schemas; price > 0, rounding, trims           |
| `app/schemas/order.py`            | Order create/status/payment/read schemas; qty & discount rules |
| `app/services/settings_service.py`| Get-or-create singleton, update logic                   |
| `app/services/category_service.py`| Category CRUD, duplicate check, delete guard            |
| `app/services/menu_item_service.py`| Item CRUD, FK validation, per-category duplicate check |
| `app/services/order_service.py`   | Order creation with server totals, status workflow, delete guard |
| `app/services/billing_service.py` | Bill list + summary totals, payment recording           |
| `app/routers/settings.py`         | GET/PUT /api/settings                                   |
| `app/routers/categories.py`       | CRUD /api/categories (+search, include_inactive)        |
| `app/routers/menu.py`             | CRUD /api/menu/items (+filters)                         |
| `app/routers/orders.py`           | Orders API: list/create/detail/status/delete            |
| `app/routers/billing.py`          | Bills API: list/detail/pay                              |
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
| `tests/`                          | pytest suite (startup, database, settings, categories, menu items, public menu, orders, billing) |

### Error Envelope

All API errors return `{ "success": false, "message": ..., "errors": [...] }`; validation failures use HTTP 422 with per-field messages.

## Chapter 8 — Software System Testing

Automated tests (`uv run pytest`) — 158 passed on 2026-08-23 (startup 19, database 5, settings 15, categories 22, menu items 32, public menu 9, orders 37, billing 19):

| Test Case                          | Input                    | Expected Result                     | Status |
| ---------------------------------- | ------------------------ | ----------------------------------- | ------ |
| Health endpoint                    | GET /api/health          | 200, status ok, database connected  | Pass   |
| Every page route loads             | GET each of 13 routes    | 200 text/html                       | Pass   |
| Unknown API route                  | GET /api/nope            | 404 JSON error envelope             | Pass   |
| Static assets served               | GET css/js/favicon       | 200 correct content type            | Pass   |
| Database file created at startup   | lifespan init_db()       | data/cafe.db exists                 | Pass   |
| Session executes query             | SELECT 1 via session     | Returns 1                           | Pass   |
| Implemented tables registered      | Base.metadata            | cafe_settings, categories, menu_items, orders, order_items present | Pass |
| No future domain tables            | Base.metadata            | inventory/purchases/employees/etc. absent | Pass |

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

* Stock/supplier/employee modules not yet implemented (see roadmap)
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

## Development Phases Roadmap

| Phase | Module                          | Status      |
| ----- | ------------------------------- | ----------- |
| 1     | Project Foundation              | Implemented |
| 2     | Cafe Settings                   | Implemented |
| 3–4   | Categories & Menu Items         | Implemented |
| 5     | Customer Digital Menu           | Implemented |
| 6     | Orders                          | Implemented |
| 7     | Billing                         | Implemented |
| 8     | Suppliers                       | Planned     |
| 9     | Inventory                       | Planned     |
| 10    | Purchases                       | Planned     |
| 11    | Employees                       | Planned     |
| 12    | Salaries                        | Planned     |
| 13    | Expenses                        | Planned     |
| 14    | Reports                         | Planned     |
| 15    | Live Dashboard                  | Planned     |
| 16–17 | System Testing & Final Docs     | Planned     |

