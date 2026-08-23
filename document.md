# Cafe Management System

A final-year project documentation for a web-based Cafe Management System developed with Python (FastAPI), SQLite and Vanilla JavaScript.

---

## Revision History

| Version | Date       | Change                                              |
| ------- | ---------- | --------------------------------------------------- |
| 1.0     | 2026-08-23 | Initial documentation · Phase 1 Foundation complete |

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

Development follows 17 phases (see Development Phases). Phase 1 — Project Foundation — is complete.

### Scope of Proposed System

* Centralized management of menu, orders, billing, stock, suppliers, staff and expenses
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
| 6  | Cafe settings management                            | Planned (Phase 2) |
| 7  | Category CRUD                                       | Planned (Phase 3) |
| 8  | Menu item CRUD with images and availability         | Planned (Phase 4) |
| 9  | Public customer digital menu                        | Planned (Phase 5) |
| 10 | Order creation and status tracking                  | Planned (Phase 6) |
| 11 | Billing with tax/discount and printable receipt     | Planned (Phase 7) |
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

### Current Architecture (Phase 1)

```text
Browser (HTML/CSS/JS)
   |  fetch() via static/js/api.js
   v
FastAPI application (app/main.py)
   |-- Page routes -> app/templates/*.html
   |-- Static files -> static/css, js, images
   |-- /api/health -> database check
   `-- Error handlers -> unified JSON envelope
   v
SQLAlchemy engine -> data/cafe.db (SQLite)
```

## Chapter 5 — I/O Screens

Screens implemented in Phase 1 (screenshots to be captured for final submission):

| Screen                | Route            | Notes                                              |
| --------------------- | ---------------- | -------------------------------------------------- |
| Dashboard shell       | `/`              | Sidebar, top bar, status chips, placeholder stats  |
| Menu Management       | `/menu`          | Placeholder card (Phase 3–4)                       |
| Customer Menu         | `/customer-menu` | Placeholder card (Phase 5)                         |
| Orders                | `/orders`        | Placeholder card (Phase 6)                         |
| Billing               | `/billing`       | Placeholder card (Phase 7)                         |
| Suppliers             | `/suppliers`     | Placeholder card (Phase 8)                         |
| Inventory             | `/inventory`     | Placeholder card (Phase 9)                         |
| Purchases             | `/purchases`     | Placeholder card (Phase 10)                        |
| Employees             | `/employees`     | Placeholder card (Phase 11)                        |
| Salaries              | `/salaries`      | Placeholder card (Phase 12)                        |
| Expenses              | `/expenses`      | Placeholder card (Phase 13)                        |
| Reports               | `/reports`       | Placeholder card (Phase 14)                        |
| Settings              | `/settings`      | Placeholder card (Phase 2)                         |

UI notes: espresso-and-paper theme, Fraunces/Inter typography, grouped navigation (Overview / Sales / Stock & Supply / People / Money & Insight / System), toast notifications, confirm dialogs, empty states, responsive sidebar collapsing under 1024px.

## Chapter 6 — Reports

No reports exist yet. Planned from Phase 14: daily/weekly/monthly sales, order status summary, current stock and low stock, purchases by supplier/date, monthly salary expense, expenses by category/date, estimated profit (Sales − Purchases − Salaries − Expenses).

## Chapter 7 — Coding

### Technology

* Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2
* SQLite via `data/cafe.db`
* HTML/CSS/Vanilla JS frontend; uv as package manager

### Key Files (Phase 1)

| File                      | Responsibility                                          |
| ------------------------- | ------------------------------------------------------- |
| `app/main.py`             | App factory, lifespan init, page routes, error handlers |
| `app/core/config.py`      | Paths, app name/version, database URL                   |
| `app/core/database.py`    | Engine, SessionLocal, Base, get_db(), init_db()         |
| `static/js/api.js`        | Fetch wrapper with ApiError                             |
| `static/js/common.js`     | Shell injection, navigation, toasts, confirm dialogs    |
| `static/js/validation.js` | Reusable form validators                                |
| `tests/`                  | pytest suite (startup + database)                       |

### Error Envelope

All API errors return `{ "success": false, "message": ..., "errors": [...] }`; validation failures use HTTP 422 with per-field messages.

## Chapter 8 — Software System Testing

Automated tests (`uv run pytest`) — 23 passed on 2026-08-23:

| Test Case                          | Input                    | Expected Result                     | Status |
| ---------------------------------- | ------------------------ | ----------------------------------- | ------ |
| Health endpoint                    | GET /api/health          | 200, status ok, database connected  | Pass   |
| Every page route loads             | GET each of 13 routes    | 200 text/html                       | Pass   |
| Unknown API route                  | GET /api/nope            | 404 JSON error envelope             | Pass   |
| Static assets served               | GET css/js/favicon       | 200 correct content type            | Pass   |
| Database file created at startup   | lifespan init_db()       | data/cafe.db exists                 | Pass   |
| Session executes query             | SELECT 1 via session     | Returns 1                           | Pass   |
| No premature domain tables         | Base.metadata            | 0 business tables before Phase 2    | Pass   |

Manual smoke test (uvicorn live): all 13 pages returned 200; health JSON verified; unknown route 404; static CSS/JS served.

## Chapter 9 — Implementation

### Installation

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. The database creates itself on first run.

### User Training

Current UI requires no training beyond navigation; module-specific training will be documented as phases complete.

### Limitations

* Business modules not yet implemented (see roadmap)
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
| 2     | Cafe Settings                   | Planned     |
| 3–4   | Categories & Menu Items         | Planned     |
| 5     | Customer Digital Menu           | Planned     |
| 6     | Orders                          | Planned     |
| 7     | Billing                         | Planned     |
| 8     | Suppliers                       | Planned     |
| 9     | Inventory                       | Planned     |
| 10    | Purchases                       | Planned     |
| 11    | Employees                       | Planned     |
| 12    | Salaries                        | Planned     |
| 13    | Expenses                        | Planned     |
| 14    | Reports                         | Planned     |
| 15    | Live Dashboard                  | Planned     |
| 16–17 | System Testing & Final Docs     | Planned     |

