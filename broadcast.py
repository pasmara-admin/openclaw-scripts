import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Invia un messaggio broadcast a tutti i gruppi Telegram degli agenti John.")
    parser.add_argument("message", help="Il messaggio da inviare")
    args = parser.parse_args()

    # Mappa degli agenti e dei loro gruppi (ID estratti da JOHN-TELEGRAM-GROUPS.md)
    agents = [
        {"id": "john-finance", "chat": "-5243139273"},
        {"id": "john-marketing", "chat": "-5176361873"},
        {"id": "john-buyer", "chat": "-5131855317"},
        {"id": "john-operations", "chat": "-5123393715"},
        {"id": "john-reporting", "chat": "-5066791920"},
        {"id": "john-ceo", "chat": "-5150029673"},
        {"id": "john-repricing", "chat": "-5274787034"},
        {"id": "john-customer", "chat": "-5127288404"},
        {"id": "john-main", "chat": "496364314"}
    ]

    print(f"Inizio broadcast: {args.message}")

    for agent in agents:
        agent_id = agent["id"]
        chat_id = agent["chat"]
        
        print(f"Inviando a {agent_id} (Chat: {chat_id})...")
        
        # Usiamo la CLI di OpenClaw per inviare il messaggio. 
        # Questo comando usa il bot predefinito configurato nell'account 'default' 
        # o quello specificato se la CLI supporta l'account.
        # Dato che John Main ha accesso a tutto, può inviare ai vari chat_id.
        cmd = [
            "openclaw", "message", "send",
            "--message", args.message,
            "--target", f"telegram:{chat_id}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Messaggio inviato a {agent_id} con successo.")
            else:
                # Se fallisce, potrebbe essere perché il bot Main non è in quel gruppo.
                # In tal caso, dovremmo usare l'account specifico dell'agente.
                print(f"Tentativo con account specifico per {agent_id}...")
                # L'ID account solitamente corrisponde al nome del settore (finance, marketing, ecc.)
                acc_name = agent_id.replace("john-", "")
                cmd_acc = cmd + ["--account", acc_name]
                result_acc = subprocess.run(cmd_acc, capture_output=True, text=True)
                if result_acc.returncode == 0:
                    print(f"Inviato con account {acc_name}.")
                else:
                    print(f"Errore critico per {agent_id}: {result_acc.stderr}")
        except Exception as e:
            print(f"Errore per {agent_id}: {str(e)}")

    print("Broadcast completato.")

if __name__ == "__main__":
    main()
