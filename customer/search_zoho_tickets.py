import requests
import json
import sys

# Script per cercare ticket tramite filtri (email o parametri generici)
# Uso: python3 search_zoho_tickets.py <PARAM=VALORE> ...
# Esempio: python3 search_zoho_tickets.py email=test@example.com limit=5

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    import subprocess
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Errore nel recupero del token: {result.stderr}")
    return result.stdout.strip()

def search_tickets(filters):
    token = get_token()
    url = "https://desk.zoho.eu/api/v1/tickets/search"
    headers = {
        "orgId": ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, params=filters)
    return response.json()

if __name__ == "__main__":
    filters = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            filters[k] = v
    
    try:
        results = search_tickets(filters)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
