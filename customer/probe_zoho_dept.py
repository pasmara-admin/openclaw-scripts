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
    url = "https://desk.zoho.eu/api/v1/tickets"
    # Abbiamo visto che il 157848 è del 24 Ottobre.
    # Proviamo ad interrogare il 20 Ottobre scendendo da li.
    # Sappiamo che il 157849 è di Luglio.
    # Quindi i ticket del 20 Ottobre DEVONO essere tra offset 157848 e indietro (verso 0).
    # Proviamo offset crescenti verso il presente.
    # 157848 -> 24 Ott.
    # 157000 -> 1 Nov.
    # C'è qualcosa di strano: il sortBy=-createdTime mette i più recenti all'inizio (offset 0).
    # Quindi scendendo l'offset (verso 0) andiamo verso il futuro.
    # Salendo l'offset (verso 157k) andiamo verso il passato.
    # Se 157848 è 24 Ottobre e 157849 è Luglio, il 20 Ottobre dovrebbe essere DOPO il 157848 (offset > 157848).
    # Ma abbiamo visto che 157849 è Luglio. 
    # Questo significa che tra 24 Ottobre e Luglio 2025 NON ci sono altri ticket nel dataset restituito.
    # Possibile che il 20 Ottobre sia stato saltato o sia in un'altra pagina?
    # Proviamo offset tra 157840 e 157850 ancora una volta con calma.
    for o in range(157840, 157860):
        params = {"sortBy": "-createdTime", "from": o, "limit": 1}
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            if 'data' in data and len(data['data']) > 0:
                t = data['data'][0]
                print(f"Offset {o}: {t['ticketNumber']} ({t['createdTime']})")
