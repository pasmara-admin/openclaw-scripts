import pymysql
import sys
from openpyxl import Workbook
import subprocess

skus = ['SE865V', 'SE867N', 'SE865G', 'SE867V', 'SE825GS', 'SE892GC', 'SE867GS']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

ps_data = {}
query_ps = f"""
    SELECT p.reference as sku, sa.quantity, ps.price as base_price, 0 as impact_price, sp.reduction, sp.reduction_type
    FROM ps_product p
    JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
    JOIN ps_product_shop ps ON p.id_product = ps.id_product AND ps.id_shop = 1
    LEFT JOIN ps_specific_price sp ON p.id_product = sp.id_product AND sp.id_shop IN (0, 1) AND sp.id_product_attribute = 0
    WHERE sa.id_shop = 1 AND p.reference IN ({sku_list_str})
    UNION
    SELECT pa.reference as sku, sa.quantity, ps.price as base_price, pas.price as impact_price, sp.reduction, sp.reduction_type
    FROM ps_product_attribute pa
    JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
    JOIN ps_product_shop ps ON pa.id_product = ps.id_product AND ps.id_shop = 1
    JOIN ps_product_attribute_shop pas ON pa.id_product_attribute = pas.id_product_attribute AND pas.id_shop = 1
    LEFT JOIN ps_specific_price sp ON pa.id_product = sp.id_product AND sp.id_shop IN (0, 1) AND (sp.id_product_attribute = 0 OR sp.id_product_attribute = pa.id_product_attribute)
    WHERE sa.id_shop = 1 AND pa.reference IN ({sku_list_str})
"""
cmd = ["mysql", "--skip-ssl-verify-server-cert", "-h", "62.84.190.199", "-u", "john", "-ppqARa6aRozi6I", "produceshop", "-B", "-N", "-e", query_ps]
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if res.returncode != 0:
    print(f"Error reading PS: {res.stderr}")
    sys.exit(1)

for line in res.stdout.strip().split('\n'):
    if not line: continue
    parts = line.split('\t')
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
ws.append(["SKU", "Giacenza (Real-Time PS)", "Venduti (da Ott 2025)", "Prezzo Scontato (€)"])

for sku in skus:
    data_ps = ps_data.get(sku, {'stock': 0, 'price': 0.0})
    sold = sales_data.get(sku, 0)
    ws.append([sku, data_ps['stock'], sold, round(data_ps['price'], 2)])

wb.save("/root/.openclaw/workspace-marketing/Report_INFO_Simone.xlsx")
print("Excel saved to /root/.openclaw/workspace-marketing/Report_INFO_Simone.xlsx")
