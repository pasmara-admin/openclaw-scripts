import pandas as pd
import subprocess

file_path = "/root/.openclaw/media/inbound/2025_12_PAYPLUG_Accounting_Report_Payplug---0ce25e01-471d-4528-a978-bcaa581a2bb9.xlsx"
df = pd.read_excel(file_path)
id_orders = df['metadata_Order'].dropna().astype(int).unique().tolist()
id_orders_str = ",".join(map(str, id_orders))

query_ps = f"SELECT id_order, reference FROM ps_orders WHERE id_order IN ({id_orders_str});"
with open("ps_query.sql", "w") as f: f.write(query_ps)
ps_result = subprocess.check_output('mysql --skip-ssl-verify-server-cert -h 62.84.190.199 -u john -pqARa6aRozi6I produceshop < ps_query.sql', shell=True, text=True)

id_to_ref = {}
for line in ps_result.strip().split('\n')[1:]:
    if line:
        parts = line.split('\t')
        if len(parts) == 2: id_to_ref[int(parts[0])] = parts[1].strip()

refs_str = ",".join(f"'{r}'" for r in set(id_to_ref.values()) if r)
query_kang = f"SELECT order_number, full_number, number, type_id, date, total FROM bil_document WHERE order_number IN ({refs_str});"
with open("kang_query.sql", "w") as f: f.write(query_kang)
kang_result = subprocess.check_output('mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro < kang_query.sql', shell=True, text=True)

ref_to_docs = {}
for line in kang_result.strip().split('\n')[1:]:
    if line:
        parts = line.split('\t')
        if len(parts) >= 6:
            ref = parts[0].strip()
            full_number = parts[1].strip()
            type_id = int(parts[3])
            date = parts[4].strip()
            total = float(parts[5].strip())
            
            type_name = "Fattura" if type_id == 1 else "Nota di Credito" if type_id == 2 else "Ricevuta" if type_id == 3 else "Storno Ricevuta"
            
            # Keep only valid primary docs
            if type_id in (1, 3):
                if ref not in ref_to_docs: ref_to_docs[ref] = []
                ref_to_docs[ref].append({'doc_num': full_number, 'doc_type': type_name, 'date': date, 'total': total, 'type_id': type_id})

# Since an order can have multiple transactions in PayPlug (Excel rows), AND multiple invoices in Kanguro,
# calculating a per-row difference is confusing if we just do "Row Amount - Sum of all Kanguro Invoices".
# We should calculate:
# Total paid for this order in Excel = SUM(Importo for this order)
# Total invoiced for this order in Kanguro = SUM(Invoices for this order)
# Diff = Total Paid - Total Invoiced

# 1. Group Excel by order to get Total Paid
df['metadata_Order_clean'] = df['metadata_Order'].fillna(0).astype(int)
order_totals_excel = df.groupby('metadata_Order_clean')['Importo (€)'].sum().to_dict()

result_rows = []
for index, row in df.iterrows():
    if pd.isna(row['metadata_Order']): continue
    
    id_order = int(row['metadata_Order'])
    ref = id_to_ref.get(id_order, '')
    docs = ref_to_docs.get(ref, [])
    
    if not docs:
        docs = [{'doc_num': '', 'doc_type': '', 'date': None, 'total': None}]
        
    reg_date_utc = row['Data di registrazione (UTC)']
    importo_excel_riga = float(row['Importo (€)']) if pd.notna(row['Importo (€)']) else 0.0
    
    # Order Level Totals
    importo_excel_totale_ordine = order_totals_excel.get(id_order, 0.0)
    importo_kanguro_totale_ordine = sum(d['total'] for d in docs if d.get('total') is not None) if docs[0].get('total') is not None else None
    
    diff_totale_ordine = importo_excel_totale_ordine - importo_kanguro_totale_ordine if importo_kanguro_totale_ordine is not None else None
    
    for doc in docs:
        doc_total = doc['total']
            
        result_rows.append({
            'ID (Codice PayPlug)': row['ID'],
            'Reference Ordine': ref,
            'Numero Documento': doc['doc_num'],
            'Tipo Documento': doc['doc_type'],
            'Importo Kanguro (Singolo Doc)': doc_total,
            'Importo Payplug (Singola Riga)': importo_excel_riga,
            'Totale Inviato PayPlug (Intero Ordine)': importo_excel_totale_ordine,
            'Totale Fatturato Kanguro (Intero Ordine)': importo_kanguro_totale_ordine,
            'Differenza Totale (PayPlug - Kanguro)': diff_totale_ordine,
            'Data Kanguro': doc['date'],
            'Data Registrazione (Excel)': reg_date_utc
        })

res_df = pd.DataFrame(result_rows)
res_df['Data Kanguro'] = pd.to_datetime(res_df['Data Kanguro'], errors='coerce')
res_df['Data Registrazione (Excel)'] = pd.to_datetime(res_df['Data Registrazione (Excel)'], errors='coerce')

res_df['Ritardo Emissione Doc (Giorni)'] = (res_df['Data Kanguro'] - res_df['Data Registrazione (Excel)']).dt.total_seconds() / 86400.0

res_df['Data Kanguro'] = res_df['Data Kanguro'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
res_df['Data Registrazione (Excel)'] = res_df['Data Registrazione (Excel)'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')

out_path = '/root/.openclaw/workspace-finance/Associazione_PayPlug_Kanguro_V5.csv'
res_df.to_csv(out_path, index=False, sep=';', encoding='utf-8')
print("Done V5")
