# SCRIPT-LIST.md - Operations Scripts

- `accounting_anomalies_report.py`: Genera e invia via email i report sulle anomalie contabili (Lista A: storni senza riemissione; Lista B: Reverse Charge/IVA estero).
- `enrich_leroy_merlin_orders_poa.py`: Arricchisce file Excel di ordini Leroy Merlin con dati di spedizione, tracking, magazzino e prodotti da Kanguro.
- `riconciliazione_post_sales.py`: Identifica ordini con note credito senza riemissione che mancano di stati post-sales adeguati (vuoti o solo "Concluso").
- `report_resi_senza_nota.py`: Estrae i resi confermati (logistica chiusa) che non hanno ancora una Nota di Credito o uno Storno Ricevuta.
- `unpaid_bank_transfer_report.py`: Report settimanale per ordini in bonifico non saldati da >7gg con importo >500€ per recall clienti.


- `analyze_tracking_delays.py`: Report spedizioni senza tracking (48h + business days + PrestaShop inheritance). Esclude spedizioni con waybill/tracking manuali o ordini annullati. Supporta l'invio via email.
- `ordini_bloccati.py`: Genera report Excel per ordini mancanti tra PS/KG (escludendo stati PS 32 e 40) e ordini bloccati su Kanguro.
- `force_shipments_delivered.py`: Forza lo stato di una lista di spedizioni a 'Consegnata' (99) in `lgs_shipment` e logga l'azione in `lgs_shipment_history`.
