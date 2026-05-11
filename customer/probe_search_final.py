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
    url = "https://desk.zoho.eu/api/v1/tickets/search"
    # Cerchiamo stringhe generiche
    params = {"subject": "Produceshop", "sortBy": "-createdTime", "limit": 50}
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        data = res.json()
        if 'data' in data:
            for t in data['data']:
                print(f"Ticket: {t['ticketNumber']} ({t['createdTime']})")
