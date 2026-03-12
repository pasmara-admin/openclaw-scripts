import pymysql
import sys
from openpyxl import Workbook

skus = ['SE865V', 'SE867N', 'SE865G', 'SE867V', 'SE825GS', 'SE892GC', 'SE867GS']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

ps_data = {}
with open('/tmp/ps_discount_info.tsv', 'r') as f:
    next(f)
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 6:
            sku = parts[0]
            stock = int(parts[1])
            base_price = float(parts[2])
            impact_price = float(parts[3])
            reduction_str = parts[4]
            reduction_type = parts[5]
            
            final_price = base_price + impact_price
            if reduction_str and reduction_str != 'NULL':
                reduction = float(reduction_str)
                if reduction_type == 'amount':
                    final_price -= reduction
                elif reduction_type == 'percentage':
                    final_price -= (final_price * reduction)
                    
            ps_data[sku] = {
                'stock': stock,
                'price': final_price
            }

conn_k = pymysql.connect(
    host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
    database='kanguro', cursorclass=pymysql.cursors.DictCursor
)
sales_data = {}
with conn_k.cursor() as cursor:
    query_sales = f"""
        SELECT r.reference as sku, SUM(r.qty) as qty_sold
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        WHERE o.date >= '2025-10-01'
          AND o.state_id NOT IN ('00', '01')
          AND o.is_deleted = 0 AND r.is_deleted = 0
          AND r.reference IN ({sku_list_str})
        GROUP BY r.reference
    """
    cursor.execute(query_sales)
    for row in cursor.fetchall():
        sales_data[row['sku']] = int(row['qty_sold'] or 0)
conn_k.close()

wb = Workbook()
ws = wb.active
ws.title = "Report INFO"
ws.append(["SKU", "Giacenza (Real-Time PS)", "Venduti (da Ottobre 2025)", "Prezzo Scontato Attuale (€)"])

for sku in skus:
    data_ps = ps_data.get(sku, {'stock': 0, 'price': 0.0})
    sold = sales_data.get(sku, 0)
    ws.append([sku, data_ps['stock'], sold, round(data_ps['price'], 2)])

file_path = "/root/.openclaw/workspace-marketing/Report_INFO_Simone.xlsx"
wb.save(file_path)
print(f"Excel saved to {file_path}")
