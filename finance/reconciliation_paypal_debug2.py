import pandas as pd
import pymysql
import warnings
warnings.filterwarnings('ignore')

f = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v10_Intesa_All.xlsx'
df_docs = pd.read_excel(f)

file_paypal_nov = '/root/.openclaw/media/inbound/202511_-_Paypal---537736e9-2122-41c6-b25b-97b75df0dc08.csv'
df_ppal = pd.read_csv(file_paypal_nov)

df_ppal_pay = df_ppal[df_ppal['Descrizione'] == 'Pagamento Express Checkout'].copy()
df_ppal_pay['Lordo '] = df_ppal_pay['Lordo '].str.replace('.', '').str.replace(',', '.').astype(float)
df_ppal_pay['Tariffa '] = df_ppal_pay['Tariffa '].str.replace('.', '').str.replace(',', '.').astype(float).abs()

# Proviamo a usare solo Nome e Cognome, a volte l'email su PayPal è diversa da quella usata in Kanguro per l'ordine!
df_ppal_pay['Nome'] = df_ppal_pay['Nome'].astype(str).str.lower().str.strip()

conn_k = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro')
query_k = """
SELECT b.full_number AS 'Numero Documento', so.customer_name AS 'Nome', b.total, so.payment_method_name
FROM bil_document b
JOIN sal_order so ON b.order_id = so.id
WHERE b.date >= '2025-10-01' AND b.date <= '2025-11-30' AND b.is_deleted = b'0' AND so.type_id IN (1, 2)
AND so.payment_method_name = 'PayPal'
"""
df_k = pd.read_sql(query_k, conn_k)
conn_k.close()

df_k['total'] = df_k['total'].astype(float)
df_k['Nome'] = df_k['Nome'].astype(str).str.lower().str.strip()

# Match on Name + Exact Amount
df_bridge_name = df_ppal_pay.merge(df_k, left_on=['Nome', 'Lordo '], right_on=['Nome', 'total'], how='inner')
df_bridge_name = df_bridge_name.drop_duplicates(subset=['Codice transazione'])

print(f"Match dopo de-duplicazione via NOME: {len(df_bridge_name)}")
