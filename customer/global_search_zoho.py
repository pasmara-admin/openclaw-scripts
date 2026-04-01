import requests
import json
import sys

# Script per la ricerca globale su Zoho Desk (modulo tickets)
# Uso: python3 global_search_zoho.py <TERMINE_DI_RICERCA>

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    import subprocess
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Errore nel recupero del token: {result.stderr}")
    return result.stdout.strip()

def global_search(search_str):
    token = get_token()
    url = "https://desk.zoho.eu/api/v1/search"
    params = {
        "module": "tickets",
        "searchStr": search_str
    }
    headers = {
        "orgId": ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Errore: Termine di ricerca mancante.")
        sys.exit(1)
        
    search_str = " ".join(sys.argv[1:])
    try:
        results = global_search(search_str)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
