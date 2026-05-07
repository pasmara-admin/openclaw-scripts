import pandas as pd
import pymysql
from datetime import datetime, timedelta

# Database connection
connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)

# Date range
start_month = '2026-04-01'
end_date = '2026-04-08'
last_week_start = '2026-04-02' # Last 7 days including yesterday

query = f"""
SELECT 
    b.date AS 'date',
    t.name AS 'marketplace',
    b.destination_country AS 'country',
    br.total_price_tax_incl AS 'revenue_gross'
FROM bil_document b
LEFT JOIN bil_document_row br ON b.id = br.document_id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE b.date >= '{start_month}' AND b.date <= '{end_date}' 
  AND b.is_deleted = 0 AND br.is_deleted = 0;
"""

df = pd.read_sql(query, connection)
connection.close()

if df.empty:
    print("No data found for the selected period.")
    exit(1)

# Normalization
country_map = {
    'Francia': 'France', 
    'Italia': 'Italy', 
    'España': 'Spain', 
    'Spagna': 'Spain',
    'Deutschland': 'Germany',
    'Germania': 'Germany'
}
df['country'] = df['country'].replace(country_map)

# Full report generation (with more columns)
query_full = f"""
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
WHERE b.date >= '{start_month}' AND b.date <= '{end_date}' 
  AND b.is_deleted = 0 AND br.is_deleted = 0;
"""
# Re-open connection for full data
connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)
df_full = pd.read_sql(query_full, connection)
connection.close()

file_path = f'/tmp/Report_Revenue_Aprile_2026_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
df_full.to_excel(file_path, index=False)

# Analysis
# 1. Total Monthly (1-8 April)
total_month = df['revenue_gross'].sum()

# 2. Last Week (2-8 April)
df['date'] = pd.to_datetime(df['date'])
df_week = df[df['date'] >= last_week_start]
total_week = df_week['revenue_gross'].sum()

# 3. By Country (Month)
country_month = df.groupby('country')['revenue_gross'].sum().sort_values(ascending=False).head(5)
# 4. By Marketplace (Month)
mp_month = df.groupby('marketplace')['revenue_gross'].sum().sort_values(ascending=False).head(5)

# Analysis summary for email body
analysis = f"""
Analisi Fatturato (01/04/2026 - 08/04/2026):
- Totale Mese (MTD): €{total_month:,.2f}
- Ultima Settimana (02/04 - 08/04): €{total_week:,.2f}

Top 5 Paesi (Mese):
"""
for country, val in country_month.items():
    analysis += f"- {country}: €{val:,.2f}\n"

analysis += "\nTop 5 Marketplace (Mese):\n"
for mp, val in mp_month.items():
    analysis += f"- {mp}: €{val:,.2f}\n"

print("FILE_PATH:" + file_path)
print("ANALYSIS_START")
print(analysis)
print("ANALYSIS_END")
