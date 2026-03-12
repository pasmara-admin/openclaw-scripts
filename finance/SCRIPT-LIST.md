# Finance Script List
Lista minimale degli script approvati per il dipartimento Finance.
**Regola d'oro:** Nessun file duplicato (v2, v3, ecc.), usa Git per il versioning. Tutti gli script devono essere generici e parametrizzati.

| Script | Descrizione |
|--------|-------------|
| `daily_fatturato.sh` | Wrapper Bash per l'esecuzione automatica del comando FATTURATO. |
| `generate_fatturato.py` | Estrazione fatturato giornaliero (Sito vs Marketplaces) da Kanguro. |
| `generate_invoice_report.py` | Generazione storico/mensile Report Revenue in formato Excel. |
| `process_payplug.py` | Script di riconciliazione Gateway/Banca e gestione transazioni Payplug. |
| `schedule_report_revenue.py` | Schedulatore e logica delle regole di invio email per il Report Revenue. |
| `send_report_revenue.py` | Modulo per l'invio via email (gog) dei report finanziari e log su Telegram. |
| `generate_chart.py` | Generazione grafici andamento vendite (da mantenere parametrizzato). |
