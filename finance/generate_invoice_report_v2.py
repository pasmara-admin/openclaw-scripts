import pandas as pd
import pymysql
from datetime import datetime
import sys

# Connect to database
connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)

start_date = sys.argv[1] if len(sys.argv) > 1 else '2026-03-01'
end_date = sys.argv[2] if len(sys.argv) > 2 else '2026-03-13'

query = f"""
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
WHERE b.date >= '{start_date}' AND b.date <= '{end_date}' AND b.is_deleted = 0 AND br.is_deleted = 0
"""

df = pd.read_sql(query, connection)
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
file_path = f'/root/.openclaw/workspace-finance/Report_Revenue_{timestamp}.xlsx'
df.to_excel(file_path, index=False)
connection.close()
print(file_path)
