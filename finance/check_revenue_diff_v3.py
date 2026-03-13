import pandas as pd
import pymysql
from datetime import datetime

# Estrazione esatta usata da Report_Revenue
connection = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro')

# La VERA VERA estrazione del Report Revenue usa `bil_document_row` SUM per il lordo, ma noi usiamo b.total
# Lascia stare bil_document_row. Facciamo la VERA estrazione di kanguro del Report_Revenue storico
query_rev = """
SELECT 
    b.full_number AS 'Invoice Number',
    b.total AS 'Revenue Gross',
    b.type_id,
    so.payment_method_name AS 'Order Payment Method'
FROM bil_document b
LEFT JOIN sal_order so ON b.order_id = so.id
WHERE b.date >= '2025-10-01 00:00:00' 
  AND b.date <= '2025-11-30 23:59:59'
  AND b.is_deleted = b'0'
  AND so.type_id = 2
"""
df_rev = pd.read_sql(query_rev, connection)
connection.close()

mask_nc_rev = df_rev['type_id'].isin([2, 4])
df_rev.loc[mask_nc_rev, 'Revenue Gross'] = -df_rev.loc[mask_nc_rev, 'Revenue Gross'].abs()

df_rev['Order Payment Method'] = df_rev['Order Payment Method'].replace({
    'Apple Pay': 'Payplug',
    'American Express': 'Payplug',
    'Satispay': 'Payplug',
    'MyBank': 'Payplug',
    'PayPlug': 'Payplug',
    'Banküberweisung': 'Bonifico bancario',
    'Transfert bancaire': 'Bonifico bancario',
    'Pagos por transferencia bancaria': 'Bonifico bancario',
    'Bonifico Bancario': 'Bonifico bancario'
})

df_rev_agg = df_rev.groupby('Order Payment Method')['Revenue Gross'].sum().reset_index()
print("--- Totali da Report_Revenue Storico per Ordine (usando solo il totale testata Kanguro) ---")
print(df_rev_agg.sort_values('Revenue Gross', ascending=False).to_string())

