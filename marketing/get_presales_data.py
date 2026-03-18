import os
import sys
import json
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    Filter,
    FilterExpression,
    FilterExpressionList,
)
from google.oauth2.credentials import Credentials

def get_presales_revenue_yesterday(property_id):
    token_path = "/root/.openclaw/workspace-marketing/analytics_token.json"
    creds_path = "/root/.config/gogcli/credentials.json"
    
    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)
        with open(creds_path, "r") as f:
            creds_json = json.load(f)
            
        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_json["client_id"],
            client_secret=creds_json["client_secret"]
        )

        client = BetaAnalyticsDataClient(credentials=creds)
        
        # Define the filters based on the screenshot:
        # 1. Country includes: Italy, France, Germany, Spain, Austria (OR)
        # 2. Page Path does NOT contain support.produceshop.info (AND)
        # 3. Page Title does NOT contain Customer Care (AND)
        
        country_filter = FilterExpression(
            or_group=FilterExpressionList(
                expressions=[
                    FilterExpression(filter=Filter(field_name="country", string_filter=Filter.StringFilter(value="Italy"))),
                    FilterExpression(filter=Filter(field_name="country", string_filter=Filter.StringFilter(value="France"))),
                    FilterExpression(filter=Filter(field_name="country", string_filter=Filter.StringFilter(value="Germany"))),
                    FilterExpression(filter=Filter(field_name="country", string_filter=Filter.StringFilter(value="Spain"))),
                    FilterExpression(filter=Filter(field_name="country", string_filter=Filter.StringFilter(value="Austria"))),
                ]
            )
        )
        
        path_filter = FilterExpression(
            not_expression=FilterExpression(
                filter=Filter(
                    field_name="pagePath", 
                    string_filter=Filter.StringFilter(value="support.produceshop.info", match_type=Filter.StringFilter.MatchType.CONTAINS)
                )
            )
        )
        
        title_filter = FilterExpression(
            not_expression=FilterExpression(
                filter=Filter(
                    field_name="pageTitle", 
                    string_filter=Filter.StringFilter(value="Customer Care", match_type=Filter.StringFilter.MatchType.CONTAINS)
                )
            )
        )
        
        combined_filter = FilterExpression(
            and_group=FilterExpressionList(
                expressions=[country_filter, path_filter, title_filter]
            )
        )

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="country")],
            metrics=[Metric(name="purchaseRevenue"), Metric(name="sessions")],
            date_ranges=[DateRange(start_date="yesterday", end_date="yesterday")],
            dimension_filter=combined_filter
        )
        
        response = client.run_report(request)
        
        print(f"📊 REPORT GA4: TRAFFICO PRESALES (Ieri)")
        if response.rows:
            total_revenue = 0.0
            total_sessions = 0
            for row in response.rows:
                country = row.dimension_values[0].value
                revenue = float(row.metric_values[0].value)
                sessions = int(row.metric_values[1].value)
                total_revenue += revenue
                total_sessions += sessions
                print(f"- {country}: €{revenue:.2f} ({sessions} sessioni)")
            print(f"\nTOTALE PRESALES IERI: €{total_revenue:.2f}")
            print(f"SESSIONI TOTALI PRESALES: {total_sessions}")
        else:
            print("Nessun dato trovato per i filtri specificati.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    property_id = "311921498"
    get_presales_revenue_yesterday(property_id)
