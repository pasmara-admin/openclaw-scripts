import requests
import json
import os
import sys

# Script per ottenere i dettagli di un ticket specifico
# Uso: python3 get_zoho_ticket.py <TICKET_ID>

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    import subprocess
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Errore nel recupero del token: {result.stderr}")
    return result.stdout.strip()

def get_ticket(ticket_id):
    token = get_token()
    url = f"https://desk.zoho.eu/api/v1/tickets/{ticket_id}"
    params = {"include": "contacts,products,assignee,departments,team"}
    headers = {
        "orgId": ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Errore: ID ticket mancante.")
        sys.exit(1)
    
    try:
        ticket = get_ticket(sys.argv[1])
        print(json.dumps(ticket, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
