import pymysql
import sys
from openpyxl import Workbook
import subprocess

skus_raw = """SGA800SNJY
SGA800SNJB
SGA800SNJR
SGA046ALTN
SGA046ALTV
SGA046ALTB
SGA046ALTG
SGA054CHIA
SGA054CHIG
SGA054CHIM
SGA054CHIN
SGA054CHIB
SGA800NEWN
SGA800NEWB
SGA800AMAN
SGA800AMAA
SGA800AMAB
SGA053LASB
BIS70QUANER
BIS70ROTBIA
SGA800SFRA
SGA054HOLG
SGA800DALS"""

skus = [s.strip() for s in skus_raw.split('\n') if s.strip()]
sku_list_str = ', '.join([f"'{s}'" for s in skus])

# 1. Get Stock from PS
ps_stock = {}
query_ps = f"""
    SELECT p.reference as sku, SUM(sa.quantity) as quantity
    FROM ps_product p
    JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
    WHERE sa.id_shop = 1 AND p.reference IN ({sku_list_str})
    GROUP BY p.reference
    UNION
    SELECT pa.reference as sku, SUM(sa.quantity) as quantity
    FROM ps_product_attribute pa
    JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
    WHERE sa.id_shop = 1 AND pa.reference IN ({sku_list_str})
    GROUP BY pa.reference
"""
cmd = ["mysql", "--skip-ssl-verify-server-cert", "-h", "62.84.190.199", "-u", "john", "-ppqARa6aRozi6I", "produceshop", "-B", "-N", "-e", query_ps]
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

if res.returncode == 0:
    for line in res.stdout.strip().split('\n'):
        if not line: continue
        parts = line.split('\t')
        if len(parts) >= 2:
            try:
                ps_stock[parts[0]] = int(parts[1])
            except:
                pass

# 2. Get Sales, Last Price and WAC from Kanguro
conn_k = pymysql.connect(
    host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
    database='kanguro', cursorclass=pymysql.cursors.DictCursor
)
sales_data = {}
price_data = {}
wac_data = {}

with conn_k.cursor() as cursor:
    # A) Total sold since Oct 2025
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
        
    # B) Last selling price in Italy
    query_price = f"""
        SELECT r.reference as sku, (r.total_price / r.qty) as unit_price
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        WHERE r.id IN (
            SELECT MAX(r2.id)
            FROM sal_order_row r2
            JOIN sal_order o2 ON r2.order_id = o2.id
            WHERE r2.reference IN ({sku_list_str})
              AND o2.delivery_country_id = 10
              AND o2.state_id NOT IN ('00', '01')
              AND r2.is_deleted = 0
              AND r2.qty > 0
            GROUP BY r2.reference
        )
    """
    cursor.execute(query_price)
    for row in cursor.fetchall():
        price_data[row['sku']] = float(row['unit_price'] or 0)
        
    # C) Original WAC from inv_weighted_average_cost (Original Currency)
    # Using the latest entry for each product_id
    query_wac = f"""
        SELECT p.reference, w.price, w.currency
        FROM inv_weighted_average_cost w
        JOIN dat_product p ON w.product_id = p.id
        WHERE w.id IN (
            SELECT MAX(w2.id)
            FROM inv_weighted_average_cost w2
            JOIN dat_product p2 ON w2.product_id = p2.id
            WHERE p2.reference IN ({sku_list_str}) AND w2.is_deleted = 0
            GROUP BY p2.reference
        )
    """
    cursor.execute(query_wac)
    for row in cursor.fetchall():
        wac_data[row['reference']] = {
            'price': float(row['price'] or 0),
            'currency': row['currency'] or 'EUR'
        }

conn_k.close()

wb = Workbook()
ws = wb.active
ws.title = "Report INFO"
ws.append(["SKU", "Giacenza Attuale (PS)", "Venduti (da Ottobre 2025)", "Prezzo Vendita (Ultimo Ordine IT) €", "WAC Valuta Originale", "Valuta"])

for sku in skus:
    stock = ps_stock.get(sku, 0)
    sold = sales_data.get(sku, 0)
    price = price_data.get(sku, 0.0)
    wac_info = wac_data.get(sku, {'price': 0.0, 'currency': 'N/A'})
    ws.append([sku, stock, sold, round(price, 2), round(wac_info['price'], 2), wac_info['currency']])

file_path = "/root/.openclaw/workspace-marketing/Report_INFO_Massivo_WAC_Original.xlsx"
wb.save(file_path)
print(f"Excel saved to {file_path}")

print("Anteprima WAC Originale (Risultato):")
for sku in skus:
    w = wac_data.get(sku, {'price': 0.0, 'currency': 'N/A'})
    print(f"- {sku}: {w['price']:.2f} {w['currency']}")
