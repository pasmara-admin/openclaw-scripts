# database_numbat.md - Database Numbat (Customer Support & Ticketing)

## Descrizione
**Numbat** è il software proprietario di assistenza e supporto per i clienti di Produceshop (disponibile su support.produceshop.info). Permette ai clienti di consultare FAQ, gestire ordini, richiedere resi e aprire ticket di assistenza.

## Logica di Utilizzo
- **Supporto & Ticketing:** Utilizzare questo database per consultare lo stato dei ticket, le interazioni con i clienti e le richieste di reso.
- **Integrazione Zoho Desk:** I ticket vengono aperti su Zoho Desk tramite API. Numbat memorizza l'ID ticket di Zoho e altre metadati nelle tabelle `tickets` e `tickets_*`.
- **Dati Ordini/Prodotti:** Numbat **NON** contiene anagrafiche prodotti o dati storici sugli ordini. La web app legge questi dati in tempo reale da Kanguro (primario) e PrestaShop.
- **Relazioni:** Usare l'ID cliente o il riferimento ordine per incrociare i ticket di Numbat con i dati fiscali/logistici di Kanguro.

## Credenziali di Accesso (MySQL)
- **Host:** `62.169.25.209`
- **User:** `john`
- **Password:** `38CEXeHI2733`
- **Database:** `numbat`

## Linee Guida per le Query
- **Sola Lettura:** Tutte le operazioni devono essere in sola lettura (`SELECT`).
- **Focus:** Concentrarsi sulla tabella `tickets` per l'analisi del volume di supporto e delle tipologie di problematiche segnalate dai clienti.
