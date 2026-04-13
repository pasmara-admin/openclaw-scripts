# SEARCH-SCRAPING-CRAWLING.MD

Questo file descrive le procedure e gli script per la ricerca, lo scraping e il crawling dei dati.

## 1. Ricerca (Serper.dev)

Tutte le ricerche utilizzano l'API di **Serper.dev**.
- **API Key:** `42c660df02d4e6df57b51db70e60e9fd7d00bb47`
- **Default (Localizzazione):** Se non specificato diversamente, utilizzare sempre `gl: "it"` (Italia) e `hl: "it"` (Italiano).

### 1.1 Ricerca Standard (Google Search)
**Endpoint:** `https://google.serper.dev/search`
```bash
curl --request POST 'https://google.serper.dev/search' --header 'X-API-KEY: 42c660df02d4e6df57b51db70e60e9fd7d00bb47' --header 'Content-Type: application/json' --data-raw '{"q": "query", "gl": "it", "hl": "it"}'
```

---

## 2. Scraping & Crawling (Chromium + OpenClaw Profile)

Utilizziamo **Chromium** (Playwright) con il profilo persistente `openclaw` per mantenere le sessioni e i cookie.

### 2.1 Configurazione Proxy (Residential Only)
Per tutte le connessioni esterne è **obbligatorio** utilizzare esclusivamente il proxy residenziale di Bright Data.
*   **Residential:** `http://brd-customer-hl_0961e0e1-zone-isp_proxy1:mif49o9yl6v0@brd.superproxy.io:33335`

### 2.2 Best Practices per il Rendering & Viewport
Per garantire un rendering consistente (Desktop 1920x1080) e triggerare tutti i contenuti dinamici:

1.  **Profilo Persistente**: Utilizzare il tool `browser` con `profile: "openclaw"`.
2.  **Viewport**: Configurare sempre `width: 1920` e `height: 1080`.
3.  Attendere `domcontentloaded` o `load`.
4.  Chiudere i banner dei cookie se necessario.
5.  Scrollare fino a fondo pagina e tornare in cima per triggerare il lazy loading.
6.  **Verifica Blocchi (WAF/404):** Basarsi ESCLUSIVAMENTE sull'HTTP Response Code. Se lo status code non è 200 (es. 403 Forbidden, 404 Not Found, 429 Too Many Requests, 503 Service Unavailable), segnalarlo nell'output e valutare il fallback sulla Scraping API.

---

## 3. Fallback: Bright Data Scraping API

Se il browser viene costantemente bloccato nonostante l'uso di proxy residenziali, utilizzare la **Scraping API** di Bright Data come fallback estremo.

### 3.1 Limitazioni Screenshot
⚠️ **Importante:** Quando si utilizza la Scraping API (fallback), **non è possibile generare screenshot**. 

- **API Token:** `98d4acac-6a05-4739-81c8-b1e79d738017`
- **Endpoint:** `https://api.brightdata.com/request`

### 3.2 Esempio Richiesta (cURL)
```bash
curl -H "Authorization: Bearer 98d4acac-6a05-4739-81c8-b1e79d738017" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://target-site.com", "zone": "web_unlocker1"}' \
     "https://api.brightdata.com/request"
```

---

## 2.3 Esempio Interazione tramite Tool Browser (OpenClaw)

Per navigare correttamente, utilizzare il tool `browser` con la seguente logica:

```json
{
  "action": "navigate",
  "url": "https://example.com",
  "profile": "openclaw",
  "width": 1920,
  "height": 1080
}
```

E per analizzare la pagina:

```json
{
  "action": "snapshot",
  "refs": "aria",
  "profile": "openclaw"
}
```
