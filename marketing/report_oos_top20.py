import pymysql
import datetime
import math
import sys

# Read PS stock from dumped file
stock_data = {}
try:
    with open('/tmp/ps_stock_all.tsv', 'r') as f:
        next(f) # skip header
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split('\t')
            if len(parts) == 2:
                try:
                    stock_data[parts[0]] = int(parts[1])
                except ValueError:
                    pass
except Exception as e:
    print(f"Error reading stock file: {e}")
    sys.exit(1)

# 1. Get Sales Velocity & Revenue from Kanguro
conn_k = pymysql.connect(
    host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
    database='kanguro', cursorclass=pymysql.cursors.DictCursor
)
query_drop = """
    SELECT DISTINCT p.reference
    FROM dat_product p
    JOIN dat_product_label pl ON p.id = pl.product_id
    JOIN dat_label l ON pl.label_id = l.id
    WHERE l.name LIKE '%drop%'
"""
drop_skus = set()
with conn_k.cursor() as cursor:
    cursor.execute(query_drop)
    for row in cursor.fetchall():
        if row['reference']:
            drop_skus.add(row['reference'])

query_sales = """
    SELECT r.reference as sku, SUM(r.qty) as qty_30d, SUM(r.total_price) as revenue
    FROM sal_order_row r
    JOIN sal_order o ON r.order_id = o.id
    WHERE o.date >= DATE_SUB('2026-03-11', INTERVAL 30 DAY)
      AND o.state_id NOT IN ('00', '01')
      AND o.is_deleted = 0 AND r.is_deleted = 0
      AND r.reference IS NOT NULL AND r.reference != ''
    GROUP BY r.reference
"""
sales_data = {}
with conn_k.cursor() as cursor:
    cursor.execute(query_sales)
    for row in cursor.fetchall():
        sku = row['sku']
        if sku not in drop_skus:
            sales_data[sku] = {
                'qty_30d': float(row['qty_30d'] or 0),
                'revenue': float(row['revenue'] or 0)
            }
conn_k.close()

today = datetime.date(2026, 3, 11)
results = []
for sku, data in sales_data.items():
    qty_30d = data['qty_30d']
    rev = data['revenue']
    if qty_30d <= 0: continue
    stock = stock_data.get(sku, 0)
    
    # We want things that WILL go out of stock (stock > 0 currently)
    if stock <= 0: continue
        
    daily_velocity = qty_30d / 30.0
    days_rem = stock / daily_velocity
    oos_date = (today + datetime.timedelta(days=math.ceil(days_rem))).strftime('%d/%m/%Y')
    
    results.append({
        'sku': sku,
        'revenue': rev,
        'velocity': daily_velocity,
        'stock': stock,
        'days_rem': days_rem,
        'oos_date': oos_date
    })

results.sort(key=lambda x: x['days_rem'])
for i, r in enumerate(results[:20]):
    days_str = f"{math.ceil(r['days_rem'])} gg"
    print(f"{i+1}. **{r['sku']}** | Vendita Media: {r['velocity']:.1f} pz/g | Fatturato (30gg): €{r['revenue']:.2f} | Stock: {r['stock']} pz | OOS: {r['oos_date']} (tra {days_str})")
