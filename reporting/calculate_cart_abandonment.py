import os
import json
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
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

def get_ga4_presales_data(property_id, days_ago):
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
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date=f"{days_ago}daysAgo", end_date="yesterday")],
            dimension_filter=combined_filter
        )
        
        response = client.run_report(request)
        data = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in response.rows}
        return data
    except Exception as e:
        print(f"GA4 Error: {e}")
        return {}

def get_kanguro_orders(days_ago):
    config = {
        'host': '34.38.166.212',
        'user': 'john',
        'password': '3rmiCyf6d~MZDO41',
        'database': 'kanguro'
    }
    country_map = {
        'Italy': ['Italia', 'Italy'],
        'France': ['France', 'Francia'],
        'Germany': ['Deutschland', 'Germania', 'Germany'],
        'Spain': ['España', 'Spagna', 'Spain'],
        'Austria': ['Österreich', 'Austria']
    }
    all_variants = [v for variants in country_map.values() for v in variants]
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        query = f"""
            SELECT delivery_country, COUNT(*) as orders 
            FROM sal_order 
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
              AND date < CURDATE()
              AND delivery_country IN ({','.join(['%s']*len(all_variants))})
              AND type_id = 2
              AND is_deleted = 0
            GROUP BY delivery_country
        """
        cursor.execute(query, [days_ago] + all_variants)
        rows = cursor.fetchall()
        conn.close()
        
        normalized = {k: 0 for k in country_map.keys()}
        for row in rows:
            for ga4_name, variants in country_map.items():
                if row['delivery_country'] in variants:
                    normalized[ga4_name] += row['orders']
                    break
        return normalized
    except Exception as e:
        print(f"DB Error: {e}")
        return {}

def get_db_abandonment():
    config = {
        'host': '62.84.190.199',
        'user': 'john',
        'password': 'qARa6aRozi6I',
        'database': 'produceshop'
    }
    shops = {'Italy': 1, 'France': 5, 'Germany': 4, 'Spain': 6, 'Austria': 9}
    results = {}
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        for country, shop_id in shops.items():
            cursor.execute(f"""
                SELECT 
                    COUNT(id_cart) as total,
                    SUM(CASE WHEN id_cart NOT IN (SELECT id_cart FROM ps_orders) THEN 1 ELSE 0 END) as abandoned
                FROM ps_cart 
                WHERE id_shop = {shop_id} AND date_add >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND date_add < CURDATE()
            """)
            results[country] = cursor.fetchone()
        conn.close()
        return results
    except Exception as e:
        print(f"PS Error: {e}")
        return {}

def main():
    property_id = "311921498"
    
    # 1. Get Data (Yesterday, 7d, 30d)
    sess_y = get_ga4_presales_data(property_id, 1)
    sess_7 = get_ga4_presales_data(property_id, 7)
    sess_30 = get_ga4_presales_data(property_id, 30)
    
    ord_y = get_kanguro_orders(1)
    ord_7 = get_kanguro_orders(7)
    ord_30 = get_kanguro_orders(30)
    
    abandonment = get_db_abandonment()
    
    # 2. Format Report
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
    report = f"🛒 **REPORT PERFORMANCE & ABBANDONO ({yesterday_str})**\n"
    report += "*(Logica Unificata: Traffico Pre-Sales vs Ordini Kanguro)*\n\n"
    
    countries = ['Italy', 'France', 'Germany', 'Spain', 'Austria']
    for c in countries:
        # Abbandono (Database PS)
        stats = abandonment.get(c, {'total': 0, 'abandoned': 0})
        abb_rate = (stats['abandoned'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        # CR (GA4 Sessions / Kanguro Orders)
        cr_y = (ord_y.get(c, 0) / sess_y.get(c, 0) * 100) if sess_y.get(c, 0) > 0 else 0
        cr_7 = (ord_7.get(c, 0) / sess_7.get(c, 0) * 100) if sess_7.get(c, 0) > 0 else 0
        cr_30 = (ord_30.get(c, 0) / sess_30.get(c, 0) * 100) if sess_30.get(c, 0) > 0 else 0
        
        report += f"📍 **{c}**\n"
        report += f"• **CR Pre-Sales: {cr_y:.2f}%** (7gg: {cr_7:.2f}% | 30gg: {cr_30:.2f}%)\n"
        report += f"• **Abbandono Carrello: {abb_rate:.1f}%**\n"
        report += f"• Sessioni: {sess_y.get(c, 0)} | Ordini: {ord_y.get(c, 0)}\n\n"
    
    report += "--- \n*Nota: CR calcolata solo su ordini Canale ProduceShop e traffico depurato da assistenza.*"
    print(report)

if __name__ == "__main__":
    main()
