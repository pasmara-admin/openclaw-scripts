import pandas as pd
import pymysql
from datetime import datetime, timedelta
import os
import subprocess

# --- CONFIGURATION ---
DB_CONFIG = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

# Recipients
TO_EMAIL = "mario.spina@produceshop.com"
CC_EMAIL = "ivan.cianci@produceshop.com,admin@produceshoptech.com"

# Dates
now = datetime.now()
# Start of month: 2026-03-01
start_of_month = now.replace(day=1).strftime('%Y-%m-%d')
# Yesterday (Wednesday): 2026-03-25
yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
# Start of last week (Thursday to Wednesday)
# Today is Thursday (March 26). Last week started last Thursday (March 19).
last_week_start = (now - timedelta(days=7)).strftime('%Y-%m-%d')

print(f"Fetching data from {start_of_month} to {yesterday}...")

# --- DATABASE CONNECTION ---
connection = pymysql.connect(**DB_CONFIG)

query = f"""
SELECT 
    b.order_number AS 'Order Number',
    b.date AS 'Invoice Date',
    t.name AS 'Order Sales Channel',
    b.destination_country AS 'Order Shipping Country',
    br.total_price_tax_excl AS 'Revenue Net'
FROM bil_document b
LEFT JOIN bil_document_row br ON b.id = br.document_id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE b.date >= '{start_of_month}' AND b.date <= '{yesterday}' 
  AND b.is_deleted = 0 AND br.is_deleted = 0
"""

df = pd.read_sql(query, connection)
connection.close()

if df.empty:
    print("No data found for the specified period.")
    exit()

# Data Cleaning
df['Invoice Date'] = pd.to_datetime(df['Invoice Date'])
df['Revenue Net'] = pd.to_numeric(df['Revenue Net'], errors='coerce').fillna(0)

# --- ANALYSIS ---

# 1. Last Week vs Monthly Total
df_last_week = df[df['Invoice Date'] >= last_week_start]

total_month = df['Revenue Net'].sum()
total_last_week = df_last_week['Revenue Net'].sum()

# 2. Revenue by Country (Month vs Last Week)
country_month = df.groupby('Order Shipping Country')['Revenue Net'].sum().sort_values(ascending=False)
country_week = df_last_week.groupby('Order Shipping Country')['Revenue Net'].sum().reindex(country_month.index).fillna(0)

# 3. Revenue by Marketplace (Month vs Last Week)
# Filter for Marketplaces (excluding 'Sito' or 'Website' if present, but usually we just group all)
channel_month = df.groupby('Order Sales Channel')['Revenue Net'].sum().sort_values(ascending=False)
channel_week = df_last_week.groupby('Order Sales Channel')['Revenue Net'].sum().reindex(channel_month.index).fillna(0)

# --- GENERATE EXCEL ---
file_path = f'/root/.openclaw/workspace-finance/Report_Revenue_MTD_{now.strftime("%Y%m%d")}.xlsx'
df.to_excel(file_path, index=False)

# --- CONSTRUCT EMAIL BODY ---
body = f"Ciao Mario,\n\nin allegato il Report Revenue aggiornato da inizio mese ({start_of_month}) a ieri ({yesterday}).\n\n"
body += f"📊 ANALISI GENERALE\n"
body += f"- Fatturato Netto Totale Mese: €{total_month:,.2f}\n"
body += f"- Fatturato Netto Ultima Settimana ({last_week_start} - {yesterday}): €{total_last_week:,.2f}\n"
body += f"  (Incidenza settimana su mese: {(total_last_week/total_month*100):.1f}%)\n\n"

body += "🌍 TOP 5 PAESI (Settimana vs Mese)\n"
for country in country_month.head(5).index:
    m_val = country_month[country]
    w_val = country_week[country]
    body += f"- {country}: €{w_val:,.2f} (Week) / €{m_val:,.2f} (Month)\n"

body += "\n🏪 TOP MARKETPLACES / CANALI (Settimana vs Mese)\n"
for channel in channel_month.head(5).index:
    m_val = channel_month[channel]
    w_val = channel_week[channel]
    body += f"- {channel}: €{w_val:,.2f} (Week) / €{m_val:,.2f} (Month)\n"

body += "\nSaluti,\nJohn Finance 📊"

# --- SEND EMAIL ---
env = os.environ.copy()
env["GOG_KEYRING_PASSWORD"] = "produceshop"
env["GOG_ACCOUNT"] = "admin@produceshoptech.com"

cmd = [
    "gog", "gmail", "send",
    "--to", TO_EMAIL,
    "--cc", CC_EMAIL,
    "--subject", f"Report Revenue MTD - {now.strftime('%d/%m/%Y')}",
    "--body", body,
    "--attach", file_path,
    "--no-input"
]

result = subprocess.run(cmd, env=env, capture_output=True, text=True)

if result.returncode == 0:
    print(f"SUCCESS: Email sent to {TO_EMAIL}")
    print(f"FILE: {file_path}")
    print(f"ANALYSIS:\n{body}")
else:
    print(f"ERROR: {result.stderr}")
    exit(1)
