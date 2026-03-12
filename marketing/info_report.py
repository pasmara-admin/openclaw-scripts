import pymysql
import sys

skus = ['SE865V', 'SE867N', 'SE865G', 'SE867V', 'SE825GS', 'SE892GC', 'SE867GS']
sku_list_str = ', '.join([f"'{s}'" for s in skus])

# 1. Prestashop Data (Stock & Price)
conn_p = pymysql.connect(
    host='62.84.190.199', user='john', password='pqARa6aRozi6I',
    database='produceshop', cursorclass=pymysql.cursors.DictCursor
)

ps_data = {}
with conn_p.cursor() as cursor:
    # Get base product prices and stock
    query_base = f"""
        SELECT p.reference as sku, sa.quantity, ps.price
        FROM ps_product p
        JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
        JOIN ps_product_shop ps ON p.id_product = ps.id_product AND ps.id_shop = 1
        WHERE sa.id_shop = 1 AND p.reference IN ({sku_list_str})
    """
    cursor.execute(query_base)
    for row in cursor.fetchall():
        ps_data[row['sku']] = {
            'stock': int(row['quantity'] or 0),
            'price': float(row['price'] or 0)
        }
        
    # Get variant prices and stock
    query_var = f"""
        SELECT pa.reference as sku, sa.quantity, ps.price as base_price, pas.price as impact_price
        FROM ps_product_attribute pa
        JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
        JOIN ps_product_shop ps ON pa.id_product = ps.id_product AND ps.id_shop = 1
        JOIN ps_product_attribute_shop pas ON pa.id_product_attribute = pas.id_product_attribute AND pas.id_shop = 1
        WHERE sa.id_shop = 1 AND pa.reference IN ({sku_list_str})
    """
    cursor.execute(query_var)
    for row in cursor.fetchall():
        sku = row['sku']
        stock = int(row['quantity'] or 0)
        # PS final price is roughly base_price + impact_price
        price = float(row['base_price'] or 0) + float(row['impact_price'] or 0)
        ps_data[sku] = {
            'stock': stock,
            'price': price
        }
conn_p.close()

# 2. Kanguro Data (Sales since Oct 2025 - assuming Ry meant 2025 since we are in March 2026)
# Actually, I'll just check both '2025-10-01' and '2026-10-01' just to be sure. I'll use 2025-10-01
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

print("SKU | Stock Attuale | Venduti (Da Ott 2025) | Prezzo (No IVA)")
print("-" * 65)
for sku in skus:
    data_ps = ps_data.get(sku, {'stock': 0, 'price': 0.0})
    sold = sales_data.get(sku, 0)
    print(f"**{sku}** | Stock: {data_ps['stock']} pz | Venduti: {sold} pz | Prezzo: €{data_ps['price']:.2f}")
