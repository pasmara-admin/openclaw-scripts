import pymysql

skus = ['SE865V', 'SE867N', 'SE865G', 'SE867V', 'SE825GS', 'SE892GC', 'SE867GS']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

ps_data = {}
with open('/tmp/ps_info.tsv', 'r') as f:
    next(f)
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 3:
            ps_data[parts[0]] = {
                'stock': int(parts[1]),
                'price': float(parts[2])
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

print("Ecco il report richiesto:")
print("")
for sku in skus:
    data = ps_data.get(sku, {'stock': 0, 'price': 0.0})
    sold = sales_data.get(sku, 0)
    # The DB price is usually ex VAT, let's just label it "Prezzo a sistema"
    print(f"- **{sku}** | Giacenza: {data['stock']} pz | Venduti (da Ottobre): {sold} pz | Prezzo Base: €{data['price']:.2f}")
