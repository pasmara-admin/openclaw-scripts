import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

accounts = {
    'IT': '2327095345',
    'CH': '4100556149',
    'FR': '8633848117',
    'ES': '6241768674',
    'DE': '9641081570',
    'AT': '4654715733'
}

def main():
    try:
        client = GoogleAdsClient.load_from_storage(path="/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
          campaign.name,
          metrics.impressions
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY metrics.impressions DESC
        LIMIT 1
    """

    for country, customer_id in accounts.items():
        try:
            request = client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query
            response = ga_service.search(request=request)
            
            found = False
            for row in response:
                print(f"{country}: {row.campaign.name} - {row.metrics.impressions} impressions")
                found = True
                break
            if not found:
                print(f"{country}: Nessuna campagna o 0 impression negli ultimi 30 giorni.")
        except GoogleAdsException as ex:
            print(f"{country}: Error API - {ex}")
        except Exception as e:
            print(f"{country}: Error - {e}")

if __name__ == "__main__":
    main()