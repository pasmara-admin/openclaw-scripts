import pandas as pd
import pymysql
from datetime import datetime

# Estrazione esatta usata da Report_Revenue
connection = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro')

query_rev = """
SELECT 
    b.full_number AS 'Invoice Number',
    b.order_number AS 'Order Number',
    DATE(b.date) AS 'Invoice Date',
    t.name AS 'Order Sales Channel',
    so.payment_method_name AS 'Order Payment Method',
    br.total_price_tax_incl AS 'Revenue Gross',
    b.type_id
FROM bil_document b
LEFT JOIN bil_document_row br ON b.id = br.document_id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE b.date >= '2025-10-01 00:00:00' 
  AND b.date <= '2025-11-30 23:59:59'
  AND b.is_deleted = b'0'
  AND so.type_id = 2
"""
df_rev = pd.read_sql(query_rev, connection)
connection.close()

mask_nc_rev = df_rev['type_id'].isin([2, 4])
df_rev.loc[mask_nc_rev, 'Revenue Gross'] = -df_rev.loc[mask_nc_rev, 'Revenue Gross'].abs()

# Raggruppo per Metodo Pagamento
df_rev_agg = df_rev.groupby('Order Payment Method')['Revenue Gross'].sum().reset_index()
print("--- Totali da Report_Revenue per Metodo di Pagamento ---")
print(df_rev_agg.sort_values('Revenue Gross', ascending=False).to_string())

print("\n--- Totali da Master Reconciliation (Fatture) ---")
f = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_Finale.xlsx'
df_rec = pd.read_excel(f)
df_rec_agg = df_rec.groupby('Metodo Pagamento')['Fatturato Lordo (Kanguro)'].sum().reset_index()
print(df_rec_agg.sort_values('Fatturato Lordo (Kanguro)', ascending=False).to_string())

