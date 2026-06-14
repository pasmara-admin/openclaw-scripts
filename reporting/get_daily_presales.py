import os
import subprocess
import json
import pandas as pd
from datetime import datetime, timedelta

# Config
DB_HOST = "34.38.166.212"
DB_USER = "john"
DB_PASS = "3rmiCyf6d~MZDO41"
DB_NAME = "kanguro"
TG_GROUP_ID = "-5066791920"

def run_query(sql):
    cmd = [
        "mysql",
        "-h", DB_HOST,
        "-u", DB_USER,
        f"-p{DB_PASS}",
        DB_NAME,
        "-e", sql,
        "-B"  # Batch mode for TSV output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running query: {result.stderr}")
        return None
    
    lines = result.stdout.strip().split('\n')
    if not lines:
        return pd.DataFrame()
    
    header = lines[0].split('\t')
    data = [line.split('\t') for line in lines[1:]]
    return pd.DataFrame(data, columns=header)

def get_presales_data():
    today = datetime(2026, 6, 14).date()
    # Need data from 5 weeks ago for the "average of 4 previous" calculation
    start_date = today - timedelta(days=40)
    
    sql = f"""
    SELECT 
        date, 
        delivery_country, 
        COUNT(*) as orders, 
        SUM(total) as gmv 
    FROM sal_order 
    WHERE type_id = 2 
      AND is_deleted = 0 
      AND date >= '{start_date}' 
      AND delivery_country IN ('Italia', 'France', 'Deutschland', 'España', 'Österreich') 
    GROUP BY date, delivery_country;
    """
    df = run_query(sql)
    if df is None or df.empty:
        return None
    
    df['orders'] = pd.to_numeric(df['orders'])
    df['gmv'] = pd.to_numeric(df['gmv'])
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

def format_report(df):
    today = datetime(2026, 6, 14).date()
    yesterday = today - timedelta(days=1)
    
    # Last 7 days (including yesterday)
    last_7_days_dates = [yesterday - timedelta(days=i) for i in range(7)]
    last_7_days_dates.reverse()
    
    report = f"📊 *Report Pre-Sales Giornaliero* ({yesterday.strftime('%d/%m/%Y')})\n\n"
    
    # Summary for Yesterday
    y_data = df[df['date'] == yesterday]
    total_orders = y_data['orders'].sum()
    total_gmv = y_data['gmv'].sum()
    
    # Last week same day
    last_week_date = yesterday - timedelta(days=7)
    lw_data = df[df['date'] == last_week_date]
    lw_orders = lw_data['orders'].sum()
    lw_gmv = lw_data['gmv'].sum()
    
    # Average of 4 previous same weekdays
    prev_dates = [yesterday - timedelta(days=7*i) for i in range(1, 5)]
    prev_data = df[df['date'].isin(prev_dates)]
    avg_orders = prev_data.groupby('date')['orders'].sum().mean()
    avg_gmv = prev_data.groupby('date')['gmv'].sum().mean()
    
    report += f"*Totaleieri:* {int(total_orders)} ordini | {total_gmv:,.2f}€\n"
    
    def get_trend(curr, prev):
        if prev == 0: return "N/A"
        diff = (curr - prev) / prev * 100
        emoji = "📈" if diff >= 0 else "📉"
        return f"{emoji} {diff:+.1f}%"

    report += f"Vs Stessa data sett. prec.: {get_trend(total_orders, lw_orders)} (Ord) | {get_trend(total_gmv, lw_gmv)} (GMV)\n"
    report += f"Vs Media 4 sett. prec.: {get_trend(total_orders, avg_orders)} (Ord) | {get_trend(total_gmv, avg_gmv)} (GMV)\n\n"
    
    # Detailed Table for Yesterday
    report += "*Dettaglio per Nazione (Ieri):*\n"
    countries = {'Italia': 'IT', 'France': 'FR', 'Deutschland': 'DE', 'España': 'ES', 'Österreich': 'AT'}
    for country_full, code in countries.items():
        row = y_data[y_data['delivery_country'] == country_full]
        if not row.empty:
            o = int(row['orders'].iloc[0])
            g = float(row['gmv'].iloc[0])
            report += f"• {code}: {o} ordini | {g:,.2f}€\n"
    
    report += "\n*Trend ultimi 7 giorni (Totale):*\n"
    for d in last_7_days_dates:
        d_data = df[df['date'] == d]
        o = d_data['orders'].sum()
        g = d_data['gmv'].sum()
        report += f"• {d.strftime('%d/%m')}: {int(o)} ordini | {g:,.2f}€\n"
        
    return report

def main():
    df = get_presales_data()
    if df is None:
        print("Could not fetch data.")
        return
    
    report_text = format_report(df)
    
    # Send via message tool (telegram)
    # Note: In a real script we'd use 'message' via OpenClaw CLI or API, 
    # but here I can use the tool directly in the next step.
    print(report_text)

if __name__ == "__main__":
    main()
