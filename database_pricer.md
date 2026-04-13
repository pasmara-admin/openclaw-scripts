# database_pricer.md - Pricer Simulator Database

## Overview
Il database **Pricer** funge da simulatore di prezzi avanzato per Pasmara Srl. Integra dati provenienti da diverse fonti per calcolare e simulare il prezzo di vendita ottimale (prezzo di uscita consigliato) basandosi su molteplici parametri di costo.

## Data Integration Flow
- **Inbound Data (via Cron):**
    - **Kanguro (ERP):** Dati logistici (volume, peso).
    - **Wallaby (Catalog):** Asset multimediali e riferimenti (immagini, link prodotto).
- **Internal Logic:**
    - Gestione parametri di configurazione (costi inbound, prezzo acquisto, costi spedizione, ecc.) salvati in tabelle locali.
    - Algoritmo di simulazione per il calcolo del prezzo di uscita.

## Connection Details
- **Host:** `5.189.187.113`
- **User:** `john`
- **Password:** `fa7oGi1oyInI`
- **Permissions:** `SELECT` (Read-only access for John).

## Usage Rules
- Utilizzare questo DB per analisi di marginalità e simulazioni di pricing richieste dai dipartimenti Buyer o Finance.
- Verificare sempre i parametri di configurazione locali prima di generare report di simulazione.
