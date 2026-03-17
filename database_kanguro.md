# Database Schema & Guidelines - Kanguro (ERP)

## Connection Details
- **Host:** 34.38.166.212
- **Database:** kanguro
- **User:** john
- **Password:** 3rmiCyf6d~MZDO41
- **Type:** MySQL / MariaDB

## Scope & Usage (IMPORTANT)
Kanguro is the central source of truth for post-checkout operations. Use this database for **ALL** queries regarding:
- **Orders:** Statuses, history, and modifications.
- **Finance & Revenue:** Totals, payments, and billing/invoices.
- **Logistics:** Shipping, tracking, and carrier management.
- **Marketplaces:** Data from external sales channels.
- **Purchases:** Supplier orders and stock arrivals.

If a request asks for order info, revenue, or invoices, **always** use Kanguro, not Prestashop.

## System Context
Kanguro is the internal ERP that manages the lifecycle of orders after they are imported from Prestashop (every 20 minutes). It handles order statuses, totals, modifications, billing, and logistics.

### Product Mapping (Prestashop vs. Kanguro)
In Kanguro, every product entry represents a specific variant (combination) from Prestashop.
- **Prestashop:** 1 `id_product` with 10 `id_product_attribute` (combinations).
- **Kanguro:** 10 distinct rows in `dat_product`.
- **Mapping fields:**
  - `external_reference` -> Prestashop `id_product`
  - `external_attribute_reference` -> Prestashop `id_product_attribute`

## Table Naming Conventions (Prefixes)
Tables are organized by macro-areas:
- `sal_`: Sales (Orders, sales data)
- `dat_`: Master data (Product registry, entities)
- `bil_`: Billing (Invoices, payments)
- `lgs_`: Logistics (Shipping, carriers)
- `pch_`: Purchases (Procurement, stock arrival)
- `ret_`: Returns (RMA, credit notes)
- `fun_`: Funnel (New product onboarding/entry)
- `acc_`: Accounts (Users, permissions)

## Critical Rules for Queries
1. **SELECT & DESCRIBE ONLY:** Strictly no write operations (`UPDATE`, `DELETE`, `INSERT`, etc.).
2. **DESCRIBE FIRST:** Always verify schema before querying.
3. **MANDATORY LIMITS:** Use `LIMIT 10` or `LIMIT 50` for exploration.
4. **PERFORMANCE:** The ERP database is business-critical. Avoid heavy joins without proper indexing.
5. **LOGGING:** Append the exact SQL query to `.openclaw/query_history.log`.
