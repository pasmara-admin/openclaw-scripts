import sys
from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime, timedelta

def get_spend(client, customer_id, start_date, end_date):
    query = f"""
        SELECT
            metrics.cost_micros
        FROM customer
        WHERE segments.date >= '{start_date}' AND segments.date <= '{end_date}'
    """
    ga_service = client.get_service("GoogleAdsService")
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    response = ga_service.search(request=request)
    
    total_micros = 0
    for row in response:
        total_micros += row.metrics.cost_micros
    return total_micros / 1000000.0

def get_sku_spend(client, customer_id, sku, start_date, end_date):
    query = f"""
        SELECT
            segments.product_item_id,
            metrics.cost_micros
        FROM shopping_performance_view
        WHERE segments.date >= '{start_date}' AND segments.date <= '{end_date}'
          AND segments.product_item_id = '{sku.lower()}'
    """
    ga_service = client.get_service("GoogleAdsService")
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    response = ga_service.search(request=request)
    
    total_micros = 0
    for row in response:
        total_micros += row.metrics.cost_micros
    return total_micros / 1000000.0

def main():
    client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    customer_ids = {
        "IT": "2327095345",
        "FR": "4100556149",
        "ES": "8633848117",
        "DE": "6241768674",
        "AT": "9641081570"
    }
    
    today = datetime.now().strftime('%Y-%m-%d')
    last_sat = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    skus = ["SA800TEX4PZE", "SA800TEXLE4PZN", "DI1798MIG"]
    
    print(f"Report Ads Comparison: {today} vs {last_sat}")
    print("-" * 50)
    
    total_today = 0
    total_last = 0
    
    for country, cid in customer_ids.items():
        spend_today = get_spend(client, cid, today, today)
        spend_last = get_spend(client, cid, last_sat, last_sat)
        total_today += spend_today
        total_last += spend_last
        print(f"[{country}] Today: €{spend_today:.2f} | Last Sat: €{spend_last:.2f}")
    
    print("-" * 50)
    print(f"TOTAL Today: €{total_today:.2f}")
    print(f"TOTAL Last Sat: €{total_last:.2f}")
    print("-" * 50)
    print("OOS SKU Spend (Today):")
    for sku in skus:
        sku_total = 0
        for country, cid in customer_ids.items():
            sku_total += get_sku_spend(client, cid, sku, today, today)
        print(f"SKU {sku}: €{sku_total:.2f}")

if __name__ == "__main__":
    main()
