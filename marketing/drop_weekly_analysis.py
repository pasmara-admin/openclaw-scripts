import pandas as pd
import mysql.connector
from google.ads.googleads.client import GoogleAdsClient

def main():
    print("Connessione al DB Kanguro per estrazione prodotti Drop...")
    conn = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor = conn.cursor(dictionary=True)
    
    # Prendi tutti i prodotti attivi etichettati drop (niente k.ps_qty)
    query_products = """
        SELECT p.id, p.reference as sku, s.name as supplier
        FROM dat_product p
        LEFT JOIN dat_supplier s ON p.supplier_id = s.id
        WHERE p.is_active = 1
          AND p.id IN (
              SELECT pl.product_id FROM dat_product_label pl
              JOIN dat_label l ON pl.label_id = l.id
              WHERE LOWER(l.name) LIKE '%drop%'
          )
    """
    cursor.execute(query_products)
    drop_products = cursor.fetchall()
    
    # Prendi le vendite degli ultimi 30 gg
    query_sales = """
        SELECT p.reference as sku, SUM(r.qty) as total_qty_30d
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        WHERE o.date >= CURDATE() - INTERVAL 30 DAY
          AND o.state_id NOT IN ('CA', 'AN')
        GROUP BY p.reference
    """
    cursor.execute(query_sales)
    sales_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print("Connessione a PrestaShop per controllo stock...")
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
    
    ps_stock = {}
    for row in stock_main:
        if row['reference']: ps_stock[row['reference'].upper()] = int(row['quantity'])
    for row in stock_attr:
        if row['reference']: ps_stock[row['reference'].upper()] = int(row['quantity'])
        
    cursor_p.close()
    conn_p.close()
    
    stats = {}
    for p in drop_products:
        sku = p['sku'].lower()
        sku_upper = p['sku'].upper()
        
        # Filtro: Disponibili (Stock >= 1 su PrestaShop)
        stock_val = ps_stock.get(sku_upper, 0)
        
        if stock_val >= 1:
            stats[sku] = {
                'SKU': sku_upper,
                'Fornitore': p['supplier'] or "Sconosciuto",
                'Stock Attuale': stock_val,
                'Vendita Media Giornaliera (30gg)': 0.0,
                'Click (Ultimi 7gg)': 0
            }
        
    for s in sales_data:
        sku = s['sku'].lower()
        if sku in stats:
            stats[sku]['Vendita Media Giornaliera (30gg)'] = round(float(s['total_qty_30d']) / 30.0, 2)
            
    print("Estrazione Click da Google Ads (Ultimi 7gg)...")
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
        ga_service = client.get_service("GoogleAdsService")
        customer_ids = ["2327095345", "8633848117", "9641081570", "6241768674", "4100556149"]
        
        query_ads = """
            SELECT
                segments.product_item_id,
                metrics.clicks
            FROM shopping_performance_view
            WHERE segments.date DURING LAST_7_DAYS
              AND metrics.clicks > 0
        """
        for cid in customer_ids:
            try:
                request = client.get_type("SearchGoogleAdsStreamRequest")
                request.customer_id = cid
                request.query = query_ads
                stream = ga_service.search_stream(request)
                for batch in stream:
                    for row in batch.results:
                        item_id = row.segments.product_item_id.lower()
                        if item_id in stats:
                            stats[item_id]['Click (Ultimi 7gg)'] += row.metrics.clicks
            except Exception:
                pass
    except Exception as e:
        print(f"Ads Error: {e}")

    high_clicks_low_sales = []
    zero_clicks_zero_sales = []
    
    for sku, data in stats.items():
        clicks = data['Click (Ultimi 7gg)']
        avg_sales = data['Vendita Media Giornaliera (30gg)']
        
        if clicks > 0 and avg_sales < 0.1:
            high_clicks_low_sales.append(data)
            
        if clicks == 0 and avg_sales == 0.0:
            zero_clicks_zero_sales.append(data)
            
    high_clicks_low_sales = sorted(high_clicks_low_sales, key=lambda x: x['Click (Ultimi 7gg)'], reverse=True)
    
    df1 = pd.DataFrame(high_clicks_low_sales)
    path1 = "/root/.openclaw/workspace-marketing/Drop_HighClicks_LowSales_InStock.xlsx"
    df1.to_excel(path1, index=False)
    
    df2 = pd.DataFrame(zero_clicks_zero_sales)
    path2 = "/root/.openclaw/workspace-marketing/Drop_ZeroClicks_ZeroSales_InStock.xlsx"
    df2.to_excel(path2, index=False)
    
    print(f"File generati. File1: {len(high_clicks_low_sales)} rows, File2: {len(zero_clicks_zero_sales)} rows.")

if __name__ == "__main__":
    main()
