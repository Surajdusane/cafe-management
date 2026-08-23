# AGENTS.md

# Cafe Management System

## use this foolowing skill as per requirement
- .agents\skills\fastapi-python
- .agents\skills\frontend-design
- .agents\skills\uv-package-manager

# very important use python uv package manager

## BCA / BBA Computer Application Final Year Project

You are the primary software development agent for a **Cafe Management System** created as an academic final-year project.

Your responsibility is to build the complete project **incrementally, feature-by-feature**, while maintaining clean code, a simple architecture, proper validation, documentation, testing, and academic project requirements.

Do NOT attempt to generate the entire project in one step.

The project must remain understandable enough for a final-year student to explain during project demonstration and viva.

---

# 1. Project Objective

Build a modern but simple **Cafe Management System** for managing the daily operations of a small or medium-sized cafe.

The system should reduce manual paperwork and provide centralized management for:

* Cafe menu
* Customer-facing digital menu
* Orders
* Billing
* Raw materials / inventory
* Suppliers
* Purchases
* Employees
* Employee salaries
* Expenses
* Basic reports
* Dashboard
* Cafe settings

The project must be realistic but **not unnecessarily complicated**.

Avoid enterprise-level architecture, microservices, cloud infrastructure, Kubernetes, Redis, message queues, or other technologies that are unnecessary for an academic project.

---

# 2. Required Technology Stack

## Backend

Use:

* Python
* FastAPI
* SQLite
* SQLAlchemy
* Pydantic
* Uvicorn

SQLite must be used as the primary database.

The database should initially be a local single-file SQLite database:

```text
data/cafe.db
```

Do not introduce PostgreSQL, MySQL, MongoDB, Firebase, or cloud databases unless explicitly requested later.

---

# 3. Frontend

Use only:

* HTML
* CSS
* Vanilla JavaScript

Do NOT use:

* React
* Vue
* Angular
* Next.js
* Bootstrap
* Tailwind
* jQuery

The frontend must communicate with FastAPI through REST APIs.

The UI should be modern, responsive, clean, and suitable for desktop/tablet use.

The customer-facing digital menu must also work well on mobile.

---

# 4. Project Architecture

Use a simple modular architecture.

Recommended structure:

```text
cafe-management-system/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── category.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   ├── inventory.py
│   │   ├── supplier.py
│   │   ├── purchase.py
│   │   ├── employee.py
│   │   ├── salary.py
│   │   └── expense.py
│   │
│   ├── schemas/
│   │   ├── category.py
│   │   ├── menu_item.py
│   │   ├── order.py
│   │   ├── inventory.py
│   │   ├── supplier.py
│   │   ├── purchase.py
│   │   ├── employee.py
│   │   ├── salary.py
│   │   └── expense.py
│   │
│   ├── routers/
│   │   ├── dashboard.py
│   │   ├── categories.py
│   │   ├── menu.py
│   │   ├── orders.py
│   │   ├── billing.py
│   │   ├── inventory.py
│   │   ├── suppliers.py
│   │   ├── purchases.py
│   │   ├── employees.py
│   │   ├── salaries.py
│   │   ├── expenses.py
│   │   └── reports.py
│   │
│   ├── services/
│   │   ├── order_service.py
│   │   ├── inventory_service.py
│   │   ├── billing_service.py
│   │   └── report_service.py
│   │
│   └── templates/
│       ├── index.html
│       ├── menu.html
│       ├── orders.html
│       ├── billing.html
│       ├── inventory.html
│       ├── suppliers.html
│       ├── purchases.html
│       ├── employees.html
│       ├── salaries.html
│       ├── expenses.html
│       ├── reports.html
│       └── settings.html
│
├── static/
│   ├── css/
│   │   ├── main.css
│   │   ├── dashboard.css
│   │   └── responsive.css
│   │
│   ├── js/
│   │   ├── api.js
│   │   ├── validation.js
│   │   ├── dashboard.js
│   │   ├── menu.js
│   │   ├── orders.js
│   │   ├── billing.js
│   │   ├── inventory.js
│   │   ├── employees.js
│   │   ├── reports.js
│   │   └── common.js
│   │
│   └── images/
│
├── data/
│   └── cafe.db
│
├── tests/
│   ├── test_menu.py
│   ├── test_orders.py
│   ├── test_billing.py
│   ├── test_inventory.py
│   └── test_employees.py
│
├── docs/
│   ├── ERD.md
│   ├── DFD.md
│   ├── DATA_DICTIONARY.md
│   └── API_DOCUMENTATION.md
│
├── document.md
├── AGENTS.md
├── requirements.txt
├── README.md
└── .gitignore
```

You may adjust the folder structure when necessary, but keep it simple and modular.

---

# 5. Development Principles

Always follow these principles:

1. Build one feature at a time.
2. Complete the backend before connecting the frontend for that feature.
3. Add database models before APIs.
4. Add API validation before frontend integration.
5. Add client-side validation as well.
6. Test each feature after implementation.
7. Update documentation after completing each feature.
8. Do not break previously completed features.
9. Reuse common components and utility functions.
10. Keep code readable for a student-level developer.
11. Do not over-engineer.
12. Use meaningful names.
13. Add comments only where they improve understanding.

---

# 6. Validation Requirements

Every form must have:

## Client-side validation

Use JavaScript validation for:

* Required fields
* Minimum/maximum length
* Number validation
* Decimal validation
* Positive values
* Mobile number format
* Email format where applicable
* Date validation
* Duplicate item checks where applicable
* Invalid quantity checks

Display useful inline validation messages.

Do not rely only on browser HTML validation.

---

## Server-side validation

FastAPI/Pydantic validation must independently validate every request.

Never trust frontend validation.

The server must validate:

* Required fields
* Data types
* Value ranges
* Positive quantities
* Valid prices
* Valid dates
* Valid foreign keys
* Duplicate records
* Business rules

Example:

A menu item price cannot be negative.

Inventory quantity cannot be negative.

Employee salary cannot be negative.

Order quantity must be greater than zero.

---

# 7. Security and Safety Rules

Even though this is an academic local application:

* Never trust client input.
* Never construct SQL using raw user input.
* Use SQLAlchemy queries.
* Validate all API inputs.
* Sanitize displayed user-generated data.
* Do not expose database internals to the frontend.
* Do not store unnecessary sensitive information.
* Use proper HTTP status codes.
* Return useful API errors.

Authentication may be kept simple.

A basic local admin/staff login can be implemented later if appropriate, but do not introduce a complicated authentication system.

---

# 8. Main Application Modules

The application must contain the following major sections.

## Dashboard

Display:

* Today's sales
* Today's orders
* Total menu items
* Low-stock items
* Pending purchases
* Employee count
* Monthly expenses
* Simple sales chart
* Recent orders

The dashboard should be visually attractive but simple.

---

# 9. Cafe Menu Management

Admin must be able to:

* Create category
* Edit category
* Delete category
* Create menu item
* Edit menu item
* Delete menu item
* Enable/disable menu item
* Set price
* Add description
* Add image
* Set category
* Mark item as vegetarian/non-vegetarian where relevant
* Mark item as popular
* Set availability

Menu categories may include:

* Coffee
* Tea
* Cold Drinks
* Snacks
* Breakfast
* Main Course
* Desserts

These should remain configurable.

---

# 10. Customer Digital Menu

Create a public customer-facing menu.

The cafe staff should be able to generate/share a menu link.

Example:

```text
/menu/cafe
```

The customer should see:

* Cafe name
* Cafe logo
* Categories
* Menu item images
* Item names
* Descriptions
* Prices
* Availability
* Popular items

The public menu should not expose administration features.

The UI must be mobile-friendly.

Do not implement online payment initially.

---

# 11. Order Management

The staff should be able to create orders.

Order information:

* Order number
* Date/time
* Table number or takeaway
* Items
* Quantity
* Unit price
* Discount
* Tax
* Total
* Payment status
* Order status

Order statuses:

```text
Pending
Preparing
Ready
Completed
Cancelled
```

Support:

* Dine-in
* Takeaway

Keep the workflow simple.

---

# 12. Billing

Billing must include:

* Automatic bill number
* Order details
* Item quantity
* Item price
* Subtotal
* Discount
* Tax
* Grand total
* Payment method
* Payment status
* Date/time

Payment methods:

```text
Cash
UPI
Card
Other
```

The system should calculate totals on the server.

The frontend may calculate totals for UX, but the backend remains the source of truth.

Provide a printable bill/receipt page.

Do not implement real payment gateway integration.

---

# 13. Raw Material / Inventory Management

Manage raw materials used by the cafe.

Example:

```text
Milk
Coffee Beans
Tea Powder
Sugar
Flour
Cheese
Bread
Cooking Oil
Chocolate
Vegetables
```

Each inventory item should contain:

* ID
* Name
* Category
* Unit
* Current quantity
* Minimum stock level
* Purchase price
* Supplier
* Status

Units may include:

```text
Kg
Gram
Litre
Millilitre
Piece
Packet
Box
```

Features:

* Add stock
* Reduce stock
* Edit item
* Delete item
* View stock
* Low-stock warning
* Inventory history

Do not implement an excessively complicated warehouse system.

---

# 14. Purchase Management

Allow staff to record purchases from suppliers.

Purchase information:

* Purchase number
* Supplier
* Date
* Raw material
* Quantity
* Unit cost
* Total cost
* Payment status
* Notes

When a purchase is recorded:

```text
inventory quantity = inventory quantity + purchased quantity
```

---

# 15. Supplier Management

Supplier fields:

* Supplier ID
* Supplier name
* Contact person
* Mobile number
* Email
* Address
* Material supplied
* Status

Features:

* Add supplier
* Edit supplier
* Delete supplier
* Search supplier
* View supplier purchases

---

# 16. Employee Management

Employee information:

* Employee ID
* Name
* Mobile
* Email
* Address
* Role
* Joining date
* Salary type
* Base salary
* Status

Roles may include:

```text
Manager
Cashier
Chef
Waiter
Helper
Cleaner
```

Salary type:

```text
Monthly
Daily
Hourly
```

---

# 17. Employee Salary Management

Record salary payments.

Fields:

* Employee
* Salary month
* Base salary
* Bonus
* Deduction
* Net salary
* Payment date
* Payment status
* Notes

Formula:

```text
Net Salary =
Base Salary + Bonus - Deduction
```

Provide salary history.

---

# 18. Expense Management

Add a simple expense management module.

Examples:

* Electricity
* Gas
* Rent
* Maintenance
* Cleaning
* Internet
* Miscellaneous

Fields:

* Expense title
* Category
* Amount
* Date
* Payment method
* Notes

Reports should show expenses by date/category.

---

# 19. Reports

Add simple reports.

Required reports:

### Sales Report

* Daily sales
* Weekly sales
* Monthly sales

### Order Report

* Orders by date
* Order status

### Inventory Report

* Current stock
* Low stock
* Stock movement

### Purchase Report

* Purchases by supplier
* Purchases by date

### Salary Report

* Monthly salary expenses

### Expense Report

* Expenses by category
* Expenses by date

### Profit Summary

Provide a simple estimated summary:

```text
Sales
- Purchases
- Salaries
- Expenses
= Estimated Profit
```

Clearly label this as an estimated business summary.

---

# 20. Search and Filtering

Where useful, provide:

* Search
* Date filters
* Category filter
* Status filter
* Supplier filter
* Employee filter

Do not add complex advanced filtering unnecessarily.

---

# 21. Dashboard Navigation

Use a sidebar layout:

```text
Dashboard
Menu
Customer Menu
Orders
Billing
Inventory
Purchases
Suppliers
Employees
Salaries
Expenses
Reports
Settings
```

The UI should have:

* Sidebar
* Top bar
* Breadcrumb/page title
* Cards
* Tables
* Modal forms
* Toast notifications
* Confirmation dialogs
* Empty states
* Loading states
* Error states

---

# 22. UI Design

The application should look modern.

Design characteristics:

* Clean dashboard
* Soft shadows
* Rounded cards
* Good spacing
* Modern typography
* Responsive tables
* Attractive buttons
* Status badges
* Consistent colors
* Light/dark-friendly architecture if practical

Do not make the UI look like an old college project.

Avoid excessive animations.

---

# 23. Database Design

Use relational SQLite database design.

Main entities should approximately include:

```text
Category
MenuItem
Order
OrderItem
InventoryItem
InventoryTransaction
Supplier
Purchase
PurchaseItem
Employee
Salary
Expense
CafeSetting
```

Use appropriate primary keys and foreign keys.

The database must maintain referential integrity.

Avoid unnecessary duplication.

---

# 24. Documentation Requirement

A file named:

```text
document.md
```

must always be maintained.

This document is the main project documentation.

The documentation should follow the academic case-study style from the provided reference material.

The project guide specifies sections such as:

* Company Profile
* System Analysis
* Requirement Analysis
* Design
* I/O Screens
* Reports
* Coding
* Software System Testing
* Implementation
* Bibliography

The documentation must gradually build these sections as development progresses.

Do not wait until the end to create documentation.

---

# 25. Documentation Update Rule

After completing every feature:

1. Update `document.md`.
2. Add the feature to the relevant chapter.
3. Update requirement lists.
4. Update database information.
5. Update data dictionary.
6. Update testing information.
7. Add relevant screenshots/placeholders where appropriate.
8. Add revision history.

Never erase previously documented information unless it is incorrect because of an intentional design change.

---

# 26. Required Design Documentation

Create and maintain:

```text
docs/ERD.md
docs/DFD.md
docs/DATA_DICTIONARY.md
docs/API_DOCUMENTATION.md
```

The academic reference specifically includes ERD, DFD and Data Dictionary as design components for TY BCA projects.

The documentation should contain:

## ERD

Represent:

* Entities
* Attributes
* Primary keys
* Foreign keys
* Relationships
* Cardinality

## DFD

Create:

* Context-level DFD
* Level-1 DFD

Where useful, create Level-2 diagrams for important workflows.

## Data Dictionary

For every major table include:

```text
Field Name
Data Type
Description
Primary Key
Foreign Key
Nullable
Example
```

---

# 27. Testing

Every completed module must be tested.

Testing should include:

* Functional testing
* Validation testing
* Black-box testing
* Basic white-box testing
* GUI testing
* Integration testing
* System testing

The supplied academic guide specifically discusses white-box, black-box, validation, GUI and system testing.

Every feature should include test cases such as:

| Test Case        | Input                | Expected Result | Status |
| ---------------- | -------------------- | --------------- | ------ |
| Valid data       | Correct values       | Record created  | Pass   |
| Missing field    | Empty required field | Error shown     | Pass   |
| Invalid number   | Negative value       | Error shown     | Pass   |
| Duplicate record | Existing value       | Error shown     | Pass   |

---

# 28. Academic Simplicity Rule

This is a final-year college project.

The project should demonstrate:

* Python programming
* FastAPI
* REST API
* SQLite
* Database design
* HTML/CSS/JavaScript
* Form validation
* CRUD operations
* Business logic
* Reports
* Testing
* SDLC
* System design

Do not add features simply because they sound advanced.

The final application must remain explainable during viva.

---

# 29. Development Workflow

Always follow this order for a new feature:

### Step 1 — Understand

Explain internally:

* What problem does this feature solve?
* Which database tables are required?
* Which API endpoints are required?
* Which frontend screens are required?
* Which validations are required?

### Step 2 — Database

Create/update:

* Model
* Relationships
* Database initialization

### Step 3 — Schema

Create Pydantic request/response schemas.

### Step 4 — Backend

Implement:

* CRUD
* Business logic
* Validation
* Error handling

### Step 5 — API

Create FastAPI routes.

### Step 6 — Frontend

Create:

* HTML
* CSS
* JavaScript
* API integration
* Loading states
* Error states

### Step 7 — Testing

Test:

* Valid input
* Invalid input
* Missing input
* Boundary cases
* API behavior
* Database behavior
* UI behavior

### Step 8 — Documentation

Immediately update:

```text
document.md
docs/ERD.md
docs/DFD.md
docs/DATA_DICTIONARY.md
docs/API_DOCUMENTATION.md
```

### Step 9 — Final Review

Check that the new feature does not break existing functionality.

---

# 30. Feature Development Order

Develop the application in the following order.

## Phase 1 — Project Foundation

Build:

* FastAPI application
* SQLite database
* SQLAlchemy setup
* Static files
* Base HTML layout
* Navigation
* Error handling
* Common API utilities
* Basic dashboard shell

Update documentation.

---

## Phase 2 — Cafe Settings

Build:

* Cafe name
* Address
* Phone
* Email
* Logo
* Tax percentage
* Currency
* Receipt information

Update documentation.

---

## Phase 3 — Menu Categories

Build complete category CRUD.

Update documentation.

---

## Phase 4 — Menu Items

Build complete menu item CRUD.

Add:

* Images
* Price
* Category
* Availability
* Description
* Popular flag

Update documentation.

---

## Phase 5 — Customer Digital Menu

Build public menu page.

Allow staff to share the public menu URL.

Update documentation.

---

## Phase 6 — Orders

Build:

* Order creation
* Order items
* Quantity
* Table/takeaway
* Order status
* Order history

Update documentation.

---

## Phase 7 — Billing

Build:

* Automatic bill calculation
* Tax
* Discount
* Payment method
* Receipt
* Print bill

Update documentation.

---

## Phase 8 — Suppliers

Build supplier CRUD.

Update documentation.

---

## Phase 9 — Inventory

Build:

* Raw materials
* Stock
* Low stock
* Stock transactions

Update documentation.

---

## Phase 10 — Purchases

Build purchase management.

Update inventory automatically after successful purchase.

Update documentation.

---

## Phase 11 — Employees

Build employee management.

Update documentation.

---

## Phase 12 — Salaries

Build salary management.

Update documentation.

---

## Phase 13 — Expenses

Build expense management.

Update documentation.

---

## Phase 14 — Reports

Build all basic reports.

Update documentation.

---

## Phase 15 — Dashboard

Connect dashboard statistics to real data.

Update documentation.

---

## Phase 16 — Testing

Perform complete system testing.

Add detailed test cases.

Update documentation.

---

## Phase 17 — Final Documentation

Complete:

* Company Profile
* System Analysis
* Requirement Analysis
* Design
* ERD
* DFD
* Data Dictionary
* I/O Screens
* Reports
* Coding
* Testing
* Implementation
* Limitations
* Future Enhancements
* Bibliography
* Glossary
* Revision History

---

# 31. How You Must Respond to Feature Requests

When the user gives you a feature request:

### First

Determine which project phase the feature belongs to.

### Then

Implement only the requested feature and its necessary dependencies.

### Never

Rewrite the entire project unnecessarily.

### Always

Preserve previously implemented functionality.

### After implementation

Report:

```text
Feature Completed
Files Added
Files Modified
Database Changes
API Endpoints Added
Frontend Screens Added
Validation Added
Tests Added
Documentation Updated
```

---

# 32. document.md Update Format

Maintain the documentation in an academic style.

Use sections such as:

```text
# Cafe Management System

## Chapter 1 — Company Profile

## Chapter 2 — System Analysis

### Study of Present System

### Problems in Present System

### Introduction to Proposed System

### Scope of Proposed System

### Benefits of Proposed System

## Chapter 3 — Requirement Analysis

### Functional Requirements

### Non-Functional Requirements

### Feasibility Study

### Hardware Requirements

### Software Requirements

## Chapter 4 — System Design

### ER Diagram

### Data Flow Diagram

### Data Dictionary

## Chapter 5 — I/O Screens

## Chapter 6 — Reports

## Chapter 7 — Coding

## Chapter 8 — Software System Testing

## Chapter 9 — Implementation

### Installation

### User Training

### User Manual

### Limitations

### Future Enhancements

## Chapter 10 — Bibliography
```

Also maintain:

```text
## Glossary

## Revision History
```

---

# 33. Revision History

Every meaningful change to documentation should update:

| Version | Date       | Change                        |
| ------- | ---------- | ----------------------------- |
| 1.0     | YYYY-MM-DD | Initial project documentation |
| 1.1     | YYYY-MM-DD | Added menu management         |
| 1.2     | YYYY-MM-DD | Added order management        |

---

# 34. Future Enhancement Suggestions

Potential future enhancements may include:

* QR-based customer menu
* Customer online ordering
* Online payment
* Multiple cafe branches
* Role-based authentication
* Cloud database
* WhatsApp order notifications
* Advanced analytics
* GST invoice support
* Supplier payment tracking

Do not implement these unless specifically requested.

They may be documented under **Future Enhancements**.

---

# 35. Important Academic Rule

Do not falsely claim that a feature was implemented if it was not.

Do not create imaginary screenshots, test results, database records, users, or business information.

Clearly differentiate:

```text
Implemented
Planned
Future Enhancement
```

---

# 36. Final Project Quality Standard

Before considering the project complete, verify:

* Application runs successfully.
* SQLite database works.
* All CRUD modules work.
* Backend validation works.
* Frontend validation works.
* Error handling works.
* Billing calculations are correct.
* Inventory updates correctly.
* Purchase records affect inventory.
* Salary calculations are correct.
* Reports display correct data.
* Customer menu is accessible publicly.
* Responsive UI works.
* Tests exist.
* Documentation is complete.
* ERD is updated.
* DFD is updated.
* Data Dictionary is updated.
* API documentation is updated.
* README is updated.

The final project must be simple enough to explain in a college viva but complete enough to demonstrate a real-world Cafe Management System.

# END OF AGENTS.MD
