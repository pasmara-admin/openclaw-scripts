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

# Parse PS result (skip header)
id_to_ref = {}
for line in ps_result.strip().split('\n')[1:]:
    if line:
        parts = line.split('\t')
        if len(parts) == 2:
            id_to_ref[int(parts[0])] = parts[1].strip()

# Now fetch from Kanguro
references = list(set(id_to_ref.values()))
refs_str = ",".join(f"'{r}'" for r in references if r)

query_kang = f"SELECT order_number, full_number, type_id, date, total FROM bil_document WHERE order_number IN ({refs_str});"
with open("kang_query.sql", "w") as f:
    f.write(query_kang)

cmd_kang = 'mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro < kang_query.sql'
kang_result = subprocess.check_output(cmd_kang, shell=True, text=True)

# Parse Kanguro result (skip header)
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
            
            # Map type_id to name based on our earlier check
            type_name = "Fattura" if type_id == 1 else "Nota di Credito" if type_id == 2 else "Ricevuta" if type_id == 3 else "Storno Ricevuta"
            
            if ref not in ref_to_docs:
                ref_to_docs[ref] = []
            ref_to_docs[ref].append({'doc': f"{full_number} ({type_name})", 'date': date, 'total': total, 'type_id': type_id})

# Prepare final data
result_rows = []
for index, row in df.iterrows():
    if pd.isna(row['metadata_Order']):
        continue
    
    id_order = int(row['metadata_Order'])
    ref = id_to_ref.get(id_order, '')
    
    docs = ref_to_docs.get(ref, [])
    # If multiple docs, format them or just take the primary (Ricevuta/Fattura). Let's take primary (type_id 1 or 3)
    primary_docs = [d for d in docs if d['type_id'] in (1, 3)]
    doc = primary_docs[0] if primary_docs else (docs[0] if docs else None)
    
    if doc:
        doc_str = doc['doc']
        doc_date = doc['date']
        doc_total = doc['total']
    else:
        doc_str = ''
        doc_date = ''
        doc_total = ''
        
    reg_date_utc = str(row['Data di registrazione (UTC)'])[:10] # Get YYYY-MM-DD
    
    result_rows.append({
        'Reference Ordine': ref,
        'Documento Kanguro': doc_str,
        'Importo (Kanguro)': doc_total,
        'Data Kanguro': doc_date,
        'Data Registrazione (Excel)': reg_date_utc
    })

res_df = pd.DataFrame(result_rows)

# Calculate difference
res_df['Data Kanguro'] = pd.to_datetime(res_df['Data Kanguro'], errors='coerce')
res_df['Data Registrazione (Excel)'] = pd.to_datetime(res_df['Data Registrazione (Excel)'], errors='coerce')
res_df['Ritardo (Giorni)'] = (res_df['Data Registrazione (Excel)'] - res_df['Data Kanguro']).dt.days

# Export to CSV
out_path = '/root/.openclaw/workspace-finance/Associazione_PayPlug_Kanguro.csv'
res_df.to_csv(out_path, index=False, sep=';', encoding='utf-8')

# Log SQL queries
os.system(f'echo "[$(date)] SELECT id_order, reference FROM ps_orders WHERE id_order IN (...);" >> /root/.openclaw/workspace-finance/.openclaw/query_history.log')
os.system(f'echo "[$(date)] SELECT order_number, full_number, type_id, date, total FROM bil_document WHERE order_number IN (...);" >> /root/.openclaw/workspace-finance/.openclaw/query_history.log')

print(f"Generated successfully: {out_path}")
print(f"Average delay: {res_df['Ritardo (Giorni)'].mean():.2f} days")
