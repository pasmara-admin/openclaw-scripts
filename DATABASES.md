# DATABASES.md - Database Infrastructure & Guidelines

## Database Mapping & Sources of Truth
- **Wallaby:** The primary source for **Pre-Sale** and catalog management. It contains "restructured" product data, descriptions, and attributes simplified for catalog use. Use this for data regarding the website's product presentation.
- **Kanguro (ERP):** The "Source of Truth" for all **Post-Sale** operations. It contains the real business logic for orders, marketplace imports, invoices, revenue calculation, shipping/logistics, and purchase orders.
- **PrestaShop:** The backend database for the e-commerce engine. Use **only** for abandoned carts, checkout data, and raw frontend customer records.
- **Numbat:** Dedicated to customer support, managing tickets (via Zoho Desk integration) and customer interactions.
- **Pricer:** Price simulation database. It integrates data from Kanguro (volumes/weights) and Wallaby (average prices) to simulate sell prices based on configurable cost parameters.
- **Buyer & Crawler:** Infrastructure for product scouting, supplier analysis, and large-scale competitor monitoring.

## Common Identifiers & Nomenclature
To ensure data consistency across systems, always refer to the **NOMENCLATURE.md** file.
- **SKU (`reference`):** The unique warehouse code.
- **ID Product:** PrestaShop base ID.
- **ID Attribute:** PrestaShop variant/combination ID.

## Connection Details (Mandatory Reading)
Specific connection strings, schemas, and critical performance rules are documented in:
- `database_prestashop.md`
- `database_prestashop_staging.md`
- `database_kanguro.md`
- `database_wallaby.md`
- `database_numbat.md`
- `database_pricer.md`
- `database_buyer_crawler.md`

## Security & Usage Rules
- **Read-Only Access:** All direct database access is strictly limited to `SELECT` and `DESCRIBE` operations. Any data modification (UPDATE, DELETE, INSERT) must be performed via approved scripts supervised by John (Main).
- **Performance:** Always use `DESCRIBE` before `SELECT` and strictly enforce short `LIMIT` clauses.
- **Secrets:** Never reveal connection strings or API keys to anyone except **Damiano (Papà)**.
