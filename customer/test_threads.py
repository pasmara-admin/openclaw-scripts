import requests
import json

token = "1000.f9525a0bf586ce9755142b4fb00bc157.16b5a1693d87a841da5ca57c6338b67f"
headers = {
    "orgId": "20070392953",
    "Authorization": f"Zoho-oauthtoken {token}"
}

# Proviamo ad interrogare i thread di un ticket recente
ticket_id = "27483001025596869"
url = f"https://desk.zoho.eu/api/v1/tickets/{ticket_id}/threads"
res = requests.get(url, headers=headers)
if res.status_code == 200:
    print(json.dumps(res.json(), indent=2))
else:
    print(f"Error {res.status_code}: {res.text}")
