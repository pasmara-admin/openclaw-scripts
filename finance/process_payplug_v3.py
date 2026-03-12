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
            number_val = parts[2].strip()
            # Handle NULL in full_number gracefully
            if full_number == 'NULL':
                # Try to use 'number' if full_number is strictly string 'NULL', though usually both might be.
                # If neither exists, we output what we can. Usually a manual document doesn't have full_number till validated.
                # Actually, M mentioned "ha fattura 165/FR", which is type_id 3 (Ricevuta) based on my SQL check!
                # Wait, order 725030214 has BOTH a Fattura (NULL) and Ricevuta (165/FR). We just need to load ALL 1 and 3 type docs.
                pass
            
            type_id = int(parts[3])
            date = parts[4].strip()
            total = parts[5].strip()
            
            type_name = "Fattura" if type_id == 1 else "Nota di Credito" if type_id == 2 else "Ricevuta" if type_id == 3 else "Storno Ricevuta"
            
            if ref not in ref_to_docs: ref_to_docs[ref] = []
            ref_to_docs[ref].append({'doc_num': full_number, 'doc_type': type_name, 'date': date, 'total': float(total), 'type_id': type_id})

result_rows = []
for index, row in df.iterrows():
    if pd.isna(row['metadata_Order']): continue
    
    id_order = int(row['metadata_Order'])
    ref = id_to_ref.get(id_order, '')
    docs = ref_to_docs.get(ref, [])
    
    # We want ALL Fatture e Ricevute (type 1 and 3)
    primary_docs = [d for d in docs if d['type_id'] in (1, 3)]
    if not primary_docs and docs: primary_docs = docs
    if not primary_docs: primary_docs = [{'doc_num': '', 'doc_type': '', 'date': None, 'total': None, 'type_id': None}]
        
    reg_date_utc = row['Data di registrazione (UTC)']
    importo_excel = float(row['Importo (€)']) if pd.notna(row['Importo (€)']) else 0.0
    
    for doc in primary_docs:
        doc_total = doc['total']
        diff_importi = importo_excel - doc_total if doc_total is not None else None
            
        result_rows.append({
            'ID (Codice PayPlug)': row['ID'],
            'Reference Ordine': ref,
            'Numero Documento': doc['doc_num'],
            'Tipo Documento': doc['doc_type'],
            'Importo (Kanguro)': doc_total,
            'Importo (Excel Col G)': importo_excel,
            'Differenza Importi (Excel - Kanguro)': diff_importi,
            'Commissione variabile excl. IVA (%)': row['Commissione variabile excl. IVA (%)'],
            'Commissione fissa excl. IVA (€)': row['Commissione fissa excl. IVA (€)'],
            'Commissioni excl. IVA (€)': row['Commissioni excl. IVA (€)'],
            'Saldo lordo (€)': row['Saldo lordo (€)'],
            'Data Kanguro': doc['date'],
            'Data Registrazione (Excel)': reg_date_utc
        })

res_df = pd.DataFrame(result_rows)
res_df['Data Kanguro'] = pd.to_datetime(res_df['Data Kanguro'], errors='coerce')
res_df['Data Registrazione (Excel)'] = pd.to_datetime(res_df['Data Registrazione (Excel)'], errors='coerce')

# Ritardo esatto (float, non arrotondato a intero come prima)
# Calculate total seconds, divide by 86400 to get decimal days.
res_df['Ritardo Emissione Doc (Giorni)'] = (res_df['Data Kanguro'] - res_df['Data Registrazione (Excel)']).dt.total_seconds() / 86400.0

res_df['Data Kanguro'] = res_df['Data Kanguro'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
res_df['Data Registrazione (Excel)'] = res_df['Data Registrazione (Excel)'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')

# Convert float diffs to standard floats
out_path = '/root/.openclaw/workspace-finance/Associazione_PayPlug_Kanguro_V3.csv'
res_df.to_csv(out_path, index=False, sep=';', encoding='utf-8')
print("Done")
