import pymysql
from collections import defaultdict
from google.ads.googleads.client import GoogleAdsClient
import sys

def get_kanguro_data():
    conn = pymysql.connect(
        host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41',
        database='kanguro', cursorclass=pymysql.cursors.DictCursor
    )
    
    # 1. Get Revenue grouped by Parent Product (external_reference = Prestashop id_product)
    # Using last 30 days.
    query_rev = """
        SELECT 
            p.external_reference as id_product,
            MAX(p.parent_reference) as parent_sku,
            SUM(r.total_price) as revenue
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.reference = p.reference
        WHERE o.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
          AND o.state_id NOT IN ('00', '01')
          AND o.is_deleted = 0 AND r.is_deleted = 0
          AND p.external_reference IS NOT NULL AND p.external_reference != ''
        GROUP BY p.external_reference
        HAVING revenue > 200  # Filter out very low revenue to avoid noise
    """
    
    parents = {}
    with conn.cursor() as cursor:
        cursor.execute(query_rev)
        for row in cursor.fetchall():
            id_prod = str(row['id_product'])
            parents[id_prod] = {
                'id_product': id_prod,
                'parent_sku': row['parent_sku'] or f"ID-{id_prod}",
                'revenue': float(row['revenue']),
                'spend': 0.0,
                'variants': []
            }
            
    if not parents:
        conn.close()
        return parents

    # 2. Get all child variants for these parent products to map Ads IDs
    id_prod_list = "', '".join(parents.keys())
    query_vars = f"""
        SELECT external_reference as id_product, reference as sku, external_attribute_reference as id_attr
        FROM dat_product
        WHERE external_reference IN ('{id_prod_list}')
    """
    with conn.cursor() as cursor:
        cursor.execute(query_vars)
        for row in cursor.fetchall():
            id_prod = str(row['id_product'])
            if id_prod in parents:
                sku = row['sku']
                id_attr = row['id_attr']
                parents[id_prod]['variants'].append({
                    'sku': sku,
                    'id_attr': id_attr
                })
                
    conn.close()
    return parents

def get_ads_spend(client, parents):
    ga_service = client.get_service("GoogleAdsService")
    
    accounts = {
        "IT": "2327095345", "ES": "6241768674",
        "FR": "8633848117", "DE": "9641081570",
        "AT": "4654715733", "CH": "4100556149"
    }
    
    # Build reverse mappings to quickly add spend to the right parent
    # Map product_item_id -> id_product (parent)
    pid_to_parent_it_es = {}
    pid_to_parent_other = {}
    
    for id_prod, data in parents.items():
        for var in data['variants']:
            sku = var['sku']
            id_attr = var['id_attr']
            
            # IT/ES uses SKU lowercase
            if sku:
                pid_to_parent_it_es[sku.lower()] = id_prod
                
            # Other uses id_product-id_attr or id_product
            if id_prod:
                pid_other = f"{id_prod}-{id_attr}" if id_attr else f"{id_prod}"
                pid_to_parent_other[pid_other] = id_prod

    def fetch_for_mapping(acc_id, mapping):
        pids = list(mapping.keys())
        if not pids: return
        
        batch_size = 800
        for i in range(0, len(pids), batch_size):
            batch = pids[i:i+batch_size]
            pid_str = ", ".join([f"'{pid}'" for pid in batch])
            query = f"""
                SELECT segments.product_item_id, metrics.cost_micros
                FROM shopping_performance_view
                WHERE segments.product_item_id IN ({pid_str})
                  AND segments.date DURING LAST_30_DAYS
            """
            try:
                search_request = client.get_type("SearchGoogleAdsStreamRequest")
                search_request.customer_id = acc_id
                search_request.query = query
                stream = ga_service.search_stream(search_request)
                for response_batch in stream:
                    for ga_row in response_batch.results:
                        pid = ga_row.segments.product_item_id
                        cost = ga_row.metrics.cost_micros / 1000000.0
                        
                        parent_id = mapping.get(pid)
                        if parent_id:
                            parents[parent_id]['spend'] += cost
            except Exception as e:
                pass # skip inactive accounts or errors

    for country, acc_id in accounts.items():
        if country in ["IT", "ES"]:
            fetch_for_mapping(acc_id, pid_to_parent_it_es)
        else:
            fetch_for_mapping(acc_id, pid_to_parent_other)

def main():
    parents = get_kanguro_data()
    
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load google-ads.yaml: {e}")
        return
        
    get_ads_spend(client, parents)
    
    results = []
    for id_prod, data in parents.items():
        rev = data['revenue']
        spend = data['spend']
        if spend > 0 and rev > 0: # Only consider products with actual marketing spend
            incidenza = spend / rev
            results.append({
                'id_product': id_prod,
                'parent_sku': data['parent_sku'],
                'revenue': rev,
                'spend': spend,
                'incidenza': incidenza
            })
            
    # Sort by Incidenza Ascending (Lower is better)
    results.sort(key=lambda x: x['incidenza'])
    
    print("TOP 20 PRODOTTI (PARENT LEVEL) PER INCIDENZA MARKETING:")
    for i, r in enumerate(results[:20]):
        print(f"{i+1}. **{r['parent_sku']}** (ID: {r['id_product']}) | Fatturato: €{r['revenue']:.2f} | Spesa Totale: €{r['spend']:.2f} | Incidenza: {r['incidenza']*100:.2f}%")

if __name__ == "__main__":
    main()
