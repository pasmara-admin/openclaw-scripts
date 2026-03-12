import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

accounts = {
    'IT': '2327095345',
    'CH': '4100556149',
    'FR': '8633848117',
    'ES': '6241768674',
    'DE': '9641081570'
    # 'AT': '4654715733' # Commentato perché sappiamo che l'account non è attivo al momento
}

def main():
    try:
        client = GoogleAdsClient.load_from_storage(path="/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    ga_service = client.get_service("GoogleAdsService")

    sku = 'S6316R'
    query = f"""
        SELECT
          segments.product_item_id,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM shopping_performance_view
        WHERE segments.date DURING LAST_30_DAYS
          AND segments.product_item_id = '{sku}'
    """

    for country, customer_id in accounts.items():
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
                print(f"{country} - SKU: {sku} | Impression: {total_impressions} | Clic: {total_clicks} | Costo: €{cost:.2f} | Conv: {total_conversions:.2f} | Valore Conv: €{total_conversions_value:.2f}")
            else:
                print(f"{country} - SKU: {sku} | Nessun dato rilevato negli ultimi 30 giorni.")

        except GoogleAdsException as ex:
            print(f"{country}: Error API - {ex}")
        except Exception as e:
            print(f"{country}: Error - {e}")

if __name__ == "__main__":
    main()