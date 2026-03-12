import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main(client, customer_id, skus):
    query = f"""
        SELECT
            campaign.name,
            segments.product_item_id,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions
        FROM shopping_performance_view
        WHERE segments.product_item_id IN ({", ".join([f"'{sku}'" for sku in skus])})
          AND segments.date DURING LAST_30_DAYS
    """
    
    ga_service = client.get_service("GoogleAdsService")
    try:
        search_request = client.get_type("SearchGoogleAdsStreamRequest")
        search_request.customer_id = customer_id
        search_request.query = query
        
        stream = ga_service.search_stream(search_request)
        print("Campaign Name | SKU | Impressions | Clicks")
        found = False
        for batch in stream:
            for row in batch.results:
                found = True
                print(f"{row.campaign.name} | {row.segments.product_item_id.upper()} | {row.metrics.impressions} | {row.metrics.clicks}")
        if not found:
            print("No active campaigns found generating traffic for these SKUs in the last 30 days.")
    except GoogleAdsException as ex:
        print(f"Error for account {customer_id}: {ex}")
    except Exception as ex:
         print(f"Other Error for account {customer_id}: {ex}")

if __name__ == "__main__":
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load google-ads.yaml: {e}")
        sys.exit(1)
        
    # ProduceShop IT
    customer_id = "2327095345"
    skus = ["di1706mig", "di1706mic", "di1706min", "di1706mir", "di1706mibl", "di1706mim", "di1706mi"]
    main(client, customer_id, skus)
