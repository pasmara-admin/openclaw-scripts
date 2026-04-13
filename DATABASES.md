# DATABASES.md - Database Infrastructure & Guidelines

## Database Mapping & Sources of Truth
- **Wallaby:** The primary source for **Pre-Sale** and catalog management. Use for restructured product data and catalog attributes.
- **Kanguro (ERP):** The "Source of Truth" for all **Post-Sale** operations. Use for orders, marketplace data, invoices, revenue, shipping, and purchases.
- **PrestaShop:** Use **only** for abandoned carts, checkout data, and frontend customer info. The PrestaShop backoffice is NOT used.
- **Numbat:** Handles customer support and ticketing (Zoho Desk integration).
- **Pricer:** Database simulatore di prezzi. Integra dati da Kanguro (volumi/pesi) e Wallaby (media) per simulare prezzi di uscita basati su costi e parametri configurabili.
- **Buyer & Crawler:** Dedicated server for scouting, supplier analysis, and large-scale competitor monitoring.

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
