import os
import subprocess
import pandas as pd
from datetime import datetime, timedelta

# Config
DB_HOST = "34.38.166.212"
DB_USER = "john"
DB_PASS = "3rmiCyf6d~MZDO41"
DB_NAME = "kanguro"

def run_query(sql):
    cmd = [
        "mysql",
        "-h", DB_HOST,
        "-u", DB_USER,
        f"-p{DB_PASS}",
        DB_NAME,
        "-e", sql,
        "-B"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    lines = result.stdout.strip().split('\n')
    if not lines or len(lines) < 2:
        return pd.DataFrame()
    header = lines[0].split('\t')
    data = [line.split('\t') for line in lines[1:]]
    return pd.DataFrame(data, columns=header)

def main():
    today = datetime.now().date()
    start_date = today - timedelta(days=40)
    
    sql = f"""
    SELECT date, delivery_country, COUNT(*) as orders, SUM(total) as gmv 
    FROM sal_order 
    WHERE type_id = 2 AND is_deleted = 0 AND date >= '{start_date}' 
      AND delivery_country IN ('Italia', 'France', 'Deutschland', 'España', 'Österreich') 
    GROUP BY date, delivery_country;
    """
    df = run_query(sql)
    if df is None or df.empty:
        print("Errore nel recupero dati.")
        return

    df['orders'] = pd.to_numeric(df['orders'])
    df['gmv'] = pd.to_numeric(df['gmv'])
    df['date'] = pd.to_datetime(df['date']).dt.date

    yesterday = today - timedelta(days=1)
    y_data = df[df['date'] == yesterday]
    
    total_orders = y_data['orders'].sum()
    total_gmv = y_data['gmv'].sum()
    
    lw_date = yesterday - timedelta(days=7)
    lw_data = df[df['date'] == lw_date]
    lw_orders = lw_data['orders'].sum()
    lw_gmv = lw_data['gmv'].sum()
    
    prev_dates = [yesterday - timedelta(days=7*i) for i in range(1, 5)]
    prev_data = df[df['date'].isin(prev_dates)]
    avg_orders = prev_data.groupby('date')['orders'].sum().mean()
    avg_gmv = prev_data.groupby('date')['gmv'].sum().mean()

    report = f"📊 *Report Pre-Sales Giornaliero* ({yesterday.strftime('%d/%m/%Y')})\n\n"
    report += f"*Totale Ieri:* {int(total_orders)} ordini | {total_gmv:,.2f}€\n"
    
    def get_trend(curr, prev):
        if not prev or prev == 0: return "N/A"
        diff = (curr - prev) / prev * 100
        return f"{'📈' if diff >= 0 else '📉'} {diff:+.1f}%"

    report += f"Vs Stessa data sett. prec.: {get_trend(total_orders, lw_orders)} (Ord) | {get_trend(total_gmv, lw_gmv)} (GMV)\n"
    report += f"Vs Media 4 sett. prec.: {get_trend(total_orders, avg_orders)} (Ord) | {get_trend(total_gmv, avg_gmv)} (GMV)\n\n"
    
    report += "*Dettaglio per Nazione (Ieri):*\n"
    countries = {'Italia': 'IT', 'France': 'FR', 'Deutschland': 'DE', 'España': 'ES', 'Österreich': 'AT'}
    for country_full, code in countries.items():
        row = y_data[y_data['delivery_country'] == country_full]
        o = int(row['orders'].iloc[0]) if not row.empty else 0
        g = float(row['gmv'].iloc[0]) if not row.empty else 0.0
        report += f"• {code}: {o} ordini | {g:,.2f}€\n"
    
    report += "\n*Trend ultimi 7 giorni (Totale):*\n"
    for i in range(6, -1, -1):
        d = yesterday - timedelta(days=i)
        d_data = df[df['date'] == d]
        o = d_data['orders'].sum()
        g = d_data['gmv'].sum()
        report += f"• {d.strftime('%d/%m')}: {int(o)} ordini | {g:,.2f}€\n"
        
    print(report)

if __name__ == "__main__":
    main()
