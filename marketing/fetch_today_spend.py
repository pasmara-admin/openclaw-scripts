import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main(client, customer_ids):
    query = """
        SELECT
            customer.descriptive_name,
            customer.currency_code,
            metrics.cost_micros
        FROM customer
        WHERE segments.date DURING TODAY
    """
    
    ga_service = client.get_service("GoogleAdsService")
    
    total_eur = 0.0
    total_chf = 0.0

    print("--- SPESA OGGI ---")
    for customer_id in customer_ids:
        try:
            search_request = client.get_type("SearchGoogleAdsStreamRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            stream = ga_service.search_stream(search_request)
            for batch in stream:
                for row in batch.results:
                    cost = row.metrics.cost_micros / 1000000.0
                    currency = row.customer.currency_code
                    name = row.customer.descriptive_name or customer_id
                    print(f"{name} ({customer_id}): {cost:.2f} {currency}")
                    if currency == 'EUR':
                        total_eur += cost
                    elif currency == 'CHF':
                        total_chf += cost
        except GoogleAdsException as ex:
            # print(f"Error for account {customer_id}: {ex}")
            pass
        except Exception as ex:
            pass

    print("------------------")
    print(f"TOTALE EUR: {total_eur:.2f}")
    print(f"TOTALE CHF: {total_chf:.2f}")

if __name__ == "__main__":
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Failed to load: {e}")
        sys.exit(1)
        
    customer_ids = ["2327095345", "4100556149", "8633848117", "6241768674", "9641081570"]
    main(client, customer_ids)