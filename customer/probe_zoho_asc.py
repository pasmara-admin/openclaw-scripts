import requests
import json
import subprocess

TOKEN_SCRIPT = "/root/.openclaw/workspace-shared/openclaw-scripts/customer/get_zoho_token.py"
ORG_ID = "20070392953"

def get_token():
    result = subprocess.run(['python3', TOKEN_SCRIPT], capture_output=True, text=True)
    return result.stdout.strip()

if __name__ == "__main__":
    token = get_token()
    headers = {"orgId": ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    url = "https://desk.zoho.eu/api/v1/tickets"
    # Proviamo ad interrogare il dipartimento 27483000000007061 (Customer Service ProduceShop)
    # Poiché è il dipartimento principale, forse i ticket sono lì.
    dept_id = "27483000000007061"
    url = f"https://desk.zoho.eu/api/v1/departments/{dept_id}/tickets"
    # Proviamo un range di offset (DESC) per questo dipartimento.
    for o in [50000, 100000, 120000, 130000, 140000]:
        params = {"sortBy": "-createdTime", "from": o, "limit": 1}
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and len(data['data']) > 0:
                t = data['data'][0]
                print(f"Dept Offset {o}: {t['ticketNumber']} ({t['createdTime']})")
