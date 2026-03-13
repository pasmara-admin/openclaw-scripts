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
        # Timeout breve per ogni singola chiamata
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return f"✅ {name}"
        else:
            return f"❌ {name}: {result.stderr.strip()}"
    except Exception as e:
        return f"🔥 {name}: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Broadcast parallelo e deterministico via OpenClaw CLI.")
    parser.add_argument("message", help="Il messaggio da inviare")
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

    print(f"🚀 Avvio broadcast PARALLELO: {args.message}")

    # Utilizzo di ThreadPoolExecutor per invii simultanei
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(broadcast_map)) as executor:
        # Lancio tutti i task in parallelo
        future_to_target = {executor.submit(send_message, target, args.message): target for target in broadcast_map}
        
        for future in concurrent.futures.as_completed(future_to_target):
            print(future.result())

    print("\nBroadcast completato in parallelo.")

if __name__ == "__main__":
    main()
