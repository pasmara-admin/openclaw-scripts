#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Genera il testo
python3 /root/.openclaw/workspace-shared/openclaw-scripts/finance/generate_fatturato.py > /tmp/fatturato_msg.txt

# Genera i grafici in tmp
python3 /root/.openclaw/workspace-shared/openclaw-scripts/finance/generate_chart.py

# Aggiungi i saluti
HOUR=$(date +"%H")
if [ "$HOUR" -eq "23" ]; then
    echo -e "\nBuonanotte a tutti dal vostro analista di fiducia. 🦞\n\nJohn Marketing" >> /tmp/fatturato_msg.txt
else
    echo -e "\nBuon proseguimento di giornata dal vostro analista di fiducia. 🦞\n\nJohn Marketing" >> /tmp/fatturato_msg.txt
fi

# Send via OpenClaw (Telegram)
openclaw message send --channel telegram --target "-5176361873" --message "$(cat /tmp/fatturato_msg.txt)"

# Send via Email
GOG_KEYRING_PASSWORD="produceshop" GOG_ACCOUNT="admin@produceshoptech.com" gog gmail send \
  --to "mario.spina@produceshop.com,ivan.cianci@produceshop.com,ronny.soana@produceshop.com,karim.elsaket@produceshop.com,luca.cuppari@produceshop.com,simone.bergantin@produceshop.com,simone.meinardi@produceshop.com" \
  --subject "Report Fatturato Produceshop - $(date '+%d/%m/%Y %H:%M')" \
  --body-file /tmp/fatturato_msg.txt \
  --attach /tmp/fatturato_charts.jpg \
  --no-input
