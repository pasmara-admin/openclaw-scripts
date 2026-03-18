import pandas as pd
import pymysql
import subprocess
import os
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
now = datetime.now()
ref_date = now - timedelta(days=1)
ref_date_str = ref_date.strftime('%d/%m/%Y')

df_attivi['Data Ordine'] = pd.to_datetime(df_attivi['Data Ordine'])
ref_dt = pd.to_datetime(now.date()) # Use today's date for comparison
df_attivi['Ritardo_Gg'] = (ref_dt - df_attivi['Data Ordine']).dt.days

# Delayed orders (>= 3 days)
df_delayed = df_attivi[df_attivi['Ritardo_Gg'] >= 3].sort_values('Data Ordine')
delayed_count = len(df_delayed)

# Format for Excel
df_attivi_out = df_attivi.drop(columns=['Ritardo_Gg'])
df_attivi_out['Data Ordine'] = df_attivi_out['Data Ordine'].dt.strftime('%Y-%m-%d')

out_file = '/root/.openclaw/workspace-finance/Report_Ordini_Non_Fatturati_Daily.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_attivi_out.to_excel(writer, sheet_name='Ordini Attivi', index=False)
    df_annullati.to_excel(writer, sheet_name='Ordini Annullati', index=False)

# Bi-weekly CC logic for Mario
# Check if current week number is even/odd? Or use a state file.
# Better to use week number: now.isocalendar()[1] % 2 == 0
is_mario_week = (now.isocalendar()[1] % 2 == 0)

# Email body construction
subject = f"Report Ordini Non Fatturati - {now.strftime('%d/%m/%Y')}"
body = f"Ciao,\n\nin allegato il report aggiornato degli ordini non ancora fatturati (Stato: 'Da Fatturare').\n\n"
body += f"📊 RIEPILOGO TOTALE:\n• Ordini Attivi da Fatturare: {len(df_attivi)}\n"
body += f"• Ordini Annullati: {len(df_annullati)}\n\n"

if not df_delayed.empty:
    body += f"⚠️ ATTENZIONE: ORDINI IN SOSPESO (>= 3 GIORNI):\n"
    for _, row in df_delayed.iterrows():
        order_date = row['Data Ordine'].strftime('%d/%m/%Y')
        body += f"• {row['Numero Ordine']} ({order_date}) - {row['Cliente']}: €{row['Totale Ordine']:.2f}\n"
else:
    body += "✅ Non ci sono ordini in sospeso da più di 3 giorni.\n"

body += "\nJohn Finance 📊"

# Send Email
env = os.environ.copy()
env["GOG_KEYRING_PASSWORD"] = "produceshop"
env["GOG_ACCOUNT"] = "admin@produceshoptech.com"

recipients = "baldassare.gulotta@produceshop.com,valentina.loreti@produceshop.com"
ccs = ["ivan.cianci@produceshop.com"] # Default CC Ivan

if is_mario_week:
    ccs.append("mario.spina@produceshop.com")

cmd = [
    "gog", "gmail", "send",
    "--to", recipients,
    "--cc", ",".join(ccs),
    "--subject", subject,
    "--body", body,
    "--attach", out_file,
    "--no-input"
]

subprocess.run(cmd, env=env)

# Telegram notification
telegram_msg = f"✅ Report 'Ordini non fatturati' inviato!\n- Totale attivi: {len(df_attivi)}\n- Ritardi >= 3gg: {len(df_delayed)}"
if is_mario_week:
    telegram_msg += "\n- Mario (CFO) in CC questa settimana."

subprocess.run([
    "openclaw", "message", "send",
    "--target", "telegram:-5243139273",
    "--message", telegram_msg
])
