import requests
import subprocess
import json

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    return result.stdout.strip()

if __name__ == "__main__":
    token = get_token()
    headers = {"orgId": ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    url = "https://desk.zoho.eu/api/v1/tickets"
    # Proviamo ad interrogare il range DESC (sortBy=-createdTime) con offset crescenti.
    # ma variando i criteri di ricerca per data se supportati in qualche modo oscuro
    # o provando a cercare threadID specifici se sequenziali (poco probabile).
    
    # Tentativo finale: cerchiamo per subject con una stringa comune
    # e vediamo se troviamo il 20 Ottobre.
    url = "https://desk.zoho.eu/api/v1/tickets/search"
    params = {"subject": "newsletter", "sortBy": "-createdTime", "limit": 100}
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        data = res.json()
        if 'data' in data:
            for t in data['data']:
                if "2025-10-20" in t['createdTime']:
                    print(f"FOUND: {t['ticketNumber']} ({t['createdTime']})")
