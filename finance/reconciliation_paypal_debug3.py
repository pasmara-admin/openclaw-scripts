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
df_ppal_pay['Data_PayPal'] = pd.to_datetime(df_ppal_pay['Data'], format='%d/%m/%Y')

conn_k = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro')
query_k = """
SELECT b.full_number AS 'Numero Documento', DATE(b.date) AS 'Data Documento', so.customer_name AS 'Nome', so.customer_email AS 'Email', b.total, so.payment_method_name
FROM bil_document b
JOIN sal_order so ON b.order_id = so.id
WHERE b.date >= '2025-10-01' AND b.date <= '2025-12-05' AND b.is_deleted = b'0' AND so.type_id IN (1, 2)
AND so.payment_method_name = 'PayPal'
"""
df_k = pd.read_sql(query_k, conn_k)
conn_k.close()

df_k['total'] = df_k['total'].astype(float)

# Match basato SOLO SULL'IMPORTO e sulla PROSSIMITA' DELLA DATA (+- 3 giorni)
df_ppal_pay['key'] = 1
df_k['key'] = 1
df_merge = df_ppal_pay.merge(df_k, on='key').drop('key', axis=1)

# Filtriamo per importo esatto
df_merge = df_merge[df_merge['Lordo '] == df_merge['total']]

# Filtriamo per data (+- 3 giorni)
df_k['Data Documento'] = pd.to_datetime(df_k['Data Documento'])
df_merge['Data Documento'] = pd.to_datetime(df_merge['Data Documento'])
df_merge['diff_days'] = (df_merge['Data_PayPal'] - df_merge['Data Documento']).dt.days.abs()
df_merge = df_merge[df_merge['diff_days'] <= 3]

# Ordiniamo per diff_days così prendiamo il match temporale più vicino
df_merge = df_merge.sort_values(by=['Codice transazione', 'diff_days'])

# De-duplicazione
df_merge = df_merge.drop_duplicates(subset=['Codice transazione'], keep='first')
df_merge = df_merge.drop_duplicates(subset=['Numero Documento'], keep='first')

print(f"Match forzato per IMPORTO + DATA (+-3gg): {len(df_merge)}")
