import pandas as pd
import mysql.connector
from google.ads.googleads.client import GoogleAdsClient
from collections import defaultdict

def main():
    print("Connessione al DB Kanguro per estrazione vendite prodotti Drop (Ultimi 30gg)...")
    conn = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor = conn.cursor(dictionary=True)
    
    # Prendi le vendite raggruppate per "parent_reference" per spalmare i costi sulle varianti
    # Usiamo parent_reference per raggruppare i prodotti (es. per calcolare l'incidenza a livello parent)
    query_sales = """
        SELECT 
            COALESCE(p.parent_reference, p.reference) as parent_sku,
            s.name as supplier, 
            SUM(r.total_price) as revenue
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
        GROUP BY parent_sku, s.name
        HAVING revenue > 0
    """
    cursor.execute(query_sales)
    sales_data = cursor.fetchall()
    
    # Prendi l'associazione child -> parent per mappare correttamente i click di Google Ads
    query_mapping = """
        SELECT 
            reference as child_sku, 
            COALESCE(parent_reference, reference) as parent_sku
        FROM dat_product 
        WHERE id IN (
            SELECT pl.product_id FROM dat_product_label pl
            JOIN dat_label l ON pl.label_id = l.id
            WHERE LOWER(l.name) LIKE '%drop%'
        )
    """
    cursor.execute(query_mapping)
    mapping_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Creiamo dizionario di mappatura child -> parent
    child_to_parent = {}
    for row in mapping_data:
        if row['child_sku'] and row['parent_sku']:
            child_to_parent[row['child_sku'].lower()] = row['parent_sku'].lower()
    
    # Inizializziamo le statistiche a livello di PARENT
    stats = {}
    for row in sales_data:
        parent_sku = row['parent_sku'].lower()
        stats[parent_sku] = {
            'Parent SKU': row['parent_sku'].upper(),
            'Fornitore': row['supplier'] or "Sconosciuto",
            'Fatturato Parent (Ultimi 30gg)': float(row['revenue']),
            'Costo Ads Parent (Ultimi 30gg)': 0.0
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
                        cost = row.metrics.cost_micros / 1000000.0
                        
                        # Trova a quale parent appartiene il click (usando la mappa o direttamente l'ID se è già un parent)
                        parent_sku = child_to_parent.get(item_id, item_id)
                        
                        if parent_sku in stats:
                            stats[parent_sku]['Costo Ads Parent (Ultimi 30gg)'] += cost
            except Exception:
                pass
    except Exception as e:
        print(f"Ads Error: {e}")

    top_performers = []
    
    for parent_sku, data in stats.items():
        revenue = data['Fatturato Parent (Ultimi 30gg)']
        cost = data['Costo Ads Parent (Ultimi 30gg)']
        
        if revenue > 0:
            incidenza = (cost / revenue) * 100
            # Vogliamo incidenza <= 10% 
            if incidenza <= 10.0:
                data['Incidenza Marketing % (Halo Effect)'] = round(incidenza, 2)
                top_performers.append(data)
                
    # Ordina per fatturato decrescente
    top_performers = sorted(top_performers, key=lambda x: x['Fatturato Parent (Ultimi 30gg)'], reverse=True)
    
    df = pd.DataFrame(top_performers)
    path = "/root/.openclaw/workspace-marketing/Drop_TopPerformers_LowIncidence_Halo.xlsx"
    df.to_excel(path, index=False)
    
    print(f"File generato con logica HALO EFFECT. {len(top_performers)} parent products trovati.")

if __name__ == "__main__":
    main()
