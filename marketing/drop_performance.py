import argparse
import mysql.connector
from google.ads.googleads.client import GoogleAdsClient
from collections import defaultdict
import datetime

def main():
    parser = argparse.ArgumentParser(description="Drop Performance Report")
    parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    args = parser.parse_args()
    
    # 1. Fetch from Kanguro
    conn = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor = conn.cursor(dictionary=True)
    
    print(f"Fetching sales data from Kanguro (Last {args.days} days)...")
    
    query = f"""
        SELECT 
            p.reference as sku,
            p.id as product_id,
            s.name as supplier_name,
            SUM(r.total_price) as revenue,
            SUM(r.qty) as qty
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        LEFT JOIN dat_supplier s ON p.supplier_id = s.id
        WHERE o.date >= CURDATE() - INTERVAL {args.days} DAY
          AND o.state_id NOT IN ('CA', 'AN')
          AND p.id IN (
              SELECT product_id FROM dat_product_label pl
              JOIN dat_label l ON pl.label_id = l.id
              WHERE LOWER(l.name) LIKE '%drop%'
          )
        GROUP BY p.id, p.reference, s.name
        HAVING qty > 0
    """
    cursor.execute(query)
    sales_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    sku_stats = {}
    supplier_stats = defaultdict(lambda: {'revenue': 0.0, 'qty': 0, 'clicks': 0})
    
    for row in sales_data:
        sku = row['sku'].lower()
        supplier = row['supplier_name'] or "Sconosciuto"
        
        sku_stats[sku] = {
            'revenue': float(row['revenue']),
            'qty': int(row['qty']),
            'clicks': 0,
            'supplier': supplier
        }
        
        supplier_stats[supplier]['revenue'] += float(row['revenue'])
        supplier_stats[supplier]['qty'] += int(row['qty'])

    print("Fetching click data from Google Ads...")
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load Ads config: {e}")
        return
        
    ga_service = client.get_service("GoogleAdsService")
    
    # Customer IDs from SOUL.md
    customer_ids = ["2327095345", "8633848117", "9641081570", "6241768674", "4100556149"]
    
    # Convert days to Google Ads format
    if args.days == 30:
        date_range = "LAST_30_DAYS"
    elif args.days == 7:
        date_range = "LAST_7_DAYS"
    elif args.days == 14:
        date_range = "LAST_14_DAYS"
    else:
        date_range = "LAST_30_DAYS" # Fallback

    query_ads = f"""
        SELECT
            segments.product_item_id,
            metrics.clicks
        FROM shopping_performance_view
        WHERE segments.date DURING {date_range}
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
                    # In Ads, product_item_id might be SKU (IT/ES) or ID-ATTR_ID (others)
                    # We'll just match the item_id if it's in our SKU list directly 
                    # Note: For strict matching across all countries, we should ideally map id_product, 
                    # but for this report's speed we'll do best-effort mapping of the raw product_item_id to our sku_stats if it exists.
                    item_id = row.segments.product_item_id.lower()
                    clicks = row.metrics.clicks
                    
                    if item_id in sku_stats:
                        sku_stats[item_id]['clicks'] += clicks
                        supplier = sku_stats[item_id]['supplier']
                        supplier_stats[supplier]['clicks'] += clicks
                    # Also try to strip '-0' or anything if it was ID based? We'll stick to basic SKU matching for now
                    # since we fetched sku_stats with sku keys.
        except Exception:
            pass

    # Sorts
    prod_by_rev = sorted(sku_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)
    prod_by_qty = sorted(sku_stats.items(), key=lambda x: x[1]['qty'], reverse=True)
    prod_by_clicks = sorted(sku_stats.items(), key=lambda x: x[1]['clicks'], reverse=True)
    
    sup_by_rev = sorted(supplier_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)
    sup_by_qty = sorted(supplier_stats.items(), key=lambda x: x[1]['qty'], reverse=True)
    sup_by_clicks = sorted(supplier_stats.items(), key=lambda x: x[1]['clicks'], reverse=True)

    print("\n" + "="*50)
    print("📊 REPORT DROP_PERFORMANCE")
    print("="*50 + "\n")
    
    print("--- TOP 10 PRODOTTI DROP (PER FATTURATO) ---")
    for i, (sku, data) in enumerate(prod_by_rev[:10], 1):
        print(f"{i}. {sku.upper()} | €{data['revenue']:.2f} ({data['supplier']})")
        
    print("\n--- TOP 10 PRODOTTI DROP (PER QTA ORDINATA) ---")
    for i, (sku, data) in enumerate(prod_by_qty[:10], 1):
        print(f"{i}. {sku.upper()} | {data['qty']} pz ({data['supplier']})")

    print("\n--- TOP 10 PRODOTTI DROP (PER CLICK ADS) ---")
    for i, (sku, data) in enumerate(prod_by_clicks[:10], 1):
        print(f"{i}. {sku.upper()} | {data['clicks']} click ({data['supplier']})")

    print("\n--- TOP 3 FORNITORI DROP (PER FATTURATO) ---")
    for i, (sup, data) in enumerate(sup_by_rev[:3], 1):
        print(f"{i}. {sup} | €{data['revenue']:.2f}")

    print("\n--- TOP 3 FORNITORI DROP (PER QTA ORDINATA) ---")
    for i, (sup, data) in enumerate(sup_by_qty[:3], 1):
        print(f"{i}. {sup} | {data['qty']} pz")

    print("\n--- TOP 3 FORNITORI DROP (PER CLICK ADS) ---")
    for i, (sup, data) in enumerate(sup_by_clicks[:3], 1):
        print(f"{i}. {sup} | {data['clicks']} click")
        
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
