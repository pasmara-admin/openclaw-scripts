#!/bin/bash
source /root/.openclaw/workspace-shared/setup_gog_env.sh

DATE_DDMMYYYY=$(date +"%d%m%Y")
DATE_YYYYMMDD=$(date +"%Y%m%d")

CSV_FILE="/tmp/${DATE_YYYYMMDD}_Ordini attesa controllo partita IVA.csv"

python3 /root/.openclaw/workspace-shared/openclaw-scripts/finance/export_attesa_piva_attivi.py "$CSV_FILE"

cat <<BODY > /tmp/email_body.txt
In allegato quanto in oggetto.

Finance Specialist
BODY

gog gmail send \
  --to "mario.spina@produceshop.com, valentina.loreti@produceshop.com" \
  --subject "Ordini in stato attesa controllo partita IVA_YTD $DATE_DDMMYYYY" \
  --body-file /tmp/email_body.txt \
  --attach "$CSV_FILE" \
  -y

rm "$CSV_FILE" /tmp/email_body.txt
