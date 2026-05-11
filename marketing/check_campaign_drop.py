import sys
from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime, timedelta

def main():
    client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
    customer_id = "2327095345"
    ga_service = client.get_service("GoogleAdsService")

    today = datetime.now().strftime('%Y-%m-%d')
    last_sat = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            metrics.cost_micros
        FROM campaign
        WHERE segments.date = '{today}'
    """
    
    print(f"Checking IT Campaigns Status Today vs Last Saturday")
    print("-" * 50)
    
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    response = ga_service.search(request=request)
    
    today_campaigns = {}
    for row in response:
        today_campaigns[row.campaign.id] = {
            "name": row.campaign.name,
            "status": str(row.campaign.status),
            "cost": row.metrics.cost_micros / 1000000.0
        }

    query_last = f"""
        SELECT
            campaign.id,
            campaign.name,
            metrics.cost_micros
        FROM campaign
        WHERE segments.date = '{last_sat}'
          AND metrics.cost_micros > 0
    """
    request.query = query_last
    response_last = ga_service.search(request=request)
    
    print(f"{'Campaign Name':<40} | {'Status':<10} | {'Today':<10} | {'Last Sat':<10}")
    for row in response_last:
        cid = row.campaign.id
        name = row.campaign.name
        cost_last = row.metrics.cost_micros / 1000000.0
        
        c_today = today_campaigns.get(cid, {"status": "NOT_FOUND", "cost": 0.0})
        print(f"{name[:40]:<40} | {c_today['status']:<10} | €{c_today['cost']:<10.2f} | €{cost_last:<10.2f}")

if __name__ == "__main__":
    main()
