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
    
    # Prendi tutti i prodotti attivi etichettati drop
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
    
    # Prendi le vendite degli ultimi 30 gg (per avere una media giornaliera robusta)
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
    
    # Costruisci dizionario sku -> dati base
    stats = {}
    for p in drop_products:
        sku = p['sku'].lower()
        stats[sku] = {
            'SKU': p['sku'].upper(),
            'Fornitore': p['supplier'] or "Sconosciuto",
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

    # Logica di divisione
    high_clicks_low_sales = []
    zero_clicks_zero_sales = []
    
    for sku, data in stats.items():
        clicks = data['Click (Ultimi 7gg)']
        avg_sales = data['Vendita Media Giornaliera (30gg)']
        
        # Criterio per File 1: Clicks > 0, vendite nulle o bassissime (< 0.1 al giorno)
        if clicks > 0 and avg_sales < 0.1:
            high_clicks_low_sales.append(data)
            
        # Criterio per File 2: Zero click e Zero vendite
        if clicks == 0 and avg_sales == 0.0:
            zero_clicks_zero_sales.append(data)
            
    # Ordiniamo il primo file per click discendenti
    high_clicks_low_sales = sorted(high_clicks_low_sales, key=lambda x: x['Click (Ultimi 7gg)'], reverse=True)
    
    # Generazione Excel 1
    df1 = pd.DataFrame(high_clicks_low_sales)
    path1 = "/tmp/Drop_HighClicks_LowSales.xlsx"
    df1.to_excel(path1, index=False)
    
    # Generazione Excel 2
    df2 = pd.DataFrame(zero_clicks_zero_sales)
    path2 = "/tmp/Drop_ZeroClicks_ZeroSales.xlsx"
    df2.to_excel(path2, index=False)
    
    print(f"File generati in /tmp. File1: {len(high_clicks_low_sales)} rows, File2: {len(zero_clicks_zero_sales)} rows.")

if __name__ == "__main__":
    main()
