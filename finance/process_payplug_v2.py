import pandas as pd
import subprocess
import os

# Load the file
file_path = "/root/.openclaw/media/inbound/2025_12_PAYPLUG_Accounting_Report_Payplug---0ce25e01-471d-4528-a978-bcaa581a2bb9.xlsx"
df = pd.read_excel(file_path)

# Extract non-null id_order values
id_orders = df['metadata_Order'].dropna().astype(int).unique().tolist()
id_orders_str = ",".join(map(str, id_orders))

# Fetch references from Prestashop
query_ps = f"SELECT id_order, reference FROM ps_orders WHERE id_order IN ({id_orders_str});"
with open("ps_query.sql", "w") as f:
    f.write(query_ps)

cmd_ps = 'mysql --skip-ssl-verify-server-cert -h 62.84.190.199 -u john -pqARa6aRozi6I produceshop < ps_query.sql'
ps_result = subprocess.check_output(cmd_ps, shell=True, text=True)

# Parse PS result
id_to_ref = {}
for line in ps_result.strip().split('\n')[1:]:
    if line:
        parts = line.split('\t')
        if len(parts) == 2:
            id_to_ref[int(parts[0])] = parts[1].strip()

# Fetch from Kanguro
references = list(set(id_to_ref.values()))
refs_str = ",".join(f"'{r}'" for r in references if r)

query_kang = f"SELECT order_number, full_number, type_id, date, total FROM bil_document WHERE order_number IN ({refs_str});"
with open("kang_query.sql", "w") as f:
    f.write(query_kang)

cmd_kang = 'mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro < kang_query.sql'
kang_result = subprocess.check_output(cmd_kang, shell=True, text=True)

# Parse Kanguro result
ref_to_docs = {}
for line in kang_result.strip().split('\n')[1:]:
    if line:
        parts = line.split('\t')
        if len(parts) == 5:
            ref = parts[0].strip()
            full_number = parts[1].strip()
            type_id = int(parts[2])
            date = parts[3].strip()
            total = parts[4].strip()
            
            type_name = "Fattura" if type_id == 1 else "Nota di Credito" if type_id == 2 else "Ricevuta" if type_id == 3 else "Storno Ricevuta"
            
            if ref not in ref_to_docs:
                ref_to_docs[ref] = []
            ref_to_docs[ref].append({'doc_num': full_number, 'doc_type': type_name, 'date': date, 'total': float(total), 'type_id': type_id})

result_rows = []
for index, row in df.iterrows():
    if pd.isna(row['metadata_Order']):
        continue
    
    id_order = int(row['metadata_Order'])
    ref = id_to_ref.get(id_order, '')
    
    docs = ref_to_docs.get(ref, [])
    # Prefer Fattura or Ricevuta
    primary_docs = [d for d in docs if d['type_id'] in (1, 3)]
    if primary_docs:
        doc = primary_docs[0]
    elif docs:
        doc = docs[0]
    else:
        doc = None
    
    if doc:
        doc_num = doc['doc_num']
        doc_type = doc['doc_type']
        doc_date = doc['date']
        doc_total = doc['total']
    else:
        doc_num = ''
        doc_type = ''
        doc_date = None
        doc_total = None
        
    reg_date_utc = row['Data di registrazione (UTC)']
    importo_excel = float(row['Importo (€)']) if pd.notna(row['Importo (€)']) else 0.0
    
    if doc_total is not None:
        diff_importi = importo_excel - doc_total
    else:
        diff_importi = None
    
    result_rows.append({
        'ID (Codice PayPlug)': row['ID'],
        'Reference Ordine': ref,
        'Numero Documento': doc_num,
        'Tipo Documento': doc_type,
        'Importo (Kanguro)': doc_total,
        'Importo (Excel Col G)': importo_excel,
        'Differenza Importi (Excel - Kanguro)': diff_importi,
        'Commissione variabile excl. IVA (%)': row['Commissione variabile excl. IVA (%)'],
        'Commissione fissa excl. IVA (€)': row['Commissione fissa excl. IVA (€)'],
        'Commissioni excl. IVA (€)': row['Commissioni excl. IVA (€)'],
        'Saldo lordo (€)': row['Saldo lordo (€)'],
        'Data Kanguro': doc_date,
        'Data Registrazione (Excel)': reg_date_utc
    })

res_df = pd.DataFrame(result_rows)

res_df['Data Kanguro'] = pd.to_datetime(res_df['Data Kanguro'], errors='coerce')
res_df['Data Registrazione (Excel)'] = pd.to_datetime(res_df['Data Registrazione (Excel)'], errors='coerce')
res_df['Ritardo Emissione Doc (Giorni)'] = (res_df['Data Kanguro'] - res_df['Data Registrazione (Excel)']).dt.days

# Formatting
res_df['Data Kanguro'] = res_df['Data Kanguro'].dt.strftime('%Y-%m-%d')
res_df['Data Registrazione (Excel)'] = res_df['Data Registrazione (Excel)'].dt.strftime('%Y-%m-%d')

out_path = '/root/.openclaw/workspace-finance/Associazione_PayPlug_Kanguro_V2.csv'
res_df.to_csv(out_path, index=False, sep=';', encoding='utf-8')

print(f"File generated: {out_path}")
