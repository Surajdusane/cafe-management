# Cafe Management System

A simple web-based Cafe Management System built for a final-year BCA/BBA Computer Application academic project. It manages the daily operations of a small or medium-sized cafe: menu, orders, billing, inventory, suppliers, purchases, employees, salaries, expenses and reports.

## Current Status — Phase 1: Project Foundation (complete)

Implemented so far:

- FastAPI application with SQLite database and SQLAlchemy setup
- Database initialization on application startup (`data/cafe.db`)
- Static file serving (CSS / JS / images)
- Admin shell layout: sidebar navigation, top bar, responsive design
- Dashboard placeholder with honest empty states
- Placeholder screens for all 12 upcoming modules
- API error handling with a consistent JSON error envelope
- Reusable frontend utilities: `api.js` (fetch wrapper), `common.js` (toast notifications, confirm dialogs), `validation.js` (form validators)
- Automated tests for startup, pages, health endpoint and database initialization

Not yet implemented (planned phases): cafe settings, menu management, customer digital menu, orders, billing, suppliers, inventory, purchases, employees, salaries, expenses, reports, dashboard live data.

## Technology Stack

| Layer     | Technology                              |
| --------- | --------------------------------------- |
| Backend   | Python 3.11+, FastAPI                   |
| Database  | SQLite (single file: `data/cafe.db`)    |
| ORM       | SQLAlchemy 2.0                          |
| Validation| Pydantic v2 (server) + vanilla JS (client) |
| Frontend  | HTML5, CSS3, Vanilla JavaScript (no frameworks) |
| Testing   | pytest + httpx (FastAPI TestClient)     |
| Tooling   | uv package manager                      |

## Prerequisites

- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) package manager

## Setup and Run

The project is a proper [uv](https://docs.astral.sh/uv/) project (`pyproject.toml` + `uv.lock`).

```bash
# 1. Install everything (creates .venv, installs deps + the app itself)
uv sync

# 2. Start the server
uv run cafe-server
```

Open http://127.0.0.1:8000 in your browser.

Other useful commands:

```bash
# Development server with auto-reload
uv run uvicorn app.main:app --reload

# Run the automated test suite
uv run pytest -v

# Interactive API documentation (Swagger UI)
http://127.0.0.1:8000/docs
```

Environment overrides: `CAFE_HOST`, `CAFE_PORT`.

> `requirements.txt` is kept pinned for non-uv users (`pip install -r requirements.txt`). The SQLite database file is created automatically at `data/cafe.db` on first startup.

## Project Structure

```text
├── app/
│   ├── main.py               # FastAPI app, routes, error handlers
│   ├── core/
│   │   ├── config.py         # Paths and app configuration
│   │   └── database.py       # SQLAlchemy engine, session, init_db()
│   ├── models/               # SQLAlchemy models (added per phase)
│   ├── schemas/              # Pydantic schemas (added per phase)
│   ├── routers/              # API routers (added per phase)
│   ├── services/             # Business logic services (added per phase)
│   └── templates/            # HTML pages served by FastAPI
├── static/
│   ├── css/                  # main.css, dashboard.css, responsive.css
│   ├── js/                   # api.js, common.js, validation.js, dashboard.js
│   └── images/
├── data/                     # SQLite database lives here (auto-created)
├── tests/                    # pytest suite
├── docs/                     # ERD, DFD, Data Dictionary, API docs
├── document.md               # Main academic project documentation
└── requirements.txt
```

## Screens

| Route            | Screen          | Status                        |
| ---------------- | --------------- | ----------------------------- |
| `/`              | Dashboard       | Shell + placeholders (Phase 1)|
| `/menu`          | Menu Management | Placeholder → Phase 3–4       |
| `/customer-menu` | Customer Menu   | Placeholder → Phase 5         |
| `/orders`        | Orders          | Placeholder → Phase 6         |
| `/billing`       | Billing         | Placeholder → Phase 7         |
| `/suppliers`     | Suppliers       | Placeholder → Phase 8         |
| `/inventory`     | Inventory       | Placeholder → Phase 9         |
| `/purchases`     | Purchases       | Placeholder → Phase 10        |
| `/employees`     | Employees       | Placeholder → Phase 11        |
| `/salaries`      | Salaries        | Placeholder → Phase 12        |
| `/expenses`      | Expenses        | Placeholder → Phase 13        |
| `/reports`       | Reports         | Placeholder → Phase 14        |
| `/settings`      | Settings        | Placeholder → Phase 2         |

## Documentation

- `document.md` — main academic documentation (chapters, testing, revision history)
- `docs/API_DOCUMENTATION.md` — current endpoints and conventions
- `docs/DATA_DICTIONARY.md` — database tables (grows each phase)
- `docs/ERD.md`, `docs/DFD.md` — added as entities are designed

## License

Academic project — free to use for educational purposes.
