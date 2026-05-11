import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main():
    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    customer_id = "2327095345" # IT
    ga_service = client.get_service("GoogleAdsService")

    # Query per shopping_product (v17+)
    query = """
        SELECT
            shopping_product.status,
            shopping_product.issues
        FROM shopping_product
    """

    try:
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query
        response = ga_service.search(request=request)
        
        counts = {}
        disapproval_reasons = {}

        for row in response:
            product = row.shopping_product
            status = str(product.status)
            counts[status] = counts.get(status, 0) + 1
            
            if "DISAPPROVED" in status or "NOT_ELIGIBLE" in status or "4" in status:
                for issue in product.issues:
                    reason = issue.description
                    disapproval_reasons[reason] = disapproval_reasons.get(reason, 0) + 1
        
        print(f"GMC Status Report (IT: {customer_id})")
        print("-" * 30)
        for status, count in counts.items():
            print(f"{status}: {count}")
        
        if disapproval_reasons:
            print("\nPrincipali motivazioni di disapprovazione:")
            # Sort by count
            sorted_reasons = sorted(disapproval_reasons.items(), key=lambda x: x[1], reverse=True)
            for reason, count in sorted_reasons[:5]:
                print(f"- {reason}: {count} prodotti")
        else:
            print("\nNessuna disapprovazione rilevata.")

    except GoogleAdsException as ex:
        # Fallback to product_view if shopping_product is not supported
        print(f"shopping_product failed, trying product_view fallback... ({ex.error.code})")
        query_fallback = """
            SELECT
                product_view.status
            FROM product_view
        """
        try:
            request.query = query_fallback
            response = ga_service.search(request=request)
            counts = {}
            for row in response:
                status = str(row.product_view.status)
                counts[status] = counts.get(status, 0) + 1
            
            print(f"GMC Status Report (Fallback product_view)")
            print("-" * 30)
            for status, count in counts.items():
                print(f"{status}: {count}")
        except Exception as e:
            print(f"Fallback failed: {e}")

if __name__ == "__main__":
    main()
