import mysql.connector

def main():
    print("Gathering sales data from Kanguro (last 30 days)...")
    # Connect to Kanguro
    conn_k = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor_k = conn_k.cursor(dictionary=True)
    
    # Get sales and current price for active products
    query_sales = """
        SELECT 
            p.reference as sku,
            COALESCE(k.sale_price, 0) as current_price,
            SUM(r.qty) / 30.0 as avg_daily_sales
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        LEFT JOIN dat_product_kpi k ON p.id = k.product_id
        WHERE o.date >= CURDATE() - INTERVAL 30 DAY
          AND o.state_id NOT IN ('CA', 'AN')
          AND p.is_active = 1
        GROUP BY p.reference, k.sale_price
        HAVING avg_daily_sales > 0
    """
    cursor_k.execute(query_sales)
    sales_data = cursor_k.fetchall()
    
    sku_sales = {}
    for row in sales_data:
        sku = row['sku'].upper()
        sku_sales[sku] = {
            'avg_daily_sales': float(row['avg_daily_sales']),
            'current_price': float(row['current_price'])
        }
        
    cursor_k.close()
    conn_k.close()
    
    print(f"Found {len(sku_sales)} products with >0 sales in the last 30 days.")
    print("Gathering stock data from PrestaShop...")

    # Connect to PrestaShop
    conn_p = mysql.connector.connect(
        host="62.84.190.199",
        user="john",
        password="qARa6aRozi6I",
        database="produceshop",
        ssl_disabled=True # Bypass TLS error
    )
    cursor_p = conn_p.cursor(dictionary=True)
    
    # We need to get reference and stock
    # For main products:
    query_stock_main = """
        SELECT 
            p.reference, 
            s.quantity
        FROM ps_product p
        JOIN ps_stock_available s ON p.id_product = s.id_product AND s.id_product_attribute = 0
        WHERE s.id_shop = 1
    """
    cursor_p.execute(query_stock_main)
    stock_main = cursor_p.fetchall()
    
    # For attributes/variants
    query_stock_attr = """
        SELECT 
            pa.reference, 
            s.quantity
        FROM ps_product_attribute pa
        JOIN ps_stock_available s ON pa.id_product = s.id_product AND pa.id_product_attribute = s.id_product_attribute
        WHERE s.id_shop = 1
    """
    cursor_p.execute(query_stock_attr)
    stock_attr = cursor_p.fetchall()
    
    sku_stock = {}
    for row in stock_main:
        if row['reference']:
            sku = row['reference'].upper()
            sku_stock[sku] = sku_stock.get(sku, 0) + int(row['quantity'])
            
    for row in stock_attr:
        if row['reference']:
            sku = row['reference'].upper()
            sku_stock[sku] = sku_stock.get(sku, 0) + int(row['quantity'])
            
    cursor_p.close()
    conn_p.close()
    
    print("Calculating Out Of Stock forecast...")
    
    results = []
    for sku, data in sku_sales.items():
        stock = sku_stock.get(sku, 0)
        
        # If stock is positive and we have sales
        if stock > 0:
            days_to_oos = stock / data['avg_daily_sales']
            if days_to_oos <= 14:
                results.append({
                    'sku': sku,
                    'stock': stock,
                    'avg_daily_sales': data['avg_daily_sales'],
                    'current_price': data['current_price'],
                    'days_to_oos': days_to_oos
                })
        elif stock == 0:
            # Already out of stock or negative stock, skip or include as 0 days
            pass
            
    # Sort by days to oos ASC
    results = sorted(results, key=lambda x: x['days_to_oos'])
    
    print(f"\n✅ REVISIONE PREZZI: PRODOTTI IN ESAURIMENTO (< 14 GG)")
    print(f"{'-'*80}")
    print(f"{'SKU':<15} | {'STOCK':<8} | {'VENDITA MEDIA/GG':<18} | {'PREZZO ATTUALE':<15} | {'OOS STIMATO':<15}")
    print(f"{'-'*80}")
    
    for r in results:
        print(f"{r['sku']:<15} | {r['stock']:<8} | {r['avg_daily_sales']:<18.2f} | €{r['current_price']:<14.2f} | {r['days_to_oos']:.1f} giorni")

    print(f"{'-'*80}")
    print(f"Totale prodotti che richiedono revisione prezzo: {len(results)}")

if __name__ == "__main__":
    main()
