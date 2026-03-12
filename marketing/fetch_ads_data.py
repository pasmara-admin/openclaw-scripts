import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main(client, customer_ids, skus):
    query = f"""
        SELECT
            segments.product_item_id,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions
        FROM shopping_performance_view
        WHERE segments.product_item_id IN ({", ".join([f"'{sku}'" for sku in skus])})
          AND segments.date DURING LAST_30_DAYS
    """
    
    results = {}
    for sku in skus:
        results[sku] = {'impressions': 0, 'clicks': 0, 'conversions': 0.0}

    for customer_id in customer_ids:
        ga_service = client.get_service("GoogleAdsService")
        try:
            search_request = client.get_type("SearchGoogleAdsStreamRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            stream = ga_service.search_stream(search_request)
            for batch in stream:
                for row in batch.results:
                    item_id = row.segments.product_item_id
                    results[item_id]['impressions'] += row.metrics.impressions
                    results[item_id]['clicks'] += row.metrics.clicks
                    results[item_id]['conversions'] += row.metrics.conversions
        except GoogleAdsException as ex:
            print(f"Error for account {customer_id}: {ex}")
        except Exception as ex:
             print(f"Other Error for account {customer_id}: {ex}")

    print("SKU\tImpressions\tClicks\tConversions")
    for sku in skus:
        print(f"{sku.upper()}\t{results[sku]['impressions']}\t{results[sku]['clicks']}\t{results[sku]['conversions']:.2f}")

if __name__ == "__main__":
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load google-ads.yaml: {e}")
        sys.exit(1)
        
    customer_ids = ["2327095345", "4100556149", "8633848117", "6241768674", "9641081570", "4654715733"]
    skus = ["di1706mig", "di1706mic", "di1706min", "di1706mir", "di1706mibl", "di1706mim", "di1706mi"]
    main(client, customer_ids, skus)
