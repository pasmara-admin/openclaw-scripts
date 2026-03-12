import time
import re
from urllib.parse import urlparse
from markdownify import markdownify
from camoufox.sync_api import Camoufox
from camoufox import DefaultAddons

def get_proxy_dict(proxy_url: str):
    p = urlparse(proxy_url)
    return {"server": f"{p.scheme}://{p.hostname}:{p.port}", "username": p.username, "password": p.password}

def prepare_page(page):
    """Esegue la chiusura dei cookie, scroll e attese per il rendering."""
    page.wait_for_load_state("domcontentloaded")
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

PROXY_URL = "http://brd-customer-hl_0961e0e1-zone-datacenter_proxy1:1b6tz37u6l8k@brd.superproxy.io:33335"
TARGET_URL = "https://produceshop.it/sedie-da-interno-grand-soleil/sedie-cucina-bar-gruvyer-in-polipropilene-impilabili-grand-soleil"

with Camoufox(
    proxy=get_proxy_dict(PROXY_URL), 
    config=custom_config, 
    i_know_what_im_doing=True, 
    headless=True, 
    os="linux", 
    geoip=True
) as browser:
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(TARGET_URL)
    
    prepare_page(page)
    
    screenshot_path = "/root/.openclaw/workspace-finance/screenshot_gruvyer.png"
    page.screenshot(path=screenshot_path, full_page=True)
    
    print(f"DONE. Screenshot: {screenshot_path}")