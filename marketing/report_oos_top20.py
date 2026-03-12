import pymysql
import datetime
import math
import sys
import subprocess

# 1. Get Sales Velocity & Revenue from Kanguro
conn_k = pymysql.connect(
    host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
    database='kanguro', cursorclass=pymysql.cursors.DictCursor
)

# Find Drop SKUs
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

# Get Sales Data (last 30 days)
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

# 2. Get Stock from Prestashop
def run_query_ps(query):
    cmd = [
        "mysql", "--skip-ssl-verify-server-cert", "-h", "62.84.190.199", "-u", "john", f"-ppqARa6aRozi6I", "produceshop",
        "-B", "-N", "-e", query
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}", file=sys.stderr)
        sys.exit(1)
    return res.stdout.strip().split('\n')

q_stock = """
    SELECT p.reference as sku, SUM(sa.quantity) as quantity
    FROM ps_product p
    JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
    WHERE sa.id_shop = 1 AND p.reference != ''
    GROUP BY p.reference
    UNION
    SELECT pa.reference as sku, SUM(sa.quantity) as quantity
    FROM ps_product_attribute pa
    JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
    WHERE sa.id_shop = 1 AND pa.reference != ''
    GROUP BY pa.reference;
"""
stk_lines = run_query_ps(q_stock)
stock_data = {}
for line in stk_lines:
    if not line: continue
    parts = line.split('\t')
    if len(parts) == 2:
        try:
            stock_data[parts[0]] = int(parts[1])
        except ValueError:
            pass

# 3. Calculate and sort
today = datetime.date(2026, 3, 11)
results = []

for sku, data in sales_data.items():
    qty_30d = data['qty_30d']
    rev = data['revenue']
    
    if qty_30d <= 0:
        continue
        
    stock = stock_data.get(sku, 0)
    
    # We want products that are going out of stock soon.
    # Exclude those that are already <= 0 since they are ALREADY out of stock.
    # Actually, we can include them but prioritize those with > 0 stock that are running out.
    # Let's filter for stock > 0 to answer "andranno fuori stock" (WILL go out of stock).
    if stock <= 0:
        continue
        
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

# Sort by days remaining ascending
results.sort(key=lambda x: x['days_rem'])

# Output top 20
print("Top 20 prodotti (NO Drop) prossimi all'esaurimento (Stock > 0):")
for i, r in enumerate(results[:20]):
    days_str = f"{math.ceil(r['days_rem'])} gg"
    print(f"{i+1}. **{r['sku']}** | Fatturato: €{r['revenue']:.2f} | Stock: {r['stock']} pz | OOS: {r['oos_date']} (tra {days_str})")
