# Database Schema & Guidelines - Prestashop Staging / Dev

## Connection Details
- **Host:** 167.86.122.122
- **Port:** 3306
- **User:** john
- **Password:** S36e8O4a
- **Type:** MySQL / MariaDB

## Scope & Usage
This is the **Staging / Dev** environment for Prestashop. Use it for:
- Testing new scripts or queries.
- Verifying data migrations.
- Comparing data with production.

## System Context
Mirror of the production database used for development and staging purposes.

## Critical Rules for Queries (HIGH RISK - NOT READ-ONLY)
1. **SELECT & DESCRIBE ONLY BY DEFAULT:** Strictly no write operations (`UPDATE`, `DELETE`, `INSERT`, `CREATE`, `DROP`, etc.) unless explicitly requested by **Damiano (Papà)**.
2. **USER PERMISSIONS:** Be aware that this database user has **WRITE** permissions. A mistake here can corrupt the staging data. Always double-check your SQL before executing.
3. **DESCRIBE FIRST:** Always verify schema before querying.
4. **MANDATORY LIMITS:** Use `LIMIT 10` or `LIMIT 50` for exploration.
5. **SSL Note:** If you get certificate errors, use `--skip-ssl-verify-server-cert`.
