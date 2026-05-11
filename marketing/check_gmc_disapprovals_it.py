import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# ID Account Italia per GMC / Ads
# In base allo script get_top_campaigns.py e temp_compare_saturdays.py, usiamo:
IT_ACCOUNT_ID = '2327095345'

def main():
    try:
        client = GoogleAdsClient.load_from_storage(path="/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Error loading Ads config: {e}")
        return

    ga_service = client.get_service("GoogleAdsService")

    # Interrogazione shopping_product per trovare i prodotti disapprovati (non approvati per la pubblicazione)
    # Lo stato 'DISAPPROVED' identifica prodotti con problemi bloccanti su Merchant Center
    query = """
        SELECT
          shopping_product.item_id,
          shopping_product.status
        FROM shopping_product
    """
    
    try:
        print(f"Verifica prodotti non approvati per Account IT ({IT_ACCOUNT_ID})...")
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = IT_ACCOUNT_ID
        request.query = query
        response = ga_service.search(request=request)
        
        count = 0
        total = 0
        
        for row in response:
            total += 1
            if "DISAPPROVED" in str(row.shopping_product.status):
                count += 1

        if count == 0:
            print(f"Analizzati {total} prodotti. Ottimo! Nessun prodotto disapprovato trovato.")
        else:
            print(f"Analizzati {total} prodotti totali.")
            print(f"Trovati {count} prodotti NON APPROVATI (disapprovazioni bloccanti).")

    except GoogleAdsException as ex:
        print(f"Errore API Ads: {ex}")
    except Exception as e:
        print(f"Errore generico: {e}")

if __name__ == "__main__":
    main()
