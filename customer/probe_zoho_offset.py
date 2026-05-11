import requests
import json
import sys
import subprocess
import time

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Errore nel recupero del token: {result.stderr}")
    return result.stdout.strip()

def search_tickets(filters):
    token = get_token()
    url = "https://desk.zoho.eu/api/v1/tickets/search"
    headers = {
        "orgId": ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    response = requests.get(url, headers=headers, params=filters)
    if response.status_code != 200:
        return None
    return response.json()

def find_ticket_by_date(target_date_str):
    # target_date_str: YYYY-MM-DD
    # Strategia: Sappiamo che il ticketNumber è sequenziale.
    # Proviamo ad avvicinarci tramite 'from' index se possibile (ma limitato a 5000).
    # Quindi dobbiamo usare la ricerca per 'modifiedTime' o simili se supportati,
    # ma sappiamo che non lo sono.
    # Unica via: scansione lineare o binaria manuale dei ticketNumber?
    # No, proviamo a usare 'createdTime' nel search se l'errore era solo per parametri EXTRA.
    # Ma l'errore diceva "Extra query parameter 'createdTime' is present".
    
    # Proviamo a usare la ricerca per subject con una stringa comune o simile, 
    # ma il modo migliore è usare il sortBy=-createdTime e andare a ritroso.
    # Poiché 'from' è limitato a 5000, possiamo solo vedere i primi 5000.
    # TUTTAVIA, se ordiniamo per sortBy=createdTime (ASC), vediamo i primi 5000 della storia.
    # Dobbiamo trovare un modo per saltare.
    
    print(f"Cercando ticket vicino a {target_date_str}...")
    
    # Sappiamo:
    # #120 -> 2020-04-17
    # #5731817 -> 2026-04-01
    
    # Stima lineare:
    # Giorni totali approx: 6 anni * 365 = 2190 giorni.
    # Ticket totali: 5.7M.
    # Ticket al giorno: 5.7M / 2190 = 2600 ticket/giorno.
    
    # Target: 2025-10-20.
    # Giorni dal 2026-04-01 a ritroso: circa 162 giorni.
    # Ticket da scalare: 162 * 2600 = 421.200 ticket.
    # Stima ticketNumber: 5.731.817 - 421.200 = 5.310.617.
    
    # Visto che non possiamo cercare per ticketNumber direttamente nel search,
    # dobbiamo scansionare i ticket tramite ID o sperare che 'createdTime' funzioni in un altro endpoint.
    
    # Proviamo a usare l'endpoint /tickets (list) con sortBy.
    token = get_token()
    url = "https://desk.zoho.eu/api/v1/tickets"
    headers = {
        "orgId": ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    
    # Proviamo a vedere se accettano 'from' > 5000 qui
    params = {
        "sortBy": "-createdTime",
        "from": 10000,
        "limit": 1
    }
    res = requests.get(url, headers=headers, params=params)
    print(f"Test list 'from'=10000: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        if 'data' in data and len(data['data']) > 0:
            print(f"Trovato ticket a offset 10000: {data['data'][0]['ticketNumber']} ({data['data'][0]['createdTime']})")

if __name__ == "__main__":
    import requests
    token = get_token()
    headers = {"orgId": ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    url = "https://desk.zoho.eu/api/v1/tickets"
    # Abbiamo visto che tra 157840 (Ott 24) e 158000 (Giu 27) c'è un buco.
    # Proviamo ad affinare tra 157840 e 157860 a passi di 1.
    offsets = range(157840, 157860, 1)
    for o in offsets:
        params = {"sortBy": "-createdTime", "from": o, "limit": 1}
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and len(data['data']) > 0:
                t = data['data'][0]
                print(f"Offset {o}: {t['ticketNumber']} ({t['createdTime']})")
        else:
            print(f"Offset {o} fallito: {res.status_code}")
