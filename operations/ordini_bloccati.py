import pandas as pd
import subprocess
import os
from datetime import datetime, timedelta

def run_query(host, user, password, db, query):
    cmd = [
        "mysql", "--skip-ssl-verify-server-cert",
        "-h", host, "-u", user, f"-p{password}", db,
        "-e", query, "--batch", "--raw"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return pd.DataFrame()
    
    lines = result.stdout.strip().split('\n')
    if not lines or (len(lines) == 1 and lines[0] == ''):
        return pd.DataFrame()
    
    headers = lines[0].split('\t')
    data = [line.split('\t') for line in lines[1:] if line.strip()]
    return pd.DataFrame(data, columns=headers)

# Config
KG_CONFIG = {"host": "34.38.166.212", "user": "john", "password": "3rmiCyf6d~MZDO41", "db": "kanguro"}
PS_CONFIG = {"host": "62.84.190.199", "user": "john", "password": "qARa6aRozi6I", "db": "produceshop"}

today = datetime.now().strftime('%Y-%m-%d')

# 1. Missing Orders (PS but not KG)
ps_refs = run_query(**PS_CONFIG, query=f"SELECT reference FROM ps_orders WHERE date_add >= DATE_SUB('{today}', INTERVAL 1 MONTH);")
kg_refs = run_query(**KG_CONFIG, query=f"SELECT number FROM sal_order WHERE date >= DATE_SUB('{today}', INTERVAL 1 MONTH);")

if not ps_refs.empty and not kg_refs.empty:
    missing_list = set(ps_refs['reference'].dropna()) - set(kg_refs['number'].dropna())
else:
    missing_list = set()

if missing_list:
    refs_str = "','".join(missing_list)
    df_missing = run_query(**PS_CONFIG, query=f"SELECT o.reference as 'Numero Ordine', o.date_add as 'Data Acquisto', GROUP_CONCAT(od.product_reference SEPARATOR '; ') as 'Articoli', 'Mancante su Kanguro' as 'Stato' FROM ps_orders o JOIN ps_order_detail od ON o.id_order = od.id_order WHERE o.reference IN ('{refs_str}') GROUP BY o.id_order;")
else:
    df_missing = pd.DataFrame(columns=['Numero Ordine', 'Data Acquisto', 'Articoli', 'Stato'])

# 2. Blocked Orders (KG but not shipped, N-2 logic)
# Note: For automation, N-2 should ideally handle weekends. This script uses a fixed interval for now as per current validation.
df_blocked = run_query(**KG_CONFIG, query=f"""
SELECT 
    o.number as 'Numero Ordine', 
    o.date as 'Data Acq.', 
    sl.name as 'Stato Kanguro', 
    IFNULL((SELECT GROUP_CONCAT(DISTINCT w.display_name SEPARATOR '; ') FROM inv_warehouse w JOIN lgs_shipment ls ON ls.order_id = o.id WHERE ls.warehouse_id = w.id), '?') as 'Magazzino', 
    (SELECT GROUP_CONCAT(sor.reference SEPARATOR '; ') FROM sal_order_row sor WHERE sor.order_id = o.id AND sor.type_id = 'V') as 'Articoli', 
    (SELECT GROUP_CONCAT(DISTINCT s.name SEPARATOR '; ') FROM sal_order_row sor JOIN dat_product p ON sor.product_id = p.id JOIN dat_supplier s ON p.supplier_id = s.id WHERE sor.order_id = o.id AND sor.type_id = 'V') as 'Fornitori'
FROM sal_order o 
JOIN sal_order_state_lang sl ON o.state_id = sl.state_id AND sl.lang_id = 1 
WHERE o.date <= DATE_SUB('{today}', INTERVAL 2 DAY) 
  AND o.date >= DATE_SUB('{today}', INTERVAL 15 DAY) 
  AND o.state_id < '99' 
  AND NOT (o.payment_state_id IN ('00', '1') AND (o.payment_method_name LIKE '%Bonifico%' OR o.payment_method_name LIKE '%Banktransfer%' OR o.payment_method_name LIKE '%Banküberweisung%' OR o.payment_method_name LIKE '%Transfert bancaire%' OR o.payment_method_name LIKE '%Pagos per transferencia%')) 
  AND o.shipping_state_id < '25' 
  AND o.state_id != '00' 
ORDER BY o.date DESC;
""")

# Save Excel
filename = f'report_bloccati_{today}.xlsx'
with pd.ExcelWriter(filename) as writer:
    df_missing.to_excel(writer, sheet_name='Ordini Mancanti', index=False)
    df_blocked.to_excel(writer, sheet_name='Ordini Bloccati', index=False)

print(f"FILE_CREATED:{filename}")
