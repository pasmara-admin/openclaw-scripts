import pymysql
import datetime
import math

skus = ['SET2SZAEPMK', 'DI319USBMIG', 'SV681PPB', 'DI8092MIGS', 'SM9006WOGS', '56714', 'SA800TEX2PZE', 'AB208106V', 'DL190CENGS', '9010K']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

# 1. Get Sales Velocity from Kanguro (Last 30 days)
conn_k = pymysql.connect(
    host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
    database='kanguro', cursorclass=pymysql.cursors.DictCursor
)
query_velocity = f"""
    SELECT r.reference as sku, SUM(r.qty) as total_qty
    FROM sal_order_row r
    JOIN sal_order o ON r.order_id = o.id
    WHERE o.date >= DATE_SUB('2026-03-11', INTERVAL 30 DAY)
      AND o.state_id NOT IN ('00', '01')
      AND o.is_deleted = 0 AND r.is_deleted = 0
      AND r.reference IN ({sku_list_str})
    GROUP BY r.reference
"""
velocity_data = {}
with conn_k.cursor() as cursor:
    cursor.execute(query_velocity)
    for row in cursor.fetchall():
        velocity_data[row['sku']] = float(row['total_qty'] or 0)
conn_k.close()

# 2. Get Current Stock from Prestashop
conn_p = pymysql.connect(
    host='62.84.190.199', user='john', password='pqARa6aRozi6I',
    database='produceshop', cursorclass=pymysql.cursors.DictCursor
)
query_stock = f"""
    SELECT p.reference as sku, sa.quantity
    FROM ps_product p
    JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
    WHERE p.reference IN ({sku_list_str})
    UNION
    SELECT pa.reference as sku, sa.quantity
    FROM ps_product_attribute pa
    JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
    WHERE pa.reference IN ({sku_list_str})
"""
stock_data = {}
with conn_p.cursor() as cursor:
    cursor.execute(query_stock)
    for row in cursor.fetchall():
        stock_data[row['sku']] = int(row['quantity'] or 0)
conn_p.close()

# 3. Calculate OOS Dates
today = datetime.date(2026, 3, 11)
print("SKU | Avg Daily Sales (30d) | Current Stock | Est. OOS Date | Days Remaining")
print("-" * 80)

results = []
for sku in skus:
    qty_30d = velocity_data.get(sku, 0)
    stock = stock_data.get(sku, 0)
    
    daily_velocity = qty_30d / 30.0
    
    if stock <= 0:
        days_rem = 0
        oos_date = "Out of Stock"
    elif daily_velocity <= 0:
        days_rem = float('inf')
        oos_date = "No Sales (30d)"
    else:
        days_rem = stock / daily_velocity
        oos_date = (today + datetime.timedelta(days=math.ceil(days_rem))).strftime('%Y-%m-%d')
        
    results.append({
        'sku': sku,
        'velocity': daily_velocity,
        'stock': stock,
        'days_rem': days_rem,
        'oos_date': oos_date
    })

# Sort by days remaining (ascending)
results.sort(key=lambda x: x['days_rem'] if x['days_rem'] != float('inf') else 999999)

for r in results:
    days_str = f"{r['days_rem']:.1f}" if r['days_rem'] != float('inf') else "∞"
    print(f"{r['sku']:<15} | {r['velocity']:<21.2f} | {r['stock']:<13} | {r['oos_date']:<13} | {days_str}")
