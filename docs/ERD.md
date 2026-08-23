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

**Relationships:** `MenuItem N : 1 Category` via `category_id`. From Phase 6, OrderItem additionally references `menu_items.id`. Since Phase 5 (public menu), `is_available` and the display fields are also read by the public `/api/public/menu` endpoint — read-only, with ids and timestamps stripped from the response.

### Order (Phase 6–7)

One customer order together with its bill. Billing fields live on the order: the order number (`ORD-0001`, generated from the primary key) doubles as the bill number on receipts. Money values are calculated once by the server at creation time and never recomputed, so later menu or settings changes cannot rewrite history.

```text
┌──────────────────────────────────────────────────────────┐
│                         Order                            │
├──────────────────────────────────────────────────────────┤
│ PK  id               INTEGER      AUTOINCREMENT          │
│ U1  order_number     VARCHAR(20)  NOT NULL  (ORD-xxxx)   │
│     order_type       VARCHAR(10)  NOT NULL               │
│         values: "Dine-in" | "Takeaway"                   │
│     table_number     INTEGER             (Dine-in only)  │
│     status           VARCHAR(12)  NOT NULL               │
│         values: Pending | Preparing | Ready |            │
│                 Completed | Cancelled                    │
│     subtotal         FLOAT        NOT NULL               │
│     discount_amount  FLOAT        NOT NULL  (≥ 0)        │
│     tax_percent      FLOAT        NOT NULL  (snapshot)   │
│     tax_amount       FLOAT        NOT NULL               │
│     total            FLOAT        NOT NULL               │
│     payment_method   VARCHAR(10)         ("Cash","UPI",  │
│                              "Card","Other")             │
│     payment_status   VARCHAR(10)  NOT NULL               │
│         values: "Unpaid" | "Paid"                        │
│     paid_at          DATETIME                            │
│     created_at       DATETIME     NOT NULL               │
│     updated_at       DATETIME                           │
└──────────────────────────────────────────────────────────┘
```

**Relationships:** `Order 1 : N OrderItem` — deleting an Order removes its item lines (ORM cascade `all, delete-orphan`). Logically reads CafeSetting: `tax_percent` is snapshotted from the singleton settings row when the order is placed.

### OrderItem (Phase 6)

One ordered line inside an order. `item_name` and `unit_price` are copied from the menu at order time so bills stay correct even if the menu changes later.

```text
┌────────────────────────────────────────────────────────────┐
│                         OrderItem                          │
├────────────────────────────────────────────────────────────┤
│ PK  id             INTEGER      AUTOINCREMENT              │
│ FK  order_id       INTEGER      NOT NULL → orders          │
│ FK  menu_item_id   INTEGER                 → menu_items    │
│                                 ON DELETE SET NULL         │
│     item_name      VARCHAR(120) NOT NULL  (snapshot)       │
│     unit_price     FLOAT        NOT NULL  (snapshot)       │
│     quantity       INTEGER      NOT NULL  (1–999)          │
│     line_total     FLOAT        NOT NULL = qty × unit price│
└────────────────────────────────────────────────────────────┘
```

**Relationships:** `OrderItem N : 1 Order` via `order_id`; `OrderItem N : 1 MenuItem` via `menu_item_id` — nullable with `ON DELETE SET NULL` because a deleted menu dish must not erase old bills; the snapshot columns keep the history readable.

## Planned Entities (not yet created)

| Entity               | Relationship to existing entities           | Phase |
| -------------------- | ------------------------------------------- | ----- |
| Supplier             | 1 : N → Purchase                            | 8     |
| InventoryItem        | 1 : N → InventoryTransaction                | 9     |
| Purchase             | 1 : N → PurchaseItem                        | 10    |
| PurchaseItem         | N : 1 → Purchase, related to InventoryItem  | 10    |
| Employee             | 1 : N → Salary                              | 11–12 |
| Expense              | standalone                                  | 13    |

## Cardinality Summary (current database)

```text
CafeSetting  ───  (0..1 row, id = 1)          no FK; read by billing for tax snapshot
Category     1 ──── N  MenuItem               menu_items.category_id → categories.id
MenuItem     1 ──── N  OrderItem              order_items.menu_item_id → menu_items.id (SET NULL)
Order        1 ──── N  OrderItem              order_items.order_id → orders.id (cascade)
```

## Business Rules enforced around Orders

* Money formula (server-side only): `taxable = subtotal − discount`; `tax = taxable × tax_percent / 100`; `total = taxable + tax`.
* Dine-in requires a table number (1–999); takeaways always have none.
* A line's quantity must be an integer 1–999; each menu item may appear on one line only.
* Every ordered dish must exist and be marked available at order time.
* Discount may not exceed the subtotal.
* Cancelled orders become immutable; paid orders can never be cancelled (refunds happen outside the system).
* Only cancelled orders may be hard-deleted.
* Payment is recorded exclusively through the billing API (`payment_method` + server-set `Paid`); the client never sends payment state.

---
*Last updated: Phase 6–7 completion (Orders and Billing).*
*Previous: Phase 5 completion (public menu reads existing tables read-only; no schema change).*
