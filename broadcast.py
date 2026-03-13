import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Broadcast deterministico via OpenClaw CLI.")
    parser.add_argument("message", help="Il messaggio da inviare")
    args = parser.parse_args()

    # Mappa deterministica Chat ID -> Account ID
    # Estratta da JOHN-TELEGRAM-GROUPS.md
    broadcast_map = [
        {"name": "Main (Papà)", "chat": "496364314", "acc": "default"},
        {"name": "Finance", "chat": "-5243139273", "acc": "finance"},
        {"name": "Marketing", "chat": "-5176361873", "acc": "marketing"},
        {"name": "Buyer", "chat": "-5131855317", "acc": "buyer"},
        {"name": "Operations", "chat": "-5123393715", "acc": "operations"},
        {"name": "Reporting", "chat": "-5066791920", "acc": "reporting"},
        {"name": "CEO", "chat": "-5150029673", "acc": "ceo"},
        {"name": "Repricing", "chat": "-5274787034", "acc": "repricing"},
        {"name": "Customer", "chat": "-5127288404", "acc": "customer"}
    ]

    print(f"🚀 Avvio broadcast rapido: {args.message}")

    for target in broadcast_map:
        print(f"-> Invio a {target['name']} ({target['chat']})...", end=" ", flush=True)
        
        cmd = [
            "openclaw", "message", "send",
            "--message", args.message,
            "--target", f"telegram:{target['chat']}",
            "--account", target['acc']
        ]
        
        try:
            # Esecuzione silenziosa e veloce
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print("✅")
            else:
                print(f"❌ Errore: {result.stderr.strip()}")
        except Exception as e:
            print(f"🔥 Eccezione: {str(e)}")

    print("\nDone.")

if __name__ == "__main__":
    main()
