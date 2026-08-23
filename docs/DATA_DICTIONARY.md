# Data Dictionary — Cafe Management System

This document lists every table that exists in the SQLite database (`data/cafe.db`), with field-level detail. It is updated after each phase.

## Current Status (Phase 2 — Cafe Settings)

**Domain tables created so far: 1.**

| Table          | Purpose                                  | Phase |
| -------------- | ---------------------------------------- | ----- |
| cafe_settings  | Cafe profile, tax %, currency, receipt   | 2     |

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

## Planned Tables (not yet created)

| Table                  | Purpose                                   | Phase |
| ---------------------- | ----------------------------------------- | ----- |
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

---
*Last updated: Phase 2 completion.*
