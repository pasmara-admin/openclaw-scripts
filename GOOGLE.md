# GOOGLE.md - Google Workspace Integration

Questo file descrive la procedura di configurazione e le regole di comportamento per l'integrazione con Google Workspace (Gmail e Calendar).

## 1. Configurazione e Rinnovo Connessione

La connessione viene gestita tramite il CLI `gog`. In caso di scadenza del token o necessità di nuova autorizzazione, seguire questo flow:

### Prerequisiti
- `credentials.json` configurato in `/root/.config/gogcli/credentials.json`.
- Keyring configurato in modalità `file` per l'uso non interattivo (password: `produceshop`).

### Credenziali Google Ads
- **Developer Token:** `vGAyxT1jd8C_dUIT56bbDA`
- **Manager Account (MCC):** `538-576-2191`
- **ProduceShop IT:** `232-709-5345`

### Procedura di Login (Manuale)
...
4. Inviare l'URL incollato allo stdin del processo `gog` ancora attivo.

### Utilizzo negli Script e Agenti
Per utilizzare `gog` in script o sessioni non interattive, caricare l'ambiente condiviso:
`source /root/.openclaw/workspace-shared/setup_gog_env.sh`
Oppure impostare manualmente:
`export GOG_KEYRING_PASSWORD="produceshop"`
`export GOG_ACCOUNT="admin@produceshoptech.com"`

---

## 2. Regole Gmail

Quando viene richiesto di gestire le email per `admin@produceshoptech.com`:

### Lettura e Ricerca
- **Mai assumere:** Quando vengono richieste informazioni sulle email, effettuare sempre una richiesta manuale in tempo reale tramite `gog gmail messages search` per recuperare gli ultimi dati dall'inbox.

### Invio Email
- **Firma Obbligatoria:** Ogni email inviata deve terminare con la firma dell'agente che sta operando.
  - Esempio (Main): `John`
  - Esempio (Finance): `John Finance`
- **Conferma:** Prima di inviare un'email, mostrare sempre una bozza all'utente e attendere conferma esplicita.

---

## 3. Regole Calendar

L'integrazione con il calendario serve a garantire la persistenza dei promemoria oltre la sessione chat.

- **Sincronizzazione:** Quando un utente chiede di memorizzare un impegno, un appuntamento o un promemoria, l'agente deve **sempre** crearlo anche su Google Calendar (calendarId: `primary`).
- **Trasparenza:** Una volta creato l'evento, palesare esplicitamente all'utente di averlo aggiunto al calendario (es: "Promemoria salvato anche sul tuo Google Calendar").
