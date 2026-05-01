import pandas as pd
import mysql.connector
import sys
import os

if len(sys.argv) < 3:
    print("Usage: python3 payplug_reconciliation_report.py <input_excel> <output_excel>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

print(f"Reading {input_file}...")
df_all = pd.read_excel(input_file, sheet_name=None)
first_sheet_name = list(df_all.keys())[0]
df = df_all[first_sheet_name]

# Ensure column E (index 4) exists and filter 'Pagamento'
pagamenti = df[df.iloc[:, 4] == "Pagamento"].copy()

# A(0), B(1), C(2), G(6), H(7), I(8), J(9), L(11), M(12), N(13), P(15)
cols_to_keep = [0, 1, 2, 6, 7, 8, 9, 11, 12, 13, 15]
df_filtered = pagamenti.iloc[:, cols_to_keep].copy()

conn = mysql.connector.connect(
    host="34.38.166.212",
    user="john",
    password="3rmiCyf6d~MZDO41",
    database="kanguro"
)
cursor = conn.cursor(dictionary=True)

data_fattura = []
num_doc = []
importo_netto = []
stato_doc = []

for index, row in df_filtered.iterrows():
    # ID API is at the last position of our filtered cols (index 10)
    api_id = row.iloc[10] 
    
    cursor.execute("SELECT order_id FROM sal_order_transaction WHERE transaction_code = %s OR payment_code = %s LIMIT 1", (api_id, api_id))
    transaction = cursor.fetchone()
    
    if transaction:
        order_id = transaction['order_id']
        # Get the first invoice/receipt for this order
        cursor.execute("SELECT date, full_number, subtotal FROM bil_document WHERE order_id = %s ORDER BY id ASC LIMIT 1", (order_id,))
        doc = cursor.fetchone()
        
        if doc:
            data_fattura.append(doc['date'].strftime('%Y-%m-%d') if doc['date'] else "")
            num_doc.append(doc['full_number'] if doc['full_number'] else "")
            importo_netto.append(float(doc['subtotal']) if doc['subtotal'] else 0.0)
            stato_doc.append("Emessa")
        else:
            data_fattura.append("")
            num_doc.append("")
            importo_netto.append("")
            stato_doc.append("Da emettere")
    else:
        data_fattura.append("")
        num_doc.append("")
        importo_netto.append("")
        stato_doc.append("Non trovato in DB")

df_filtered['Data Fattura'] = data_fattura
df_filtered['Numero Documento'] = num_doc
df_filtered['Importo Netto Fattura'] = importo_netto
df_filtered['Stato Documento'] = stato_doc

print(f"Writing to {output_file}...")
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, sheet_df in df_all.items():
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    df_filtered.to_excel(writer, sheet_name="Riconciliazione Pagamenti", index=False)

cursor.close()
conn.close()
print("Done!")
