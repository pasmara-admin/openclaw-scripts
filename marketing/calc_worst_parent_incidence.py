import pymysql
from collections import defaultdict
from google.ads.googleads.client import GoogleAdsClient
import sys

def get_ads_spend(client):
    ga_service = client.get_service("GoogleAdsService")
    accounts = {
        "IT": "2327095345", "ES": "6241768674",
        "FR": "8633848117", "DE": "9641081570",
        "AT": "4654715733", "CH": "4100556149"
    }
    
    spend_it_es = defaultdict(float)
    spend_other = defaultdict(float)
    
    query = """
        SELECT segments.product_item_id, metrics.cost_micros
        FROM shopping_performance_view
        WHERE segments.date DURING LAST_30_DAYS
    """
    for country, acc_id in accounts.items():
        try:
            search_request = client.get_type("SearchGoogleAdsStreamRequest")
            search_request.customer_id = acc_id
            search_request.query = query
            stream = ga_service.search_stream(search_request)
            for batch in stream:
                for row in batch.results:
                    cost = row.metrics.cost_micros / 1000000.0
                    if cost > 0:
                        pid = row.segments.product_item_id
                        if country in ["IT", "ES"]:
                            spend_it_es[pid.lower()] += cost
                        else:
                            spend_other[pid] += cost
        except Exception as e:
            pass
    return spend_it_es, spend_other

def get_kanguro_map_and_revenue(spend_it_es, spend_other):
    conn = pymysql.connect(
        host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
        database='kanguro', cursorclass=pymysql.cursors.DictCursor
    )
    
    sku_to_parent = {}
    pid_to_parent = {}
    
    query_map = "SELECT reference, external_reference, external_attribute_reference, parent_reference FROM dat_product WHERE is_deleted = 0 AND reference != ''"
    with conn.cursor() as cursor:
        cursor.execute(query_map)
        for row in cursor.fetchall():
            parent = row['parent_reference'] or f"ID-{row['external_reference']}"
            sku = row['reference'].lower()
            sku_to_parent[sku] = parent
            
            id_prod = row['external_reference']
            id_attr = row['external_attribute_reference']
            if id_prod:
                pid = f"{id_prod}-{id_attr}" if id_attr else f"{id_prod}"
                pid_to_parent[pid] = parent

    parent_spend = defaultdict(float)
    for pid, cost in spend_it_es.items():
        parent = sku_to_parent.get(pid, f"UNKNOWN-{pid}")
        parent_spend[parent] += cost
        
    for pid, cost in spend_other.items():
        parent = pid_to_parent.get(pid, f"UNKNOWN-{pid}")
        parent_spend[parent] += cost

    query_rev = """
        SELECT p.parent_reference, p.external_reference, SUM(r.total_price) as revenue
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.reference = p.reference
        WHERE o.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
          AND o.state_id NOT IN ('00', '01')
          AND o.is_deleted = 0 AND r.is_deleted = 0
        GROUP BY p.parent_reference, p.external_reference
    """
    parent_rev = defaultdict(float)
    with conn.cursor() as cursor:
        cursor.execute(query_rev)
        for row in cursor.fetchall():
            parent = row['parent_reference'] or f"ID-{row['external_reference']}"
            parent_rev[parent] += float(row['revenue'])
            
    conn.close()
    return parent_spend, parent_rev

def main():
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load google-ads.yaml: {e}")
        return
        
    spend_it_es, spend_other = get_ads_spend(client)
    parent_spend, parent_rev = get_kanguro_map_and_revenue(spend_it_es, spend_other)
    
    results = []
    for parent, spend in parent_spend.items():
        if spend < 15.0:  # Filter out trivial spend to highlight real bleeders
            continue
        if parent.startswith("UNKNOWN"):
            continue
        
        rev = parent_rev.get(parent, 0.0)
        incidenza = (spend / rev) if rev > 0 else float('inf')
            
        results.append({
            'parent': parent,
            'spend': spend,
            'revenue': rev,
            'incidenza': incidenza
        })
        
    # Sort by Incidenza DESC (worst), then spend DESC
    results.sort(key=lambda x: (x['incidenza'], x['spend']), reverse=True)
    
    print("I 20 PRODOTTI (PARENT) CON L'INCIDENZA PEGGIORE (Spesa > 15€ negli ultimi 30gg):")
    for i, r in enumerate(results[:20]):
        inc_str = "∞ (0 Vendite)" if r['incidenza'] == float('inf') else f"{r['incidenza']*100:.2f}%"
        print(f"{i+1}. **{r['parent']}** | Spesa Totale: €{r['spend']:.2f} | Fatturato: €{r['revenue']:.2f} | Incidenza: {inc_str}")

if __name__ == "__main__":
    main()
