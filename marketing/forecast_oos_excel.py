import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("Gathering sales data from Kanguro (last 30 days, Site + Marketplaces)...")
    conn_k = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor_k = conn_k.cursor(dictionary=True)
    
    # Get sales for active products (all source_srv since we want Site + Marketplaces)
    query_sales = """
        SELECT 
            p.reference as sku,
            SUM(r.qty) / 30.0 as avg_daily_sales
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        WHERE o.date >= CURDATE() - INTERVAL 30 DAY
          AND o.state_id NOT IN ('CA', 'AN')
          AND p.is_active = 1
        GROUP BY p.reference
        HAVING avg_daily_sales > 0
    """
    cursor_k.execute(query_sales)
    sales_data = cursor_k.fetchall()
    
    sku_sales = {}
    for row in sales_data:
        sku = row['sku'].upper()
        sku_sales[sku] = float(row['avg_daily_sales'])
        
    cursor_k.close()
    conn_k.close()
    
    print("Gathering stock data from PrestaShop...")
    conn_p = mysql.connector.connect(
        host="62.84.190.199",
        user="john",
        password="qARa6aRozi6I",
        database="produceshop",
        ssl_disabled=True
    )
    cursor_p = conn_p.cursor(dictionary=True)
    
    query_stock_main = """
        SELECT p.reference, s.quantity
        FROM ps_product p
        JOIN ps_stock_available s ON p.id_product = s.id_product AND s.id_product_attribute = 0
        WHERE s.id_shop = 1
    """
    cursor_p.execute(query_stock_main)
    stock_main = cursor_p.fetchall()
    
    query_stock_attr = """
        SELECT pa.reference, s.quantity
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
    today = datetime.now()
    
    for sku, avg_daily_sales in sku_sales.items():
        stock = sku_stock.get(sku, 0)
        if stock > 0:
            days_to_oos = stock / avg_daily_sales
            if days_to_oos <= 14:
                oos_date = today + timedelta(days=days_to_oos)
                results.append({
                    'SKU': sku,
                    'Stock Attuale (PrestaShop)': int(stock),
                    'Vendita Media Giornaliera (Sito+MK)': round(avg_daily_sales, 2),
                    'Data stimata OOS': oos_date.strftime('%Y-%m-%d')
                })
                
    # Sort by date ASC
    results = sorted(results, key=lambda x: x['Data stimata OOS'])
    
    df = pd.DataFrame(results)
    excel_path = "/root/.openclaw/workspace-marketing/forecast_oos.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Excel generated at {excel_path} with {len(results)} products.")

if __name__ == "__main__":
    main()
