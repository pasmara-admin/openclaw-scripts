import pandas as pd
import mysql.connector
import os

print("Connecting to database...")
conn = mysql.connector.connect(
    host="34.38.166.212",
    user="john",
    password="3rmiCyf6d~MZDO41",
    database="kanguro"
)
cursor = conn.cursor(dictionary=True)

print("Fetching active orders from Jan 2026...")
# Added payment_state_id, total_paid
query_orders = """
SELECT id, number, date, total, total_paid, state_id, billing_state_id, payment_state_id
FROM sal_order
WHERE date >= '2026-01-01'
  AND state_id NOT IN ('00', '01')
"""
cursor.execute(query_orders)
orders = cursor.fetchall()
print(f"Found {len(orders)} active orders.")

order_ids = [str(o['id']) for o in orders]
doc_map = {}

if order_ids:
    print("Fetching billing documents...")
    chunk_size = 5000
    for i in range(0, len(order_ids), chunk_size):
        chunk = order_ids[i:i+chunk_size]
        format_strings = ','.join(['%s'] * len(chunk))
        query_docs = f"""
        SELECT order_id, full_number, total
        FROM bil_document
        WHERE order_id IN ({format_strings})
          AND type_id IN (1,3)
          AND state_id NOT IN ('00', '80')
        """
        cursor.execute(query_docs, tuple(chunk))
        
        for row in cursor.fetchall():
            o_id = row['order_id']
            if o_id not in doc_map:
                doc_map[o_id] = {
                    'numbers': [],
                    'total': 0.0
                }
            if row['full_number']:
                doc_map[o_id]['numbers'].append(row['full_number'])
            doc_map[o_id]['total'] += float(row['total']) if row['total'] else 0.0

print("Processing results...")
results = []
for o in orders:
    o_id = o['id']
    docs = doc_map.get(o_id)
    
    if docs and docs['numbers']:
        num_doc_str = " + ".join(docs['numbers'])
        tot_doc = round(docs['total'], 2)
        stato = "Fatturato/Ricevuta emessa"
    else:
        num_doc_str = ""
        tot_doc = 0.0
        stato = "Da fatturare / Nessun doc"
        
    # Determine payment status
    # Usually payment_state_id '99' means paid, '10' / '05' pending, etc.
    # Also checking if total_paid >= total as a safety net
    # If it's cash on delivery, payment_state might be '10' but it's handled differently, 
    # but we will just provide a clear text label
    payment_status = "Sì" if o['payment_state_id'] == '99' or float(o['total_paid']) >= float(o['total']) else "No"
        
    results.append({
        'ID Ordine (Kanguro)': o_id,
        'Numero Ordine': o['number'],
        'Data Ordine': o['date'].strftime('%Y-%m-%d') if o['date'] else "",
        'Totale Ordine (€)': round(float(o['total']), 2) if o['total'] else 0.0,
        'Totale Pagato (€)': round(float(o['total_paid']), 2) if o['total_paid'] else 0.0,
        'Ordine Pagato?': payment_status,
        'Stato Documenti': stato,
        'Numeri Documento': num_doc_str,
        'Totale Documenti Emessi (€)': tot_doc,
        'Stato Ordine (ID)': o['state_id'],
        'Stato Fatturazione (ID)': o['billing_state_id'],
        'Stato Pagamento (ID)': o['payment_state_id']
    })

df = pd.DataFrame(results)

output_file = "/root/.openclaw/workspace-finance/Ordini_Attivi_Fatturazione_Pagamenti_2026.xlsx"
print(f"Saving to {output_file}...")
df.to_excel(output_file, index=False)

cursor.close()
conn.close()
print("Done!")
