import pymysql

sku = 'sa800texe'
sku_upper = sku.upper()

# PS Stock
conn_ps = pymysql.connect(host='62.84.190.199', user='john', password='pqARa6aRozi6I', database='produceshop', cursorclass=pymysql.cursors.DictCursor)
with conn_ps.cursor() as cur:
    cur.execute("""
        SELECT SUM(s.quantity) as qty
        FROM ps_stock_available s 
        LEFT JOIN ps_product_attribute pa ON s.id_product = pa.id_product AND s.id_product_attribute = pa.id_product_attribute 
        LEFT JOIN ps_product p ON s.id_product = p.id_product
        WHERE (pa.reference = %s OR p.reference = %s) AND s.id_shop = 1
    """, (sku, sku))
    stock = cur.fetchone()['qty']
conn_ps.close()

# Kanguro DB
conn_k = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro', cursorclass=pymysql.cursors.DictCursor)
with conn_k.cursor() as cur:
    # Sales
    cur.execute("""
        SELECT SUM(sor.qty) as qty
        FROM sal_order_row sor 
        JOIN sal_order so ON sor.order_id = so.id 
        WHERE sor.reference IN (%s, %s)
          AND so.date >= '2025-10-01' 
          AND so.state_id NOT IN ('00', '01')
    """, (sku, sku_upper))
    sales = cur.fetchone()['qty']

    # Last IT Price
    cur.execute("""
        SELECT sor.price
        FROM sal_order_row sor
        JOIN sal_order so ON sor.order_id = so.id
        WHERE sor.reference IN (%s, %s)
          AND so.delivery_country_id = 10
          AND so.state_id NOT IN ('00', '01')
          AND sor.price > 0
        ORDER BY so.date DESC, so.time DESC
        LIMIT 1
    """, (sku, sku_upper))
    res = cur.fetchone()
    last_price = res['price'] if res else 0

    # Find the WAC in USD. Let's look for 31.7 in a few tables.
    # Check inv_weighted_average_cost
    cur.execute("""
        SELECT price, currency, wac_eur
        FROM inv_weighted_average_cost w
        JOIN dat_product p ON w.product_id = p.id
        WHERE p.reference IN (%s, %s, 'SA800TEX')
        ORDER BY w.purchase_date DESC LIMIT 1
    """, (sku, sku_upper))
    wac_res1 = cur.fetchone()

    # Check pch_order_row
    cur.execute("""
        SELECT r.price_fob, o.currency_iso_code
        FROM pch_order_row r
        JOIN pch_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        WHERE p.reference IN (%s, %s, 'SA800TEX')
        ORDER BY o.date DESC LIMIT 1
    """, (sku, sku_upper))
    wac_res2 = cur.fetchone()
    
    # Check pch_price_list_detail
    cur.execute("""
        SELECT d.net_price, c.iso_code
        FROM pch_price_list_detail d
        JOIN pch_price_list l ON d.list_id = l.id
        JOIN dat_currency c ON l.currency_id = c.id
        JOIN dat_product p ON d.product_id = p.id
        WHERE p.reference IN (%s, %s, 'SA800TEX')
        ORDER BY d.date DESC LIMIT 1
    """, (sku, sku_upper))
    wac_res3 = cur.fetchone()

print(f"Stock: {stock}")
print(f"Sales: {sales}")
print(f"Price: {last_price}")
print(f"WAC_inv: {wac_res1}")
print(f"WAC_pch_order: {wac_res2}")
print(f"WAC_pch_list: {wac_res3}")

