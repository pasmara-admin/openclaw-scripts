import pandas as pd
import pymysql
from datetime import datetime

# Connect to database
connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)

query = """
SELECT 
    b.order_number AS 'Order Number',
    b.date AS 'Invoice Date',
    t.name AS 'Order Sales Channel',
    b.destination_country AS 'Order Shipping Country',
    so.payment_method_name AS 'Order Payment Method',
    b.customer_name AS 'Customer Name',
    br.reference AS 'Item Reference',
    br.description AS 'Item Name',
    br.qty AS 'Sold Quantity',
    br.total_price_tax_excl AS 'Revenue Net',
    br.total_tax AS 'Vat',
    br.tax_rate AS 'Vat Percentage',
    br.total_price_tax_incl AS 'Revenue Gross'
FROM bil_document b
LEFT JOIN bil_document_row br ON b.id = br.document_id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE b.date >= '2026-02-27' AND b.date <= '2026-03-05' AND b.is_deleted = 0 AND br.is_deleted = 0
LIMIT 500;
"""

df = pd.read_sql(query, connection)
file_path = f'/root/.openclaw/workspace-finance/Test_Report_Kanguro_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
df.to_excel(file_path, index=False)
connection.close()
print(file_path)
