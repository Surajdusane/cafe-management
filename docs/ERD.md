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

### Supplier (Phase 8)

A business the cafe buys raw materials from. Names are unique (any case).

```text
┌──────────────────────────────────────────────┐
│                   Supplier                   │
├──────────────────────────────────────────────┤
│ PK  id                  INTEGER  AUTOINCREMENT │
│ U1  name                VARCHAR(100) NOT NULL│
│     contact_person      VARCHAR(100)         │
│     phone               VARCHAR(15)  (10-digit pattern when set) │
│     email               VARCHAR(100) (valid format when set)     │
│     address             VARCHAR(255)         │
│     materials_supplied  VARCHAR(255)         │
│     is_active           BOOLEAN   NOT NULL   │
│     created_at          DATETIME  NOT NULL   │
│     updated_at          DATETIME             │
└──────────────────────────────────────────────┘
```

**Relationships:** `Supplier 1 : N InventoryItem` via `inventory_items.supplier_id` — an optional "preferred supplier" link on each raw material. Deleting a supplier is always allowed; the FK is `ON DELETE SET NULL`, so materials simply lose the link while their stock and history remain untouched.

### InventoryItem (Phase 9)

A raw material kept in stock. Names are unique. The live level (`current_quantity`) changes only through stock movements.

```text
┌────────────────────────────────────────────────────────────┐
│                      InventoryItem                         │
├────────────────────────────────────────────────────────────┤
│ PK  id               INTEGER      AUTOINCREMENT            │
│ U1  name             VARCHAR(120) NOT NULL                 │
│     category         VARCHAR(80)  NOT NULL (free text)     │
│     unit             VARCHAR(12)  NOT NULL                 │
│         values: Kg | Gram | Litre | Millilitre |           │
│                 Piece | Packet | Box                       │
│     current_quantity FLOAT        NOT NULL  (≥ 0)          │
│     minimum_stock    FLOAT        NOT NULL  (≥ 0)          │
│     purchase_price   FLOAT        NOT NULL  (≥ 0, per unit)│
│ FK  supplier_id      INTEGER                 → suppliers   │
│                              ON DELETE SET NULL            │
│     is_active        BOOLEAN      NOT NULL                 │
│     notes            VARCHAR(255)                          │
│     created_at       DATETIME     NOT NULL                 │
│     updated_at       DATETIME                              │
└────────────────────────────────────────────────────────────┘
```

**Relationships:** `InventoryItem 1 : N InventoryTransaction` — deleting a material removes its movement history (ORM cascade). Derived rule: `is_low_stock = current_quantity <= minimum_stock` (out-of-stock is always flagged).

### InventoryTransaction (Phase 9)

One recorded stock movement. Every quantity change to a material writes exactly one of these rows.

```text
┌──────────────────────────────────────────────────────────┐
│                  InventoryTransaction                    │
├──────────────────────────────────────────────────────────┤
│ PK  id               INTEGER      AUTOINCREMENT          │
│ FK  item_id          INTEGER      NOT NULL → inventory_items (cascade) │
│     transaction_type VARCHAR(12)  NOT NULL               │
│         values: "Stock In" | "Stock Out" | "Adjustment"  │
│     quantity         FLOAT        NOT NULL               │
│         Stock In/Out: amount moved (> 0);                │
│         Adjustment: new counted total (≥ 0)              │
│     balance_after    FLOAT        NOT NULL  (snapshot)   │
│     note             VARCHAR(200)                        │
│     created_at       DATETIME     NOT NULL               │
└──────────────────────────────────────────────────────────┘
```

**Relationships:** `InventoryTransaction N : 1 InventoryItem` via `item_id`. `balance_after` snapshots the stock level once the movement is applied so the history stays meaningful as later movements change the level.

### Purchase (Phase 10)

One recorded purchase from a supplier. Like orders, all money values are calculated once by the server when the purchase is recorded and never recomputed; the purchase number (`PUR-0001`, derived from the primary key) identifies it on history screens.

```text
┌──────────────────────────────────────────────────────────────┐
│                          Purchase                            │
├──────────────────────────────────────────────────────────────┤
│ PK  id               INTEGER      AUTOINCREMENT              │
│ U1  purchase_number  VARCHAR(20)  NOT NULL  (PUR-xxxx)       │
│ FK  supplier_id      INTEGER                 → suppliers     │
│                                   ON DELETE SET NULL         │
│     supplier_name    VARCHAR(100) NOT NULL  (snapshot)       │
│     purchase_date    DATE         NOT NULL (defaults today)  │
│     subtotal         FLOAT        NOT NULL = Σ line totals   │
│     total            FLOAT        NOT NULL (= subtotal)      │
│     payment_status   VARCHAR(10)  NOT NULL                   │
│         values: "Unpaid" | "Paid"                            │
│     notes            VARCHAR(255)                            │
│     created_at       DATETIME     NOT NULL                   │
│     updated_at       DATETIME                                │
└──────────────────────────────────────────────────────────────┘
```

**Relationships:** `Purchase 1 : N PurchaseItem` via `purchase_items.purchase_id` — deleting a purchase removes its lines (ORM cascade + DB `ON DELETE CASCADE`). `Purchase N : 1 Supplier` via `supplier_id` — nullable with `ON DELETE SET NULL`; the `supplier_name` snapshot keeps old purchases readable after the supplier master record is deleted.

### PurchaseItem (Phase 10)

One purchased material line inside a purchase. `item_name` and `unit` are copied from the raw material at purchase time so lines stay readable even if the material is renamed or deleted later.

```text
┌────────────────────────────────────────────────────────────────┐
│                         PurchaseItem                           │
├────────────────────────────────────────────────────────────────┤
│ PK  id                 INTEGER      AUTOINCREMENT              │
│ FK  purchase_id        INTEGER      NOT NULL → purchases       │
│                                     ON DELETE CASCADE          │
│ FK  inventory_item_id  INTEGER                 → inventory_items│
│                                     ON DELETE SET NULL         │
│     item_name          VARCHAR(120) NOT NULL  (snapshot)       │
│     unit               VARCHAR(12)  NOT NULL  (snapshot)       │
│     quantity           FLOAT        NOT NULL  (> 0, 3 dp)      │
│     unit_cost          FLOAT        NOT NULL  (≥ 0, 2 dp)      │
│     line_total         FLOAT        NOT NULL = qty × unit cost │
└────────────────────────────────────────────────────────────────┘
```

**Relationships:** `PurchaseItem N : 1 Purchase` via `purchase_id` (cascade); `PurchaseItem N : 1 InventoryItem` via `inventory_item_id` (`ON DELETE SET NULL`). Not a FK but a business rule: recording the purchase also writes one `Stock In` InventoryTransaction per line and increases `current_quantity` — in the same database transaction as the purchase itself.

## Planned Entities (not yet created)

| Entity               | Relationship to existing entities           | Phase |
| -------------------- | ------------------------------------------- | ----- |
| Employee             | 1 : N → Salary                              | 11–12 |
| Expense              | standalone                                  | 13    |

## Cardinality Summary (current database)

```text
CafeSetting          ───  (0..1 row, id = 1)   no FK; read by billing for tax snapshot
Category             1 ──── N  MenuItem        menu_items.category_id → categories.id
MenuItem             1 ──── N  OrderItem       order_items.menu_item_id → menu_items.id (SET NULL)
Order                1 ──── N  OrderItem       order_items.order_id → orders.id (cascade)
Supplier             1 ──── N  InventoryItem   inventory_items.supplier_id → suppliers.id (SET NULL)
InventoryItem        1 ──── N  InventoryTransaction  inventory_transactions.item_id → inventory_items.id (cascade)
Supplier             1 ──── N  Purchase        purchases.supplier_id → suppliers.id (SET NULL)
Purchase             1 ──── N  PurchaseItem    purchase_items.purchase_id → purchases.id (CASCADE)
InventoryItem        1 ──── N  PurchaseItem    purchase_items.inventory_item_id → inventory_items.id (SET NULL)
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

## Business Rules enforced around Suppliers & Inventory

* Material names and supplier names are unique (case-insensitive check at the API).
* Quantities, minimum stock and purchase prices can never be negative; opening/movement quantities round to 3 decimals, prices to 2.
* A material's supplier, when provided, must exist (HTTP 404 otherwise).
* `current_quantity` changes only through movements: Stock In (> 0), Stock Out (> 0), Adjustment (≥ 0 absolute level).
* Stock Out is atomic: a guarded SQL UPDATE refuses to go below zero (HTTP 409), so concurrent removals cannot oversell stock.
* A failed movement writes no history row; every successful one snapshots `balance_after`.
* Deleting a supplier keeps its materials (link cleared); deleting a material removes its history.

## Business Rules enforced around Purchases

* Purchases are record-only ledger entries — they cannot be edited or deleted, keeping the audit trail intact.
* The supplier must exist (HTTP 404); every material must exist and be active (404 / HTTP 409).
* Each material may appear on one line only; quantities must be > 0 (≤ 999999) and unit costs ≥ 0.
* All money values (`line_total`, `subtotal`, `total`) are calculated server-side from rounded inputs; the client cannot send totals.
* Purchase creation and inventory update behave as ONE logical database operation: a single commit writes the header, its lines, one `Stock In` movement per line and the updated stock levels — any failure rolls everything back.
* Every successful purchase writes a `Stock In` history row noting `Purchase PUR-xxxx`.
* `purchase_date` defaults to today when omitted; payment status starts as Unpaid (or Paid if recorded immediately) and can be toggled later via the API.
* Deleting a supplier keeps its purchases readable (`supplier_id` cleared, name snapshot retained).

---
*Last updated: Phase 10 completion (Purchase + PurchaseItem entities added).*
*Previous: Phase 8–9 completion (Suppliers + Inventory entities added).*
