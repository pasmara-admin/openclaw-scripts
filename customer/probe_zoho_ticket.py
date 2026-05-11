import requests
import json
import subprocess

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Errore nel recupero del token: {result.stderr}")
    return result.stdout.strip()

if __name__ == "__main__":
    import requests
    token = get_token()
    headers = {"orgId": ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    url = "https://desk.zoho.eu/api/v1/tickets"
    # Proviamo a scendere tra 157800 e 157849 a passi di 1.
    offsets = range(157800, 157850, 1)
    for o in offsets:
        params = {"sortBy": "-createdTime", "from": o, "limit": 1}
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and len(data['data']) > 0:
                t = data['data'][0]
                print(f"Offset {o}: {t['ticketNumber']} ({t['createdTime']})")
