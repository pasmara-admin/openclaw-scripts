# Marketing Script List
Lista minimale degli script per il dipartimento Marketing. Consultare prima di creare nuovi script.

| Script | Descrizione |
|--------|-------------|
| analyze_roas.py | Analisi dell'incidenza (spend/revenue) e ROAS delle campagne Google Ads. |
| calc_final_prices.py | Calcolo dei prezzi di vendita finali (inclusi tasse/margini). |
| calc_parent_incidence.py | Calcolo dell'incidenza a livello di Parent Product per risolvere l'effetto halo. |
| calc_worst_parent_incidence.py | Analisi e individuazione dei prodotti parent con l'incidenza peggiore. |
| check_lower_sku.py | Utility per validazione SKU in minuscolo e controllo consistenza feed. |
| check_sku_performance.py | Script generico parametrizzato per controllo performance Ads su qualsiasi SKU. |
| check_sku_format.py | Controllo e validazione del formato SKU per richieste Google Ads. |
| check_sku_title.py | Analisi dei titoli prodotto associati agli SKU nei feed. |
| fetch_ads_campaigns_it.py | Estrazione in tempo reale delle campagne attive sull'account IT. |
| fetch_ads_data.py | Estrazione generica di metriche da Google Ads API. |
| fetch_today_spend.py | Download in realtime della spesa Google Ads del giorno (procedura principale condivisa con Finance). |
| find_product_costs.sh | Utility bash per estrarre tutti i costi e prezzi associati a un product_id. |
| find_value_in_db.sh | Utility bash generica per cercare uno specifico valore numerico (es. 31.70) in tutte le tabelle di prezzo/costo del DB Kanguro. |
| get_info_ry.py | Generazione del report INFO (Stock, vendite dal 10/2025, prezzo, WAC). |
| get_prices_vat.py | Estrazione prezzi con IVA calcolata per country. |
| get_product_stats.py | Generazione di report statistici su prodotti e conversioni. |
| get_top_campaigns.py | Estrazione delle migliori campagne in base all'incidenza/revenue. |
| recalc_incidenza.py | Ricalcolo massivo dell'incidenza aggregando spesa e fatturato. |
| realtime_incidence.py | Calcolo in tempo reale dell'incidenza globale e per country sul sito ProduceShop (Ads/Kanguro). |
| forecast_oos_pricing.py | Estrazione prodotti con vendite >0 e Out Of Stock stimato in <14gg (Kanguro sales + PrestaShop stock) per revisione prezzi. |
| drop_performance.py | Estrazione delle performance di vendita e di traffico (Google Ads + Kanguro) per i prodotti etichettati in Dropshipping. |
| send_drop_report.py | Genera e invia via mail il report giornaliero sulle performance Drop (Kanguro + Ads). |
| drop_weekly_analysis.py | Report settimanale in Excel su prodotti Drop ad alti click e basse vendite, o a zero click e zero vendite. |
