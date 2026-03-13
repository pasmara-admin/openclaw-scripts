import pandas as pd
import pymysql
import sys
from datetime import datetime

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
    'Italia': 'Italy', 'Italie': 'Italy', 'Francia': 'France',
    'Germania': 'Germany', 'Deutschland': 'Germany', 'Spagna': 'Spain',
    'Espana': 'Spain', 'España': 'Spain', 'Austria': 'Austria',
    'Osterreich': 'Austria', 'Österreich': 'Austria', 'Svizzera': 'Switzerland',
    'Suisse': 'Switzerland', 'Schweiz': 'Switzerland', 'Belgio': 'Belgium',
    'Belgique': 'Belgium', 'Paesi Bassi': 'Netherlands', 'Olanda': 'Netherlands',
    'Croazia': 'Croatia', 'Slovenia': 'Slovenia', 'Romania': 'Romania',
    'Portogallo': 'Portugal', 'Grecia': 'Greece', 'Svezia': 'Sweden',
    'Danimarca': 'Denmark', 'Polonia': 'Poland', 'Repubblica Ceca': 'Czech Republic',
    'Ungheria': 'Hungary', 'Irlanda': 'Ireland'
}

df['Nazione'] = df['Nazione'].astype(str).str.strip().str.title()
df['Nazione'] = df['Nazione'].replace(country_map)

mask = df['Stato Operativo'].astype(str).str.strip().str.lower() == 'annullato'
df_annullati = df[mask]
df_attivi = df[~mask]

out_file = '/root/.openclaw/workspace-finance/Report_Ordini_Non_Fatturati_Daily.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_attivi.to_excel(writer, sheet_name='Ordini Attivi', index=False)
    df_annullati.to_excel(writer, sheet_name='Ordini Annullati', index=False)

print(out_file)
