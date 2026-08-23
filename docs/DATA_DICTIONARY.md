# Data Dictionary — Cafe Management System

This document lists every table that exists in the SQLite database (`data/cafe.db`), with field-level detail. It is updated after each phase.

## Current Status (Phase 1 — Project Foundation)

**Domain tables created so far: none.**

Phase 1 delivers the application foundation: the SQLAlchemy engine, the declarative `Base`, session management and `init_db()` which creates `data/cafe.db` on startup. The first business table (Cafe Settings) arrives in Phase 2; menu categories in Phase 3.

The metadata currently contains **0 tables**, verified by `GET /api/meta/tables`.

## Planned Tables (not yet created)

| Table                  | Purpose                                   | Phase |
| ---------------------- | ----------------------------------------- | ----- |
| cafe_settings          | Cafe name, tax %, currency, receipt info  | 2     |
| categories             | Menu categories                           | 3     |
| menu_items             | Menu items with price, image, flags       | 4     |
| orders                 | Order headers                             | 6     |
| order_items            | Order line items                          | 6     |
| suppliers              | Supplier master                           | 8     |
| inventory_items        | Raw materials with stock levels           | 9     |
| inventory_transactions | Stock add/reduce history                  | 9     |
| purchases              | Purchase headers                          | 10    |
| purchase_items         | Purchase line items                       | 10    |
| employees              | Employee master                           | 11    |
| salaries               | Salary payments                           | 12    |
| expenses               | Operating expenses                        | 13    |

## Field Entry Format

Each table section will use this format once created:

```text
Field Name | Data Type | Description | Primary Key | Foreign Key | Nullable | Example
```

---
*Last updated: Phase 1 completion.*
