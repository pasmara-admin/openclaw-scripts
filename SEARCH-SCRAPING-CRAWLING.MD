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

### 1.2 Ricerca Shopping (Google Shopping)
**Endpoint:** `https://google.serper.dev/shopping`
```bash
curl --request POST 'https://google.serper.dev/shopping' --header 'X-API-KEY: 42c660df02d4e6df57b51db70e60e9fd7d00bb47' --header 'Content-Type: application/json' --data-raw '{"q": "ean_o_query", "gl": "it", "hl": "it"}'
```

---

## 2. Scraping & Crawling (Camoufox)

Utilizziamo **Camoufox** (Firefox-based) con proxy a rotazione per navigare e scaricare dati.

### 2.1 Configurazione Proxy
*   **Datacenter:** `http://brd-customer-hl_0961e0e1-zone-datacenter_proxy1:1b6tz37u6l8k@brd.superproxy.io:33335`
*   **Residential:** `http://brd-customer-hl_0961e0e1-zone-isp_proxy1:mif49o9yl6v0@brd.superproxy.io:33335`

### 2.2 Best Practices per il Rendering & Viewport
Per garantire un rendering consistente (Desktop 1920x1080) e triggerare tutti i contenuti dinamici:

1.  **Forzare la risoluzione nel `config`**: Camoufox randomizza le dimensioni per evitare il fingerprinting. Per avere un 1920x1080 reale, bisogna forzare i parametri `window.*` e `screen.*` nel dizionario `config` e passare `i_know_what_im_doing=True`.
2.  Attendere `domcontentloaded`.
3.  Chiudere i banner dei cookie.
4.  Scrollare fino a fondo pagina e tornare in cima.
5.  Attendere un cooldown di 500ms.
6.  **Verifica Blocchi (WAF/404):** Basarsi ESCLUSIVAMENTE sull'HTTP Response Code. Controllare sempre l'oggetto `response` restituito da `page.goto()`. Se lo status code non è 200 (es. 403 Forbidden, 404 Not Found, 429 Too Many Requests, 503 Service Unavailable), segnalarlo nell'output e valutare il cambio di proxy (es. da Datacenter a Residential) o il fallback API. NON usare controlli su stringhe nel DOM per rilevare WAF.

---

## 3. Fallback: Bright Data Scraping API

Se Camoufox viene costantemente bloccato nonostante l'uso di proxy residenziali, utilizzare la **Scraping API** di Bright Data come fallback estremo. Questa API gestisce automaticamente browser, sblocco e proxy.

### 3.1 Limitazioni Screenshot
⚠️ **Importante:** Quando si utilizza la Scraping API (fallback), **non è possibile generare screenshot**. 
Se l'utente richiede uno screenshot ma la pagina fallisce tramite browser (Camoufox) e richiede il fallback API, l'agente deve:
1. Informare l'utente che lo screenshot non è disponibile per questa modalità di accesso.
2. Restituire esclusivamente i dati strutturati o il contenuto testuale (Markdown) della pagina.

- **API Token:** `98d4acac-6a05-4739-81c8-b1e79d738017`
- **Endpoint:** `https://api.brightdata.com/request`

### 3.1 Esempio Richiesta (cURL)
```bash
curl -H "Authorization: Bearer 98d4acac-6a05-4739-81c8-b1e79d738017" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://target-site.com", "zone": "web_unlocker1"}' \
     "https://api.brightdata.com/request"
```

### 3.2 Integrazione Python (Fallback)
```python
import requests

def fetch_with_brightdata_api(url):
    api_url = "https://api.brightdata.com/request"
    headers = {
        "Authorization": "Bearer 98d4acac-6a05-4739-81c8-b1e79d738017",
        "Content-Type": "application/json"
    }
    data = {
        "url": url,
        "zone": "web_unlocker1", # O altra zona configurata
        "format": "raw"
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.text
    else:
        print(f"BRIGHTDATA_API_ERROR: {response.status_code} - {response.text}")
        return None
```

---

## 2.3 Esempio Script Python (Full Flow con Verifica Status Code)

```python
import time
import re
import sys
from urllib.parse import urlparse
from markdownify import markdownify
from camoufox.sync_api import Camoufox
from camoufox import DefaultAddons

def get_proxy_dict(proxy_url: str):
    p = urlparse(proxy_url)
    return {"server": f"{p.scheme}://{p.hostname}:{p.port}", "username": p.username, "password": p.password}

def convert_to_markdown(html: str) -> str:
    md = markdownify(html, heading_style="ATX", autolinks=True, default_title=False)
    return re.sub(r"\n{3,}", "\n\n", md).strip()

def prepare_page(page):
    """Esegue la chiusura dei cookie, scroll e attese per il rendering."""
    page.wait_for_load_state("domcontentloaded")
    time.sleep(1) # Attesa minima post-load
    
    try:
        cookie_selectors = [
            "button:has-text('accetta')", "button:has-text('Accetta')", 
            "button:has-text('OK')", "button:has-text('Chiudi')",
            "#js-cookie-consent button", ".cookie-popup button"
        ]
        for selector in cookie_selectors:
            if page.locator(selector).is_visible():
                page.click(selector, timeout=2000)
                break
    except: pass
    
    # Scroll per triggerare lazy loading
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.5)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)

# Configurazione Viewport Desktop 1920x1080
custom_config = {
    'window.outerWidth': 1920, 'window.outerHeight': 1080,
    'window.innerWidth': 1920, 'window.innerHeight': 1080,
    'screen.width': 1920, 'screen.height': 1080,
    'screen.availWidth': 1920, 'screen.availHeight': 1080
}

PROXY_DC = "http://brd-customer-hl_0961e0e1-zone-datacenter_proxy1:1b6tz37u6l8k@brd.superproxy.io:33335"
TARGET_URL = "https://example.com/target-page"

with Camoufox(
    proxy=get_proxy_dict(PROXY_DC), 
    config=custom_config, 
    i_know_what_im_doing=True, 
    headless=True, 
    os="linux", 
    geoip=True
) as browser:
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    try:
        response = page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
        
        # CONTROLLO STRICT SULLO STATUS CODE
        if response is None or response.status != 200:
            status_code = response.status if response else "N/A"
            print(f"FAILED: Errore HTTP {status_code} rilevato. Fallback proxy o API necessario.")
            sys.exit(1)
            
        prepare_page(page)
        
        # Estrazione se HTTP 200
        html = page.content()
        markdown = convert_to_markdown(html)
        print("SUCCESS: Pagina acquisita correttamente.")
        
    except Exception as e:
        print(f"FAILED: Errore durante la navigazione: {str(e)}")
        sys.exit(1)
```