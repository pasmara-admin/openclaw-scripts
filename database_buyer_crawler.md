# database_buyer_crawler.md - Database Buyer & Crawler

## Descrizione
Questo server ospita i database relativi al progetto **Buyer** e al sistema di **Crawler** (Price/Product monitoring).

## Database Presenti
- **buyer**: Gestione delle logiche di scouting, fornitori e analisi buyer.
- **crawler**: Gestione dei task di crawling, code e dati estratti dai competitor.

## Credenziali di Accesso (MySQL)
- **Host:** `185.182.185.94`
- **User:** `john`
- **Password:** `4oJI5261ce3O`
- **Porta:** `3306` (default)

## Linee Guida
- **Sola Lettura:** Operazioni `SELECT` e `DESCRIBE` consentite.
- **Aggiornamenti:** Modifiche solo tramite script autorizzati.
- **Performance:** Usare `LIMIT` e verificare gli indici per query su tabelle di crawling massive.
