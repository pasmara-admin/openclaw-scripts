import sys
from google.ads.googleads.client import GoogleAdsClient

def main():
    try:
        client = GoogleAdsClient.load_from_storage(path="/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    ga_service = client.get_service("GoogleAdsService")

    customer_id = '2327095345' # IT
    
    query = """
        SELECT
          segments.product_item_id,
          metrics.impressions
        FROM shopping_performance_view
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY metrics.impressions DESC
        LIMIT 5
    """

    try:
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query
        response = ga_service.search(request=request)
        
        print("Top 5 SKUs per formato in IT:")
        for row in response:
            print(f"ID: {row.segments.product_item_id} | Imp: {row.metrics.impressions}")

    except Exception as e:
        print(f"Error - {e}")

if __name__ == "__main__":
    main()