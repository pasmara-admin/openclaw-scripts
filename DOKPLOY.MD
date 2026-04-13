# DOKPLOY.MD - Deployment & Infrastructure Management

## Overview
**Dokploy** è il nostro sistema centralizzato per il deployment automatico e l'orchestrazione di infrastrutture basate su Docker. Gestisce l'intero ciclo di vita del software (tranne PrestaShop), inclusi:
- Deployment automatici (CI/CD) collegati a GitHub.
- Gestione container e database.
- Orchestrazione di server remoti (VPS) dedicati ai singoli progetti.
- Routing via Traefik, gestione backup e analisi log.

## Role of John
John utilizza Dokploy per monitorare lo stato dell'infrastruttura su richiesta. I compiti principali includono:
- **Analisi Deployment:** Verificare lo storico dei deployment e diagnosticare le cause di eventuali fallimenti.
- **Ispezione Log:** Estrarre e analizzare i log dei container per risolvere bug o anomalie operative.
- **Stato Risorse:** Monitorare la salute dei container associati ai progetti aziendali.

## Connection Details
- **URL:** `https://dokploy.produceshop.com`
- **User:** `john@produceshop.com`
- **Password:** `8wJbnkoQu7seW2p9Z7un`

## Usage Instructions
Per analizzare i log o i deployment, John deve:
1. Navigare su `dokploy.produceshop.com` utilizzando il profilo `openclaw`.
2. Effettuare il login (se la sessione non è già attiva).
3. Localizzare il progetto o il servizio specifico (es. Wallaby, Pricer, ecc.).
4. Estrarre i dati necessari tramite snapshot o ispezione del DOM.
