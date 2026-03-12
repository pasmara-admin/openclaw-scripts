import sys
import pymysql
import csv
from collections import defaultdict
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_top_revenue_skus(limit=100):
    conn = pymysql.connect(
        host='34.38.166.212',
        user='john',
        password='3rmiCyf6d~MZDO41',
        database='kanguro',
        cursorclass=pymysql.cursors.DictCursor
    )
    query = """
    SELECT
      r.reference as sku,
      SUM(r.total_price) as revenue,
      p.external_reference as id_product,
      p.external_attribute_reference as id_product_attribute
    FROM sal_order_row r
    JOIN sal_order o ON r.order_id = o.id
    LEFT JOIN dat_product p ON r.reference = p.reference
    WHERE o.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
      AND o.state_id NOT IN ('00', '01')
      AND o.is_deleted = 0
      AND r.is_deleted = 0
      AND r.reference IS NOT NULL AND r.reference != ''
    GROUP BY r.reference, p.external_reference, p.external_attribute_reference
    ORDER BY revenue DESC
    LIMIT %s
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
    conn.close()
    return results

def get_ads_spend(client, sku_mapping):
    ga_service = client.get_service("GoogleAdsService")
    
    # IT, ES -> sku lower
    # FR, DE, AT, CH -> id_product-id_attr
    accounts = {
        "IT": "2327095345",
        "ES": "6241768674",
        "FR": "8633848117",
        "DE": "9641081570",
        "AT": "4654715733",
        "CH": "4100556149"
    }
    
    # Map product_item_id -> SKU
    pid_to_sku_it_es = {}
    pid_to_sku_other = {}
    
    for row in sku_mapping:
        sku = row['sku']
        pid_to_sku_it_es[sku.lower()] = sku
        
        id_prod = row['id_product']
        id_attr = row['id_product_attribute']
        if id_prod:
            if id_attr:
                pid_other = f"{id_prod}-{id_attr}"
            else:
                pid_other = f"{id_prod}"
            pid_to_sku_other[pid_other] = sku
            
    # Fetch spend
    sku_spend = defaultdict(float)
    
    for country, acc_id in accounts.items():
        if country in ["IT", "ES"]:
            target_mapping = pid_to_sku_it_es
        else:
            target_mapping = pid_to_sku_other
            
        if not target_mapping:
            continue
            
        pids = list(target_mapping.keys())
        # Batching pids just in case there are too many for one query
        batch_size = 500
        for i in range(0, len(pids), batch_size):
            batch = pids[i:i+batch_size]
            pid_str = ", ".join([f"'{pid}'" for pid in batch])
            
            query = f"""
                SELECT
                    segments.product_item_id,
                    metrics.cost_micros
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
                        
                        original_sku = target_mapping.get(pid)
                        if original_sku:
                            sku_spend[original_sku] += cost
            except Exception as e:
                print(f"Skipping/Error on {country} ({acc_id}): {e}")
                
    return sku_spend

def main():
    print("Fetching top 100 revenue SKUs from Kanguro...")
    try:
        top_skus = get_top_revenue_skus(100)
    except Exception as e:
        print(f"Error connecting to Kanguro: {e}")
        return

    print("Loading Google Ads client...")
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load google-ads.yaml: {e}")
        return

    print("Fetching Google Ads spend...")
    sku_spend = get_ads_spend(client, top_skus)
    
    # Calculate ROAS
    final_data = []
    for row in top_skus:
        sku = row['sku']
        rev = float(row['revenue'] or 0)
        spend = sku_spend.get(sku, 0.0)
        roas = (rev / spend) if spend > 0 else float('inf')
        
        final_data.append({
            'SKU': sku,
            'Revenue': rev,
            'Spend': spend,
            'ROAS': roas
        })
        
    # Sort by ROAS descending (filter out 0 spend or sort them last/first depending on needs)
    # We want best ROI, so high ROAS. If spend is 0, ROI is infinite.
    # Let's sort by ROAS desc, but maybe put inf at the top? Yes.
    final_data.sort(key=lambda x: x['ROAS'], reverse=True)
    
    # Write to CSV
    csv_file = "/root/.openclaw/workspace-marketing/top_100_roas_analysis.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['SKU', 'Revenue', 'Spend', 'ROAS'])
        writer.writeheader()
        for r in final_data:
            writer.writerow(r)
            
    print(f"Analysis complete. CSV saved to {csv_file}")
    print("Top 10 SKUs by ROAS (with spend > 0):")
    
    # Print top 10 with actual spend for the chat context
    valid_roas = [r for r in final_data if r['Spend'] > 0]
    for i, r in enumerate(valid_roas[:10]):
        print(f"{i+1}. {r['SKU']} - Rev: €{r['Revenue']:.2f} | Spend: €{r['Spend']:.2f} | ROAS: {r['ROAS']:.2f}")

if __name__ == "__main__":
    main()
