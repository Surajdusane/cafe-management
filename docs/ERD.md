# ER Diagram (ERD) — Cafe Management System

The ERD grows as phases are implemented. Only entities that exist in the SQLite database are shown below; planned entities are listed at the end.

## Implemented Entities

### CafeSetting (Phase 2)

A single-row configuration table. The primary key is always `1`, so there is exactly one settings record for the whole cafe (singleton pattern).

```text
┌──────────────────────────────────────────────┐
│                  CafeSetting                 │
├──────────────────────────────────────────────┤
│ PK  id            INTEGER   (= 1, singleton) │
│     cafe_name     VARCHAR(100)  NOT NULL     │
│     address       VARCHAR(255)               │
│     phone         VARCHAR(15)                │
│     email         VARCHAR(100)               │
│     logo_url      VARCHAR(300)               │
│     tax_percent   FLOAT  NOT NULL  (0–100)   │
│     currency      VARCHAR(8)   NOT NULL      │
│     receipt_footer VARCHAR(200)              │
│     updated_at    DATETIME                   │
└──────────────────────────────────────────────┘
```

**Relationships:** none. CafeSetting is a standalone configuration entity. From Phase 7 (Billing) onwards it is *logically referenced*: billing reads `tax_percent`, `currency` and `receipt_footer` when generating bills, but no foreign key is required because there is always exactly one row.

### Category (Phase 3)

Groups menu items together (Coffee, Tea, Snacks…). Names are unique.

```text
┌──────────────────────────────────────────────┐
│                   Category                   │
├──────────────────────────────────────────────┤
│ PK  id            INTEGER      AUTOINCREMENT │
│ U1  name          VARCHAR(80)  NOT NULL      │
│     description   VARCHAR(255)               │
│     is_active     BOOLEAN      NOT NULL      │
│     created_at    DATETIME     NOT NULL      │
│     updated_at    DATETIME                   │
└──────────────────────────────────────────────┘
```

**Relationships:** `Category 1 : N MenuItem` — one category holds many menu items; each item belongs to exactly one category (`menu_items.category_id` FK). Deleting a category through the API is blocked while items still reference it; when a delete does happen the ORM removes any remaining children (cascade).

### MenuItem (Phase 4)

An item sold by the cafe. The pair `(category_id, name)` is unique, so names can repeat across categories but never inside one category.

```text
┌───────────────────────────────────────────────────────┐
│                       MenuItem                        │
├───────────────────────────────────────────────────────┤
│ PK  id             INTEGER      AUTOINCREMENT         │
│ FK  category_id    INTEGER      NOT NULL → categories │
│     name           VARCHAR(120) NOT NULL              │
│     description    VARCHAR(500)                       │
│     price          FLOAT        NOT NULL  (> 0)       │
│     image_url      VARCHAR(300)                       │
│     is_vegetarian  BOOLEAN      NOT NULL              │
│     is_popular     BOOLEAN      NOT NULL              │
│     is_available   BOOLEAN      NOT NULL              │
│     created_at     DATETIME     NOT NULL              │
│     updated_at     DATETIME                           │
└───────────────────────────────────────────────────────┘
```

**Relationships:** `MenuItem N : 1 Category` via `category_id`. From Phase 6 (Orders), OrderItem will additionally reference `menu_items.id`. Since Phase 5 (public menu), `is_available` and the display fields are also read by the public `/api/public/menu` endpoint — read-only, with ids and timestamps stripped from the response.

## Planned Entities (not yet created)

| Entity          | Relationship to existing entities           | Phase |
| --------------- | ------------------------------------------- | ----- |
| Order           | 1 : N → OrderItem; logically → CafeSetting  | 6     |
| OrderItem       | N : 1 → Order, N : 1 → MenuItem             | 6     |
| Supplier        | 1 : N → Purchase                            | 8     |
| InventoryItem   | 1 : N → InventoryTransaction                | 9     |
| Purchase        | 1 : N → PurchaseItem                        | 10    |
| PurchaseItem    | N : 1 → Purchase, related to InventoryItem  | 10    |
| Employee        | 1 : N → Salary                              | 11–12 |
| Expense         | standalone                                  | 13    |

## Cardinality Summary (current database)

```text
CafeSetting  ───  (0..1 row, id = 1)          no FK relationships
Category     1 ──── N  MenuItem               menu_items.category_id → categories.id
```

---
*Last updated: Phase 5 completion (public menu reads existing tables read-only; no schema change).*
