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
from google.auth.transport.requests import Request

# Kanguro Config
DB_HOST = "34.38.166.212"
DB_USER = "john"
DB_PASS = "3rmiCyf6d~MZDO41"
DB_NAME = "kanguro"

def run_query(sql):
    cmd = [
        "mysql", "-h", DB_HOST, "-u", DB_USER, f"-p{DB_PASS}", DB_NAME, "-e", sql, "-B"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0: return pd.DataFrame()
    lines = result.stdout.strip().split('\n')
    if not lines or len(lines) < 2: return pd.DataFrame()
    header = lines[0].split('\t')
    data = [line.split('\t') for line in lines[1:]]
    return pd.DataFrame(data, columns=header)

def get_ga4_data(property_id, start_date, end_date):
    token_path = "/root/.openclaw/workspace-marketing/analytics_token.json"
    creds_path = "/root/.config/gogcli/credentials.json"
    
    with open(token_path, "r") as f: token_data = json.load(f)
    with open(creds_path, "r") as f: creds_json = json.load(f)
        
    access_token = token_data.get("access_token")
    if access_token == "placeholder":
        access_token = None
        
    creds = Credentials(
        token=access_token,
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_json["client_id"],
        client_secret=creds_json["client_secret"]
    )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_data["access_token"] = creds.token
            with open(token_path, "w") as f:
                json.dump(token_data, f)

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
        dimensions=[Dimension(name="date"), Dimension(name="country")],
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
                'country': row.dimension_values[1].value,
                'users': int(row.metric_values[0].value)
            })
    return pd.DataFrame(rows)

def main():
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    # Fetch 40 days of data for averages
    start_history = yesterday - timedelta(days=40)
    
    # Orders from Kanguro
    sql = f"""
    SELECT date, delivery_country, COUNT(*) as orders, SUM(total) as gmv 
    FROM sal_order 
    WHERE type_id = 2 AND is_deleted = 0 AND date >= '{start_history}' 
      AND delivery_country IN ('Italia', 'France', 'Deutschland', 'España', 'Österreich') 
    GROUP BY date, delivery_country;
    """
    df_orders = run_query(sql)
    if df_orders.empty:
        print("Errore: Nessun ordine trovato.")
        return
        
    df_orders['orders'] = pd.to_numeric(df_orders['orders'])
    df_orders['gmv'] = pd.to_numeric(df_orders['gmv'])
    df_orders['date'] = pd.to_datetime(df_orders['date']).dt.date
    
    # GA4 Data
    df_ga4 = get_ga4_data("311921498", start_history, yesterday)
    
    # Mapping
    countries_map = {
        'Italy': 'Italia', 
        'France': 'France', 
        'Germany': 'Deutschland', 
        'Spain': 'España', 
        'Austria': 'Österreich'
    }
    codes = {'Italia': 'IT', 'France': 'FR', 'Deutschland': 'DE', 'España': 'ES', 'Österreich': 'AT'}
    df_ga4['delivery_country'] = df_ga4['country'].map(countries_map)

    # Merge
    df = pd.merge(df_orders, df_ga4, on=['date', 'delivery_country'], how='outer').fillna(0)
    
    def get_daily_totals(target_date):
        day_df = df[df['date'] == target_date]
        return day_df['users'].sum(), day_df['orders'].sum(), day_df['gmv'].sum()

    u_y, o_y, g_y = get_daily_totals(yesterday)
    cr_y = (o_y / u_y * 100) if u_y > 0 else 0.0

    # 1. Utenti Pre-Sales stesso giorno settimana precedente
    lw_date = yesterday - timedelta(days=7)
    u_lw, o_lw, g_lw = get_daily_totals(lw_date)
    cr_lw = (o_lw / u_lw * 100) if u_lw > 0 else 0.0

    # 2. Media dello stesso giorno delle 4 settimane prima
    prev_dates = [yesterday - timedelta(days=7*i) for i in range(1, 5)]
    history = df[df['date'].isin(prev_dates)].groupby('date').sum()
    avg_u = history['users'].mean()
    avg_cr = (history['orders'].sum() / history['users'].sum() * 100) if history['users'].sum() > 0 else 0.0

    def get_trend(curr, prev):
        if not prev or prev == 0: return "N/A"
        diff = (curr - prev) / prev * 100
        return f"{'📈' if diff >= 0 else '📉'} {diff:+.1f}%"

    report = f"📊 *Report Pre-Sales Giornaliero* ({yesterday.strftime('%d/%m/%Y')})\n\n"
    report += f"*Totale Ieri:* {int(u_y):,} Utenti | {int(o_y)} Ordini | {cr_y:.2f}% CR | {g_y:,.2f}€\n"
    report += f"Vs Stessa data sett. prec.: {get_trend(u_y, u_lw)} (Utenti) | {get_trend(cr_y, cr_lw)} (CR)\n"
    report += f"Vs Media 4 sett. prec.: {get_trend(u_y, avg_u)} (Utenti) | {get_trend(cr_y, avg_cr)} (CR)\n\n"
    
    report += "*Dettaglio per Nazione (Pre-Sales):*\n"
    y_data = df[df['date'] == yesterday]
    for country_full, code in codes.items():
        row = y_data[y_data['delivery_country'] == country_full]
        u = int(row['users'].iloc[0]) if not row.empty else 0
        o = int(row['orders'].iloc[0]) if not row.empty else 0
        g = float(row['gmv'].iloc[0]) if not row.empty else 0.0
        cr = (o / u * 100) if u > 0 else 0.0
        report += f"• {code}: {u:,} Ut | {o} Ord | *{cr:.2f}% CR* | {g:,.2f}€\n"
    
    report += "\n*Utenti Pre-Sales ultimi 8 giorni:*\n"
    for i in range(7, -1, -1):
        d = yesterday - timedelta(days=i)
        u_d, o_d, g_d = get_daily_totals(d)
        cr_d = (o_d / u_d * 100) if u_d > 0 else 0.0
        report += f"• {d.strftime('%d/%m')}: {int(u_d):,} utenti | {cr_d:.2f}% CR\n"
        
    print(report)

if __name__ == "__main__":
    main()
