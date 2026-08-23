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

**Relationships:** none yet. CafeSetting is a standalone configuration entity. From Phase 7 (Billing) onwards it is *logically referenced*: billing reads `tax_percent`, `currency` and `receipt_footer` when generating bills, but no foreign key is required because there is always exactly one row.

## Planned Entities (not yet created)

| Entity          | Relationship to CafeSetting / others        | Phase |
| --------------- | ------------------------------------------- | ----- |
| Category        | 1 : N → MenuItem                            | 3     |
| MenuItem        | N : 1 → Category                            | 4     |
| Order           | 1 : N → OrderItem                           | 6     |
| OrderItem       | N : 1 → Order, N : 1 → MenuItem             | 6     |
| Supplier        | 1 : N → Purchase                            | 8     |
| InventoryItem   | 1 : N → InventoryTransaction                | 9     |
| Purchase        | 1 : N → PurchaseItem                        | 10    |
| PurchaseItem    | N : 1 → Purchase, related to InventoryItem  | 10    |
| Employee        | 1 : N → Salary                              | 11–12 |
| Expense         | standalone                                  | 13    |

## Cardinality Summary (current database)

```text
CafeSetting  ───  (0..1 row, id = 1)   no FK relationships
```

---
*Last updated: Phase 2 completion.*
