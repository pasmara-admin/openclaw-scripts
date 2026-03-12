import pandas as pd
import mysql.connector
from google.ads.googleads.client import GoogleAdsClient

def main():
    print("Connessione al DB Kanguro per estrazione vendite prodotti Drop (Ultimi 30gg)...")
    conn = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor = conn.cursor(dictionary=True)
    
    query_sales = """
        SELECT p.id, p.reference as sku, s.name as supplier, SUM(r.total_price) as revenue
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        LEFT JOIN dat_supplier s ON p.supplier_id = s.id
        WHERE o.date >= CURDATE() - INTERVAL 30 DAY
          AND o.state_id NOT IN ('CA', 'AN')
          AND p.id IN (
              SELECT pl.product_id FROM dat_product_label pl
              JOIN dat_label l ON pl.label_id = l.id
              WHERE LOWER(l.name) LIKE '%drop%'
          )
        GROUP BY p.id, p.reference, s.name
        HAVING revenue > 0
    """
    cursor.execute(query_sales)
    sales_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    stats = {}
    for row in sales_data:
        sku = row['sku'].lower()
        stats[sku] = {
            'SKU': row['sku'].upper(),
            'Fornitore': row['supplier'] or "Sconosciuto",
            'Fatturato (Ultimi 30gg)': float(row['revenue']),
            'Costo Ads (Ultimi 30gg)': 0.0
        }
            
    print("Estrazione Spesa da Google Ads (Ultimi 30gg)...")
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
        ga_service = client.get_service("GoogleAdsService")
        customer_ids = ["2327095345", "8633848117", "9641081570", "6241768674", "4100556149"]
        
        query_ads = """
            SELECT
                segments.product_item_id,
                metrics.cost_micros
            FROM shopping_performance_view
            WHERE segments.date DURING LAST_30_DAYS
              AND metrics.cost_micros > 0
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
                            stats[item_id]['Costo Ads (Ultimi 30gg)'] += (row.metrics.cost_micros / 1000000.0)
            except Exception:
                pass
    except Exception as e:
        print(f"Ads Error: {e}")

    top_performers = []
    
    for sku, data in stats.items():
        revenue = data['Fatturato (Ultimi 30gg)']
        cost = data['Costo Ads (Ultimi 30gg)']
        
        if revenue > 0:
            incidenza = (cost / revenue) * 100
            # Vogliamo incidenza <= 10% (ma anche i prodotti con 0 spesa e >0 vendite che avranno incidenza 0%)
            if incidenza <= 10.0:
                data['Incidenza %'] = round(incidenza, 2)
                top_performers.append(data)
                
    # Ordina per fatturato decrescente
    top_performers = sorted(top_performers, key=lambda x: x['Fatturato (Ultimi 30gg)'], reverse=True)
    
    df = pd.DataFrame(top_performers)
    path = "/root/.openclaw/workspace-marketing/Drop_TopPerformers_LowIncidence.xlsx"
    df.to_excel(path, index=False)
    
    print(f"File generato. {len(top_performers)} prodotti trovati.")

if __name__ == "__main__":
    main()
