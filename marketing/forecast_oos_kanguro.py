import pymysql
import datetime
import math

skus = ['SET2SZAEPMK', 'DI319USBMIG', 'SV681PPB', 'DI8092MIGS', 'SM9006WOGS', '56714', 'SA800TEX2PZE', 'AB208106V', 'DL190CENGS', '9010K']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

conn_k = pymysql.connect(
    host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
    database='kanguro', cursorclass=pymysql.cursors.DictCursor
)

# 1. Get Sales Velocity from Kanguro (Last 30 days)
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

# 2. Get Current Stock from Kanguro (inv_inventory_stock)
query_stock = f"""
    SELECT p.reference as sku, SUM(s.qty) as quantity
    FROM inv_inventory_stock s
    JOIN dat_product p ON s.product_id = p.id
    WHERE p.reference IN ({sku_list_str})
      AND s.is_deleted = 0
    GROUP BY p.reference
"""
stock_data = {}
with conn_k.cursor() as cursor:
    cursor.execute(query_stock)
    for row in cursor.fetchall():
        stock_data[row['sku']] = float(row['quantity'] or 0)

conn_k.close()

# 3. Calculate OOS Dates
today = datetime.date(2026, 3, 11)

results = []
for sku in skus:
    qty_30d = velocity_data.get(sku, 0)
    stock = stock_data.get(sku, 0)
    
    daily_velocity = qty_30d / 30.0
    
    if stock <= 0:
        days_rem = 0
        oos_date = "OOS / Negativo"
    elif daily_velocity <= 0:
        days_rem = float('inf')
        oos_date = "No Sales"
    else:
        days_rem = stock / daily_velocity
        oos_date = (today + datetime.timedelta(days=math.ceil(days_rem))).strftime('%d/%m/%Y')
        
    results.append({
        'sku': sku,
        'velocity': daily_velocity,
        'stock': stock,
        'days_rem': days_rem,
        'oos_date': oos_date
    })

results.sort(key=lambda x: x['days_rem'] if x['days_rem'] != float('inf') else 999999)

for r in results:
    days_str = f"{math.ceil(r['days_rem'])} gg" if r['days_rem'] != float('inf') else "∞"
    vel = f"{r['velocity']:.1f}/giorno"
    stk = int(r['stock'])
    print(f"- **{r['sku']}** | Stock: {stk} pz | Ritmo: {vel} -> **{r['oos_date']}** (tra {days_str})")
