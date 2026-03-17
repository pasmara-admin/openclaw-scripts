# database_wallaby.md - Database Wallaby (Pre-Sale & Catalog Management)

## Descrizione
**Wallaby** è il gestionale interno utilizzato per le anagrafiche prodotti e i processi di pre-vendita. Si sincronizza automaticamente con PrestaShop e funge da interfaccia principale per la gestione del catalogo, superando i limiti del backoffice di PrestaShop.

## Logica di Utilizzo
- **Pre-Sale & Catalogo:** Usare Wallaby come fonte primaria per anagrafiche prodotti, descrizioni e dati strutturati per il catalogo.
- **Dati Integrati:** Contiene dati "ristrutturati" e semplificati rispetto a PrestaShop, arricchiti con informazioni aziendali aggiuntive.
- **Relazione con PrestaShop:** Consultare PrestaShop **solo** se esplicitamente richiesto o per dati specifici su carrelli e customers.
- **Flusso Aziendale:**
    - **Wallaby:** Pre-Sale e Gestione Catalogo.
    - **Kanguro:** Post-Sale (Ordini, Logistica, Fatturazione).

## Credenziali di Accesso (MySQL)
- **Host:** `161.97.132.28`
- **User:** `john`
- **Password:** `6uxA8iwIsA5e`
- **Porta:** `3306` (default)

## Linee Guida per le Query
- **Sola Lettura:** Tutte le operazioni devono essere rigorosamente in sola lettura (`SELECT`).
- **Performance:** Utilizzare sempre `LIMIT` per evitare il caricamento di troppi dati.
- **Esplorazione:** Usare `DESCRIBE [tabella]` prima di eseguire query complesse per comprendere la struttura dei dati arricchiti.
