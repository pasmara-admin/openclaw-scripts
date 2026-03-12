import subprocess
import datetime
import math
import sys

skus = ['SET2SZAEPMK', 'DI319USBMIG', 'SV681PPB', 'DI8092MIGS', 'SM9006WOGS', '56714', 'SA800TEX2PZE', 'AB208106V', 'DL190CENGS']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

def run_query(host, user, pwd, db, query):
    cmd = [
        "mysql", "--skip-ssl-verify-server-cert", "-h", host, "-u", user, f"-p{pwd}", db,
        "-B", "-N", "-e", query
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}", file=sys.stderr)
        sys.exit(1)
    return res.stdout.strip().split('\n')

# 1. Get Sales Velocity from Kanguro (Last 30 days)
q_velocity = f"""
    SELECT r.reference, SUM(r.qty)
    FROM sal_order_row r
    JOIN sal_order o ON r.order_id = o.id
    WHERE o.date >= DATE_SUB('2026-03-11', INTERVAL 30 DAY)
      AND o.state_id NOT IN ('00', '01')
      AND o.is_deleted = 0 AND r.is_deleted = 0
      AND r.reference IN ({sku_list_str})
    GROUP BY r.reference;
"""
vel_lines = run_query('34.38.166.212', 'john', '3rmiCyf6d~MZDO41', 'kanguro', q_velocity)
velocity_data = {}
for line in vel_lines:
    if not line: continue
    parts = line.split('\t')
    velocity_data[parts[0]] = float(parts[1])

# 2. Get Current Stock from Prestashop
q_stock = f"""
    SELECT p.reference as sku, sa.quantity
    FROM ps_product p
    JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
    WHERE p.reference IN ({sku_list_str})
    UNION
    SELECT pa.reference as sku, sa.quantity
    FROM ps_product_attribute pa
    JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
    WHERE pa.reference IN ({sku_list_str});
"""
stk_lines = run_query('62.84.190.199', 'john', 'pqARa6aRozi6I', 'produceshop', q_stock)
stock_data = {}
for line in stk_lines:
    if not line: continue
    parts = line.split('\t')
    stock_data[parts[0]] = int(parts[1])

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
