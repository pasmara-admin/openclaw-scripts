# Database Schema & Guidelines - Prestashop

## Connection Details
- **Database:** produceshop
- **SSL Note:** If you get certificate errors, use `--skip-ssl-verify-server-cert`.
- **Command Template:** `mysql --skip-ssl-verify-server-cert -h 62.84.190.199 -u john -pqARa6aRozi6I produceshop -e "DESCRIBE ps_shop; SELECT id_shop, name FROM ps_shop LIMIT 10;"`
- **User:** john
- **Password:** qARa6aRozi6I
- **Type:** MySQL / MariaDB

## Scope & Usage (IMPORTANT)
Prestashop is the customer-facing frontend. Use this database **ONLY** for:
- Abandoned carts and checkout processes.
- Product catalog master data (as seen by customers).
- Frontend-specific configurations.

**DO NOT** use Prestashop for order processing, billing, or shipping data. For anything related to orders, marketplace sync, invoices, or revenue, use the **Kanguro ERP** database.

## Critical Rules for Queries
1. **SELECT & DESCRIBE ONLY:** You are strictly forbidden from executing any command other than `SELECT` or `DESCRIBE`. No `UPDATE`, `DELETE`, `INSERT`, or `ALTER`.
2. **DESCRIBE FIRST:** The database has many custom modifications. ALWAYS run `DESCRIBE [table_name]` before writing a `SELECT` query to verify column names.
3. **MANDATORY LIMITS:** Always use short `LIMIT` clauses (e.g., `LIMIT 10` or `LIMIT 50`). Never run unbounded selects as it may crash the session or impact DB performance.
4. **PERFORMANCE (BIG DATA):** The database is very large (several GBs). Be extremely careful with `JOIN` operations. Optimize your `WHERE` clauses to use indexed fields (like IDs) whenever possible.
5. **MULTILINGUAL & MULTISHOP:** Most tables require filtering by `id_shop` and `id_lang` (e.g., `ps_product_lang`).
   - **Default Shop:** 1 (Italia)
   - **Default Language:** 1 (Italiano)
   - If a specific shop or language is requested, or if you are unsure, query `ps_shop` and `ps_lang` first to identify the correct IDs.

## Mapping & Naming Conventions
- **SKU (Stock Keeping Unit):** Nel database di Prestashop, gli SKU sono memorizzati nella colonna chiamata **`reference`** (presente in tabelle come `ps_product`, `ps_product_attribute`, ecc.).
- **Numero Ordine:** Anche per gli ordini, il numero di riferimento visibile all'utente si trova nella colonna **`reference`** della tabella `ps_orders`.

## Key Tables for Reference (DESCRIBE first!)
- `ps_orders`: Orders data.
- `ps_product`: Core product data.
- `ps_product_lang`: Multilingual product names/descriptions.
- `ps_customer`: Customer information.
