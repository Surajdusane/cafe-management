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
* **Admin/Cafe staff** — enters and manages cafe settings, menu categories and menu items through the browser.
* **Customer** — receives a shareable digital menu link (fully wired in Phase 5).

**Data stores (current):** `data/cafe.db` holding `cafe_settings`, `categories`, `menu_items`.

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

Planned (not yet implemented):
P4 Orders (Phase 6) ─▶ D4 orders / D5 order_items ─ reads D3 prices
P5 Public customer menu (Phase 5) ◀─ reads D1 branding + D2/D3 active rows
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

---
*Last updated: Phase 3–4 completion.*
