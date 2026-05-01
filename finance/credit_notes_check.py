import pandas as pd
import mysql.connector

print("Connecting to database...")
conn = mysql.connector.connect(
    host="34.38.166.212",
    user="john",
    password="3rmiCyf6d~MZDO41",
    database="kanguro"
)
cursor = conn.cursor(dictionary=True)

# 1. Fetch all orders from 2026 that are cancelled OR have refunds
# We also want to know their total_refunded and billing_state_id to be thorough
query_orders = """
SELECT id, number, date, total, total_refunded, state_id, billing_state_id
FROM sal_order
WHERE date >= '2026-01-01'
  AND (state_id = '00' OR total_refunded > 0 OR billing_state_id IN ('11', '28', '29'))
"""
cursor.execute(query_orders)
target_orders = cursor.fetchall()
print(f"Found {len(target_orders)} orders cancelled, refunded or pending NC.")

if not target_orders:
    print("No target orders found. Exiting.")
    sys.exit(0)

order_ids = [str(o['id']) for o in target_orders]

# 2. Fetch billing documents for these orders
doc_map = {}
chunk_size = 5000
for i in range(0, len(order_ids), chunk_size):
    chunk = order_ids[i:i+chunk_size]
    format_strings = ','.join(['%s'] * len(chunk))
    query_docs = f"""
    SELECT order_id, full_number, total, type_id
    FROM bil_document
    WHERE order_id IN ({format_strings})
      AND state_id NOT IN ('00', '80')
      AND full_number IS NOT NULL
    """
    cursor.execute(query_docs, tuple(chunk))
    for row in cursor.fetchall():
        o_id = row['order_id']
        t_id = row['type_id']
        if o_id not in doc_map:
            doc_map[o_id] = {'invoices': [], 'credit_notes': [], 'inv_total': 0.0, 'cn_total': 0.0}
        
        if t_id in (1, 3): # Fattura / Ricevuta
            doc_map[o_id]['invoices'].append(row['full_number'])
            doc_map[o_id]['inv_total'] += float(row['total']) if row['total'] else 0.0
        elif t_id in (2, 4): # Nota di Credito / Storno Ricevuta
            doc_map[o_id]['credit_notes'].append(row['full_number'])
            doc_map[o_id]['cn_total'] += float(row['total']) if row['total'] else 0.0

print("Processing results...")
results = []
for o in target_orders:
    o_id = o['id']
    docs = doc_map.get(o_id)
    
    # We ONLY care about orders that HAD an invoice/receipt issued
    if docs and docs['invoices']:
        inv_str = " + ".join(docs['invoices'])
        inv_tot = round(docs['inv_total'], 2)
        
        cn_str = " + ".join(docs['credit_notes']) if docs['credit_notes'] else ""
        cn_tot = round(docs['cn_total'], 2) if docs['credit_notes'] else 0.0
        
        if cn_tot > 0:
            stato_nc = "Nota di Credito emessa"
        else:
            stato_nc = "NC Mancante / Da emettere"
            
        results.append({
            'ID Ordine (Kanguro)': o_id,
            'Numero Ordine': o['number'],
            'Data Ordine': o['date'].strftime('%Y-%m-%d') if o['date'] else "",
            'Stato Ordine': "Annullato" if o['state_id'] == '00' else "Attivo/Rimborsato",
            'Totale Ordine (€)': round(float(o['total']), 2),
            'Totale Rimborsato su Ordine (€)': round(float(o['total_refunded']), 2),
            'Documenti Fiscali (Fatture/Ricevute)': inv_str,
            'Totale Fatturato (€)': inv_tot,
            'Stato Nota di Credito': stato_nc,
            'Documenti di Storno (NC/Storno)': cn_str,
            'Totale Stornato con NC (€)': cn_tot
        })

df = pd.DataFrame(results)
output_file = "/root/.openclaw/workspace-finance/Verifica_Note_Credito_2026.xlsx"
print(f"Saving to {output_file}...")
df.to_excel(output_file, index=False)

cursor.close()
conn.close()
print("Done!")
