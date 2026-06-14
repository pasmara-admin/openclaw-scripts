import os
import sys
import json
import subprocess
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

def get_ga4_traffic_data(property_id, start_date, end_date):
    token_path = "/root/.openclaw/workspace-marketing/analytics_token.json"
    creds_path = "/root/.config/gogcli/credentials.json"
    
    with open(token_path, "r") as f: token_data = json.load(f)
    with open(creds_path, "r") as f: creds_json = json.load(f)
        
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
                FilterExpression(filter=Filter(field_name="country", string_filter=Filter.StringFilter(value=c)))
                for c in ["Italy", "France", "Germany", "Spain", "Austria"]
            ]
        )
    )
    path_filter = FilterExpression(not_expression=FilterExpression(filter=Filter(field_name="pagePath", string_filter=Filter.StringFilter(value="support.produceshop.info", match_type=Filter.StringFilter.MatchType.CONTAINS))))
    title_filter = FilterExpression(not_expression=FilterExpression(filter=Filter(field_name="pageTitle", string_filter=Filter.StringFilter(value="Customer Care", match_type=Filter.StringFilter.MatchType.CONTAINS))))
    
    combined_filter = FilterExpression(and_group=FilterExpressionList(expressions=[country_filter, path_filter, title_filter]))

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="totalUsers")],
        date_ranges=[DateRange(start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))],
        dimension_filter=combined_filter
    )
    
    response = client.run_report(request)
    rows = []
    if response.rows:
        for row in response.rows:
            rows.append({
                'date': datetime.strptime(row.dimension_values[0].value, '%Y%m%d').date(),
                'users': int(row.metric_values[0].value)
            })
    return pd.DataFrame(rows)

def main():
    # Use 13/06 as "yesterday" for testing based on context
    today = datetime(2026, 6, 14).date()
    yesterday = today - timedelta(days=1)
    
    # Range for history (40 days back)
    start_history = yesterday - timedelta(days=40)
    
    df = get_ga4_traffic_data("311921498", start_history, yesterday)
    if df.empty:
        print("Nessun dato di traffico trovato.")
        return
        
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values('date')

    # 1. Utenti Pre-Sales ultimi 8 giorni
    trend_8d = []
    for i in range(7, -1, -1):
        target = yesterday - timedelta(days=i)
        row = df[df['date'] == target]
        users = int(row['users'].iloc[0]) if not row.empty else 0
        trend_8d.append((target, users))

    # 2. Utenti Pre-Sales stesso giorno settimana precedente
    lw_date = yesterday - timedelta(days=7)
    row_lw = df[df['date'] == lw_date]
    users_lw = int(row_lw['users'].iloc[0]) if not row_lw.empty else 0

    # 3. Media dello stesso giorno delle 4 settimane prima
    prev_dates = [yesterday - timedelta(days=7*i) for i in range(1, 5)]
    history_4w = df[df['date'].isin(prev_dates)]
    avg_4w = history_4w['users'].mean() if not history_4w.empty else 0

    report = f"📊 *Report Traffico Pre-Sales* ({yesterday.strftime('%d/%m/%Y')})\n\n"
    
    report += "*Utenti Pre-Sales ultimi 8 giorni:*\n"
    for d, u in trend_8d:
        report += f"• {d.strftime('%d/%m')}: {u:,} utenti\n"
    
    report += f"\n*Confronto Storico (vs Ieri):*\n"
    report += f"• Stesso giorno sett. prec. ({lw_date.strftime('%d/%m')}): {users_lw:,} utenti\n"
    report += f"• Media stesso giorno (ultime 4 sett.): {int(avg_4w):,} utenti\n"
    
    def get_diff(curr, prev):
        if not prev or prev == 0: return "N/A"
        diff = (curr - prev) / prev * 100
        return f"{'📈' if diff >= 0 else '📉'} {diff:+.1f}%"

    row_y = df[df['date'] == yesterday]
    u_y = int(row_y['users'].iloc[0]) if not row_y.empty else 0
    
    report += f"\n*Variazione Ieri:* {get_diff(u_y, users_lw)} vs sett. prec. | {get_diff(u_y, avg_4w)} vs media 4 sett."

    print(report)

if __name__ == "__main__":
    main()
