import argparse
import subprocess
import concurrent.futures
import sys

def send_message(target, message):
    name = target['name']
    chat = target['chat']
    acc = target['acc']
    
    cmd = [
        "openclaw", "message", "send",
        "--message", message,
        "--target", f"telegram:{chat}",
        "--account", acc
    ]
    
    try:
        # Aumentato il timeout a 30s perché l'avvio della CLI è pesante
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return f"✅ {name}"
        else:
            return f"❌ {name}: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"⏰ {name}: Timeout (30s)"
    except Exception as e:
        return f"🔥 {name}: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Broadcast parallelo e deterministico via OpenClaw CLI.")
    parser.add_argument("message", help="Il messaggio da inviare")
    parser.add_argument("--targets", help="Elenco di nomi target separati da virgola (es. Finance,CEO). Se vuoto, invia a tutti.")
    args = parser.parse_args()

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

    # Filtro target se specificato
    if args.targets:
        target_names = [t.strip().lower() for t in args.targets.split(",")]
        active_targets = [t for t in broadcast_map if t['name'].lower() in target_names or t['acc'].lower() in target_names]
        if not active_targets:
            print(f"⚠️ Nessun target trovato per: {args.targets}")
            sys.exit(1)
    else:
        active_targets = broadcast_map

    print(f"🚀 Avvio broadcast PARALLELO su {len(active_targets)} target: {args.message}")

    # Utilizzo di ThreadPoolExecutor per invii simultanei
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_targets)) as executor:
        future_to_target = {executor.submit(send_message, target, args.message): target for target in active_targets}
        
        for future in concurrent.futures.as_completed(future_to_target):
            print(future.result())

    print("\nDone.")

if __name__ == "__main__":
    main()
