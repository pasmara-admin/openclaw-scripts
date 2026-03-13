import pandas as pd
import pymysql
import warnings
warnings.filterwarnings('ignore')

print("Connessione a Kanguro...")
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
    o.total AS 'Fatturato Lordo (Kanguro)',
    o.total_paid AS 'Totale Pagato (Kanguro)',
    o.payment_method_name AS 'Metodo Pagamento',
    sl.name AS 'Stato Operativo',
    bsl.name AS 'Stato Fatturazione'
FROM sal_order o
LEFT JOIN sal_order_state_lang sl ON o.state_id = sl.state_id AND sl.lang_id = 1
LEFT JOIN sal_order_billing_state_lang bsl ON o.billing_state_id = bsl.billing_state_id AND bsl.lang_id = 1
WHERE o.type_id = 2 
  AND o.date >= '2025-10-01' 
  AND o.date <= '2025-11-30'
  AND o.is_deleted = b'0'
  AND o.state_id != '00'
"""
df_orders = pd.read_sql(query, connection)
connection.close()

# Inizializza colonne
df_orders['Incasso Gateway (€)'] = 0.0
df_orders['Commissioni Gateway (€)'] = 0.0
df_orders['Incasso Netto (€)'] = 0.0
df_orders['Credito da Incassare (€)'] = df_orders['Fatturato Lordo (Kanguro)']
df_orders['Gateway Match'] = ''

print("Ordini Kanguro caricati:", len(df_orders))

# 1. PAYPLUG MATCH
file_pp = '/root/.openclaw/media/inbound/2025_11_10_-_Accounting_Report_Payplug_2026-03-12---b1e94e55-c874-4003-91eb-1f7ba7acc62c.xlsx'
try:
    df_pp = pd.read_excel(file_pp)
    df_pp = df_pp[df_pp['Tipo'] == 'Pagamento']
    # Aggrega per order_id per evitare doppi
    df_pp_agg = df_pp.groupby('metadata_Order').agg({
        'Importo (€)': 'sum',
        'Commissioni excl. IVA (€)': 'sum'
    }).reset_index()
    # Il metadata_order in PP potrebbe essere un float
    df_pp_agg['Numero Ordine'] = df_pp_agg['metadata_Order'].fillna(0).astype(int).astype(str)
    
    # Merge
    for idx, row in df_pp_agg.iterrows():
        mask = df_orders['Numero Ordine'] == row['Numero Ordine']
        if mask.any():
            df_orders.loc[mask, 'Incasso Gateway (€)'] += float(row['Importo (€)'])
            df_orders.loc[mask, 'Commissioni Gateway (€)'] += float(row['Commissioni excl. IVA (€)'])
            df_orders.loc[mask, 'Gateway Match'] = 'Payplug'
    print("Match PayPlug completato.")
except Exception as e:
    print("Errore PayPlug:", e)

# 2. PAYPAL MATCH
file_paypal = '/root/.openclaw/media/inbound/202510_-_Paypal---8ac13786-531e-4b89-aafe-a95aa5dd9290.csv'
# Paypal file does not explicitly have the order ID in this CSV unless it's in the reference, skipping direct order match for now due to lack of order ID in CSV. 

# 3. KLARNA MATCH
file_klarna = '/root/.openclaw/media/inbound/NOV25_klarna---b608cd4d-d7fe-447c-bbd0-eae73c0c8813.xlsx'
try:
    df_kl = pd.read_excel(file_klarna, skiprows=4)
    df_kl = df_kl.dropna(subset=['merchant_reference2'])
    
    df_kl_sale = df_kl[df_kl['type'] == 'SALE'].groupby('merchant_reference2')['amount'].sum().reset_index()
    df_kl_fee = df_kl[df_kl['type'] == 'FEE'].groupby('merchant_reference2')['amount'].sum().reset_index()
    
    df_kl_sale['Numero Ordine'] = df_kl_sale['merchant_reference2'].astype(str)
    df_kl_fee['Numero Ordine'] = df_kl_fee['merchant_reference2'].astype(str)
    
    for idx, row in df_kl_sale.iterrows():
        mask = df_orders['Numero Ordine'] == row['Numero Ordine']
        if mask.any():
            df_orders.loc[mask, 'Incasso Gateway (€)'] += float(row['amount'])
            df_orders.loc[mask, 'Gateway Match'] = 'Klarna'
            
    for idx, row in df_kl_fee.iterrows():
        mask = df_orders['Numero Ordine'] == row['Numero Ordine']
        if mask.any():
            df_orders.loc[mask, 'Commissioni Gateway (€)'] += float(row['amount'])
    print("Match Klarna completato.")
except Exception as e:
    print("Errore Klarna:", e)

# Calcolo Crediti e Netto
df_orders['Incasso Netto (€)'] = df_orders['Incasso Gateway (€)'] - df_orders['Commissioni Gateway (€)']
df_orders['Credito da Incassare (€)'] = df_orders['Fatturato Lordo (Kanguro)'] - df_orders['Incasso Gateway (€)']

# Sort
df_orders = df_orders.sort_values(by='Data Ordine')

out_file = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Sito_Ott_Nov_2025.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_orders.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)
    
print("File finale salvato:", out_file)
