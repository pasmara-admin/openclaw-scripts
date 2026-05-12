# Finance Scripts List

- `payplug_reconciliation_report.py` : Adds a reconciliation sheet to PayPlug exported Excel reports (matches transactions with Kanguro billing documents).
- `export_attesa_piva_attivi.py`: Esporta gli ordini attivi in stato 'Attesa Controllo Partita IVA' (state_id = 20, is_deleted = 0) in formato CSV.
- `send_attesa_piva.sh`: Script per invio automatico via email del file generato da `export_attesa_piva_attivi.py`.
