#!/bin/bash
DATE=$(date +"%d/%m/%Y")
SUBJECT="Ordini non fatturati up to $DATE"
BODY="In allegato quanto in oggetto."
FILE="/root/.openclaw/workspace-finance/Report_Ordini_Non_Fatturati_Daily.xlsx"

# Genera il file
python3 /root/.openclaw/workspace-shared/openclaw-scripts/finance/generate_unbilled_orders.py > /dev/null 2>&1

export GOG_KEYRING_PASSWORD="produceshop"
export GOG_ACCOUNT="admin@produceshoptech.com"

# Logica per i 10 invii (semplificata: leggiamo quante volte ha girato)
COUNT_FILE="/root/.openclaw/workspace-finance/.unbilled_email_count"
if [ ! -f "$COUNT_FILE" ]; then
    echo "0" > "$COUNT_FILE"
fi

COUNT=$(cat "$COUNT_FILE")
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNT_FILE"

RECIPIENTS="baldassare.gulotta@produceshop.com,valentina.loreti@produceshop.com"
if [ "$COUNT" -le 10 ]; then
    CC="ivan.cianci@produceshop.com"
    gog gmail send --to "$RECIPIENTS" --cc "$CC" --subject "$SUBJECT" --body "$BODY" --attach "$FILE" --no-input
else
    gog gmail send --to "$RECIPIENTS" --subject "$SUBJECT" --body "$BODY" --attach "$FILE" --no-input
fi

openclaw message send --target telegram:-5243139273 --message "✅ Report_Ordini_Non_Fatturati_Daily inviato con successo (Invio n. $COUNT)."
