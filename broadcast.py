import argparse
import json
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Invia un messaggio broadcast a tutti i gruppi Telegram degli agenti John.")
    parser.add_argument("message", help="Il messaggio da inviare")
    args = parser.parse_args()

    # Mappa degli agenti e dei loro gruppi
    agents = [
        {"id": "john-finance", "label": "Finance Specialist"},
        {"id": "john-marketing", "label": "Buyer Specialist"}, # In SOUL.md Buyer e Marketing sembrano sovrapposti in alcuni nomi, ma usiamo gli ID agent
        {"id": "john-buyer", "label": "Buyer Specialist"},
        {"id": "john-operations", "label": "Operations Specialist"},
        {"id": "john-reporting", "label": "Reporting Specialist"},
        {"id": "john-ceo", "label": "CEO Specialist"},
        {"id": "john-repricing", "label": "Repricing Specialist"},
        {"id": "john-customer", "label": "Customer Specialist"}
    ]

    print(f"Inizio broadcast: {args.message}")

    for agent in agents:
        agent_id = agent["id"]
        # Prepariamo il comando per spawnare una sessione rapida dell'agente
        # Usiamo sessions_spawn tramite CLI se possibile o simuliamo il task.
        # Poiché questo script viene eseguito da John (Main), usiamo la logica di mandare un messaggio
        # o istruire l'agente a usare il suo tool message.
        
        task = f"Invia esattamente questo messaggio al tuo gruppo Telegram ufficiale usando il tool message: {args.message}. Non fare nient'altro e non rispondere qui."
        
        print(f"Istruendo {agent_id}...")
        
        # Eseguiamo tramite openclaw cli sessions spawn
        cmd = [
            "openclaw", "sessions", "spawn",
            "--agent", agent_id,
            "--task", task,
            "--mode", "run"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Richiesta inviata a {agent_id} con successo.")
            else:
                print(f"Errore nell'invio a {agent_id}: {result.stderr}")
        except Exception as e:
            print(f"Errore durante l'esecuzione per {agent_id}: {str(e)}")

    # John Main manda anche a Damiano direttamente (opzionale, ma coerente con 'tutti i gruppi')
    print("Inviando messaggio a Damiano (John Main)...")
    # Qui il tool message di John Main verrebbe usato dall'agente che chiama lo script,
    # ma lo script è un processo separato. Meglio se John Main lo fa dopo lo script o lo script lo fa via CLI.
    cmd_main = [
        "openclaw", "message", "send",
        "--message", args.message,
        "--target", "telegram:496364314"
    ]
    subprocess.run(cmd_main)

    print("Broadcast completato.")

if __name__ == "__main__":
    main()
