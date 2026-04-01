import requests
import json
import os
import time

# Configuration from Damiano's prompt
ZOHO_ORGID = "20070392953"
ZOHO_REFRESH_TOKEN = "1000.cbc6de3df2c9ed3e16a48a4e61b33776.d11742a0f2713b4a4549f2ce570386e6"
ZOHO_CLIENT_ID = "1000.ALSZ46YQ1YWK6WOTF1KMNXP4ZC8OJM"
ZOHO_CLIENT_SECRET = "8e59f8544a2e8e54a4c7ab6559cc6029b023ce0195"
ZOHO_SCOPE = "Desk.search.READ,Desk.tickets.READ,Desk.settings.READ,Desk.basic.READ"
ZOHO_REDIRECT_URI = "https://support.produceshop.info/"
ZOHO_GRANT_TYPE = "refresh_token"

TOKEN_FILE = "/tmp/zoho_access_token.json"

def get_access_token():
    # Check if we have a valid cached token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            if data.get('expires_at', 0) > time.time() + 60: # 1 minute buffer
                return data.get('access_token')

    # Refresh token
    url = f"https://accounts.zoho.eu/oauth/v2/token"
    params = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "scope": ZOHO_SCOPE,
        "redirect_uri": ZOHO_REDIRECT_URI,
        "grant_type": ZOHO_GRANT_TYPE
    }
    
    response = requests.post(url, params=params)
    res_data = response.json()
    
    if "access_token" in res_data:
        res_data['expires_at'] = time.time() + res_data.get('expires_in', 3600)
        with open(TOKEN_FILE, 'w') as f:
            json.dump(res_data, f)
        return res_data['access_token']
    else:
        raise Exception(f"Failed to refresh Zoho token: {res_data}")

if __name__ == "__main__":
    try:
        print(get_access_token())
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
