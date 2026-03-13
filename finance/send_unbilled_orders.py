import pandas as pd
import pymysql
import subprocess
import os
import calendar
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Connect to database
connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)

query = """
SELECT 
    o.number AS 'Numero Ordine',
    o.date AS 'Data Ordine',
    o.total AS 'Totale Ordine',
    psl.name AS 'Stato Pagamento',
    sl.name AS 'Stato Operativo',
    t.name AS 'Canale di Vendita',
    o.payment_method_name AS 'Metodo di Pagamento',
    o.customer_name AS 'Cliente',
    o.customer_country AS 'Nazione'
FROM sal_order o
LEFT JOIN sal_order_payment_state_lang psl ON o.payment_state_id = psl.payment_state_id AND psl.lang_id = 1
LEFT JOIN sal_order_state_lang sl ON o.state_id = sl.state_id AND sl.lang_id = 1
LEFT JOIN sal_order_type t ON o.type_id = t.id
WHERE o.billing_state_id = '10' 
  AND o.date >= '2025-10-01'
  AND o.is_deleted = b'0'
ORDER BY o.date DESC
"""

df = pd.read_sql(query, connection)
connection.close()

# Translations and standardizations
country_map = {
    'Italia': 'Italy', 'Italie': 'Italy', 'Francia': 'France', 'Germania': 'Germany', 'Deutschland': 'Germany',
    'Spagna': 'Spain', 'Espana': 'Spain', 'España': 'Spain', 'Austria': 'Austria', 'Osterreich': 'Austria',
    'Österreich': 'Austria', 'Svizzera': 'Switzerland', 'Suisse': 'Switzerland', 'Schweiz': 'Switzerland',
    'Belgio': 'Belgium', 'Belgique': 'Belgium', 'Paesi Bassi': 'Netherlands', 'Olanda': 'Netherlands',
    'Croazia': 'Croatia', 'Slovenia': 'Slovenia', 'Romania': 'Romania', 'Portogallo': 'Portugal',
    'Grecia': 'Greece', 'Svezia': 'Sweden', 'Danimarca': 'Denmark', 'Polonia': 'Poland',
    'Repubblica Ceca': 'Czech Republic', 'Ungheria': 'Hungary', 'Irlanda': 'Ireland'
}

df['Nazione'] = df['Nazione'].astype(str).str.strip().str.title()
df['Nazione'] = df['Nazione'].replace(country_map)

mask = df['Stato Operativo'].astype(str).str.strip().str.lower() == 'annullato'
df_annullati = df[mask]
df_attivi = df[~mask].copy()

# Date calculations
ref_date = datetime.now() - timedelta(days=1)
ref_date_str = ref_date.strftime('%d/%m/%Y')

df_attivi['Data Ordine'] = pd.to_datetime(df_attivi['Data Ordine'])
ref_dt = pd.to_datetime(ref_date.date())
delays = (ref_dt - df_attivi['Data Ordine']).dt.days
delayed_count = int((delays >= 3).sum())

# Previous months calculations
month_names = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
mask_prev = (df_attivi['Data Ordine'].dt.year < ref_dt.year) | ((df_attivi['Data Ordine'].dt.year == ref_dt.year) & (df_attivi['Data Ordine'].dt.month < ref_dt.month))
df_prev = df_attivi[mask_prev]

# Restore string format for excel
df_attivi['Data Ordine'] = df_attivi['Data Ordine'].dt.strftime('%Y-%m-%d')

out_file = '/root/.openclaw/workspace-finance/Report_Ordini_Non_Fatturati_Daily.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_attivi.to_excel(writer, sheet_name='Ordini Attivi', index=False)
    df_annullati.to_excel(writer, sheet_name='Ordini Annullati', index=False)

# Email prep
subject = f"Ordini attivi non fatturati up to {ref_date_str}"
body = "In allegato quanto in oggetto."
cc_arg = []

if delayed_count > 0:
    body += f"\n\nCi sono {delayed_count} ordini con più di 3 gg di ritardo dalla data dell'ordine."
    cc_arg = ["--cc", "ivan.cianci@produceshop.com"]

if not df_prev.empty:
    body += f"\n\n📋 Riepilogo ordini non fatturati di mesi precedenti ({len(df_prev)} ordini totali):"
    summary = df_prev.groupby([df_prev['Data Ordine'].str[:4], df_prev['Data Ordine'].str[5:7]]).size()
    for (year, month), count in summary.items():
        month_name = month_names[int(month)]
        body += f"\n- {month_name} {year}: {count} ordini"

body += "\n\nJohn Finance 📊"

env = os.environ.copy()
env["GOG_KEYRING_PASSWORD"] = "produceshop"
env["GOG_ACCOUNT"] = "admin@produceshoptech.com"

cmd = [
    "gog", "gmail", "send",
    "--to", "baldassare.gulotta@produceshop.com,valentina.loreti@produceshop.com",
    "--subject", subject,
    "--body", body,
    "--attach", out_file,
    "--no-input"
] + cc_arg

subprocess.run(cmd, env=env)

# Telegram notification
subprocess.run([
    "openclaw", "message", "send",
    "--target", "telegram:-5243139273",
    "--message", f"✅ Email 'Ordini non fatturati' inviata! Ritardi >= 3gg: {delayed_count}. Ordini mesi passati: {len(df_prev)}"
])
