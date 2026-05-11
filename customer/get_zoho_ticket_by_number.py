import requests
import json
import sys
import subprocess

# Script per recuperare un singolo ticket tramite ticketNumber (NON l'ID interno)
# Uso: python3 get_zoho_ticket_by_number.py <ticketNumber>

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Errore nel recupero del token: {result.stderr}")
    return result.stdout.strip()

def get_ticket_by_number(ticket_number):
    token = get_token()
    # Proviamo con l'endpoint specifico per ticketNumber se esiste o general search
    # La documentazione Zoho Desk dice che per cercare per ticketNumber si usa q=numero
    # Ma abbiamo visto che q non è accettato. Proviamo a cercarlo come 'query'
    url = "https://desk.zoho.eu/api/v1/tickets/search"
    headers = {
        "orgId": ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    # Prova 1: caseNumber (fallita)
    # Prova 2: ticketNumber (fallita)
    # Prova 3: Usiamo l'endpoint di base /tickets con filtro? No, proviamo search con 'subject' o simili se q fallisce
    # Ma se vogliamo il ticket esatto, proviamo a chiamare /tickets/search con parametro 'any'
    params = {
        "ticketNumber": ticket_number
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 get_zoho_ticket_by_number.py <ticketNumber>")
        sys.exit(1)
    
    ticket_num = sys.argv[1]
    try:
        result = get_ticket_by_number(ticket_num)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
