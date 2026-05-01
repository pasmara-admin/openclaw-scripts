import pandas as pd
import mysql.connector
import sys

if len(sys.argv) < 3:
    print("Usage: python3 payplug_reconciliation_report.py <input_excel> <output_excel>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

print(f"Reading {input_file}...")
df_all = pd.read_excel(input_file, sheet_name=None)
first_sheet_name = list(df_all.keys())[0]
df = df_all[first_sheet_name]

pagamenti = df[df.iloc[:, 4] == "Pagamento"].copy()
cols_to_keep = [0, 1, 2, 6, 7, 8, 9, 11, 12, 13, 15]
df_filtered = pagamenti.iloc[:, cols_to_keep].copy()

api_ids = df_filtered.iloc[:, 10].dropna().unique().tolist()
print(f"Found {len(api_ids)} unique API IDs. Fetching from DB...")

conn = mysql.connector.connect(
    host="34.38.166.212",
    user="john",
    password="3rmiCyf6d~MZDO41",
    database="kanguro"
)
cursor = conn.cursor(dictionary=True)

# We batch select order transactions
chunk_size = 1000
order_map = {} # api_id -> order_id

for i in range(0, len(api_ids), chunk_size):
    chunk = api_ids[i:i+chunk_size]
    format_strings = ','.join(['%s'] * len(chunk))
    # Check transaction_code
    cursor.execute(f"SELECT transaction_code, order_id FROM sal_order_transaction WHERE transaction_code IN ({format_strings})", tuple(chunk))
    for row in cursor.fetchall():
        order_map[row['transaction_code']] = row['order_id']
    
    # Check payment_code for those missing
    missing = [c for c in chunk if c not in order_map]
    if missing:
        format_strings_m = ','.join(['%s'] * len(missing))
        cursor.execute(f"SELECT payment_code, order_id FROM sal_order_transaction WHERE payment_code IN ({format_strings_m})", tuple(missing))
        for row in cursor.fetchall():
            order_map[row['payment_code']] = row['order_id']

order_ids = list(set(order_map.values()))
print(f"Found {len(order_ids)} matching orders. Fetching billing documents and order numbers...")

# Batch select order numbers
order_number_map = {} # order_id -> order_number
for i in range(0, len(order_ids), chunk_size):
    chunk = order_ids[i:i+chunk_size]
    format_strings = ','.join(['%s'] * len(chunk))
    cursor.execute(f"SELECT id, number FROM sal_order WHERE id IN ({format_strings})", tuple(chunk))
    for row in cursor.fetchall():
        order_number_map[row['id']] = row['number']

# Batch select billing documents (only Invoices and Receipts, type_id IN (1,3))
doc_map = {} # order_id -> {'date': max_date, 'full_number': list_of_numbers, 'total': sum_of_totals}
for i in range(0, len(order_ids), chunk_size):
    chunk = order_ids[i:i+chunk_size]
    format_strings = ','.join(['%s'] * len(chunk))
    cursor.execute(f"SELECT order_id, date, full_number, total FROM bil_document WHERE order_id IN ({format_strings}) AND type_id IN (1,3) ORDER BY id ASC", tuple(chunk))
    for row in cursor.fetchall():
        o_id = row['order_id']
        if o_id not in doc_map:
            doc_map[o_id] = {
                'date': row['date'],
                'numbers': [row['full_number']] if row['full_number'] else [],
                'total': float(row['total']) if row['total'] else 0.0
            }
        else:
            if row['full_number']:
                doc_map[o_id]['numbers'].append(row['full_number'])
            doc_map[o_id]['total'] += float(row['total']) if row['total'] else 0.0
            if row['date'] and doc_map[o_id]['date'] and row['date'] > doc_map[o_id]['date']:
                doc_map[o_id]['date'] = row['date'] # take latest date if multiple

cursor.close()
conn.close()

print("Processing results...")
data_fattura = []
num_doc = []
importo_totale = []
stato_doc = []
num_ordine = []

for index, row in df_filtered.iterrows():
    api_id = row.iloc[10]
    
    order_id = order_map.get(api_id)
    if order_id:
        num_ordine.append(order_number_map.get(order_id, ""))
        
        doc = doc_map.get(order_id)
        if doc and doc['numbers']: # Has at least one valid invoice/receipt
            data_fattura.append(doc['date'].strftime('%Y-%m-%d') if doc['date'] else "")
            num_doc.append(" + ".join(doc['numbers']))
            importo_totale.append(round(doc['total'], 2))
            stato_doc.append("Emessa")
        else:
            data_fattura.append("")
            num_doc.append("")
            importo_totale.append("")
            stato_doc.append("Da emettere")
    else:
        num_ordine.append("")
        data_fattura.append("")
        num_doc.append("")
        importo_totale.append("")
        stato_doc.append("Non trovato in DB")

df_filtered['Numero Ordine Kanguro'] = num_ordine
df_filtered['Data Fattura'] = data_fattura
df_filtered['Numero Documento'] = num_doc
df_filtered['Importo Totale Fattura'] = importo_totale
df_filtered['Stato Documento'] = stato_doc

print(f"Writing to {output_file}...")
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, sheet_df in df_all.items():
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    df_filtered.to_excel(writer, sheet_name="Riconciliazione Pagamenti", index=False)

print("Done!")
