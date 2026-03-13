import pandas as pd
import pymysql
import warnings
warnings.filterwarnings('ignore')

f = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v10_Intesa_All.xlsx'
df_docs = pd.read_excel(f)

# File Paypal di Novembre
file_paypal_nov = '/root/.openclaw/media/inbound/202511_-_Paypal---537736e9-2122-41c6-b25b-97b75df0dc08.csv'
df_ppal = pd.read_csv(file_paypal_nov)

df_ppal_pay = df_ppal[df_ppal['Descrizione'] == 'Pagamento Express Checkout'].copy()
df_ppal_pay['Lordo '] = df_ppal_pay['Lordo '].str.replace('.', '').str.replace(',', '.').astype(float)
df_ppal_pay['Tariffa '] = df_ppal_pay['Tariffa '].str.replace('.', '').str.replace(',', '.').astype(float).abs()
df_ppal_pay['Indirizzo email mittente'] = df_ppal_pay['Indirizzo email mittente'].astype(str).str.lower().str.strip()

print("Connessione a Kanguro per incrociare gli ordini PayPal di Novembre...")
conn_k = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro')
query_k = """
SELECT b.full_number AS 'Numero Documento', b.order_number AS 'Numero Ordine', so.customer_email AS 'Indirizzo email mittente', b.total, so.payment_method_name
FROM bil_document b
JOIN sal_order so ON b.order_id = so.id
WHERE b.date >= '2025-10-01' AND b.date <= '2025-11-30' AND b.is_deleted = b'0' AND so.type_id IN (1, 2)
"""
df_k = pd.read_sql(query_k, conn_k)
conn_k.close()

df_k['total'] = df_k['total'].astype(float)
df_k['Indirizzo email mittente'] = df_k['Indirizzo email mittente'].astype(str).str.lower().str.strip()

# Match on Email + Exact Amount
df_bridge = df_ppal_pay.merge(df_k, left_on=['Indirizzo email mittente', 'Lordo '], right_on=['Indirizzo email mittente', 'total'], how='inner')
df_bridge = df_bridge.drop_duplicates(subset=['Codice transazione'])

matched_count = 0
for idx, row in df_bridge.iterrows():
    num_doc = str(row['Numero Documento'])
    mask = df_docs['Numero Documento'].astype(str) == num_doc
    if mask.any() and pd.isna(df_docs.loc[mask, 'Gateway Match'].iloc[0]):
        df_docs.loc[mask, 'Incasso Gateway (€)'] += float(row['Lordo '])
        df_docs.loc[mask, 'Commissioni Gateway (€)'] += float(row['Tariffa '])
        df_docs.loc[mask, 'Gateway Match'] = 'PayPal'
        df_docs.loc[mask, 'Metodo Pagamento v2'] = 'PayPal'
        matched_count += 1

print(f"Match PayPal (Novembre) completato: {matched_count} transazioni incrociate su {len(df_ppal_pay)} totali in CSV.")

df_docs['Incasso Netto (€)'] = df_docs['Incasso Gateway (€)'] - df_docs['Commissioni Gateway (€)']
df_docs['Credito da Incassare (€)'] = df_docs['Fatturato Lordo (Kanguro)'] - df_docs['Incasso Gateway (€)']

out_file = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v11_PayPal_Nov.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_docs.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)

print("Export completato con PayPal Novembre.")
