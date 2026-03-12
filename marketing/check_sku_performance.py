import sys
import argparse
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main():
    parser = argparse.ArgumentParser(description="Get performance metrics for a specific SKU from Google Ads.")
    parser.add_argument("sku", help="The SKU to search for (e.g., s6316r). Will be converted to lowercase as per protocol.")
    parser.add_argument("--customer-id", default="2327095345", help="Google Ads Customer ID (default is IT: 2327095345).")
    parser.add_argument("--days", default="LAST_30_DAYS", help="Timeframe for the query (default: LAST_30_DAYS).")
    args = parser.parse_args()

    sku = args.sku.lower()
    customer_id = args.customer_id.replace('-', '')

    try:
        client = GoogleAdsClient.load_from_storage(path="/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
          segments.product_item_id,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM shopping_performance_view
        WHERE segments.date DURING {args.days}
          AND segments.product_item_id = '{sku}'
    """

    try:
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query
        response = ga_service.search(request=request)
        
        found = False
        total_impressions = 0
        total_clicks = 0
        total_cost_micros = 0
        total_conversions = 0.0
        total_conversions_value = 0.0

        for row in response:
            total_impressions += row.metrics.impressions
            total_clicks += row.metrics.clicks
            total_cost_micros += row.metrics.cost_micros
            total_conversions += row.metrics.conversions
            total_conversions_value += row.metrics.conversions_value
            found = True
        
        if found:
            cost = total_cost_micros / 1000000
            print(f"[{customer_id}] SKU: {sku} ({args.days}) | Impression: {total_impressions} | Clic: {total_clicks} | Costo: €{cost:.2f} | Conv: {total_conversions:.2f} | Valore Conv: €{total_conversions_value:.2f}")
        else:
            print(f"[{customer_id}] SKU: {sku} ({args.days}) | Nessun dato rilevato.")

    except GoogleAdsException as ex:
        print(f"Error API - {ex}")
    except Exception as e:
        print(f"Error - {e}")

if __name__ == "__main__":
    main()
