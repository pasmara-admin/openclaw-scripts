import pandas as pd
import pymysql
import warnings
warnings.filterwarnings('ignore')

print("Connessione a Kanguro per estrazione Fatture...")
connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)

query = """
SELECT 
    b.full_number AS 'Numero Documento',
    DATE(b.date) AS 'Data Documento',
    dt.name AS 'Tipo Documento',
    b.total AS 'Fatturato Lordo (Kanguro)',
    b.order_number AS 'Numero Ordine',
    so.date AS 'Data Ordine',
    so.payment_method_name AS 'Metodo Pagamento',
    t.name AS 'Canale Vendita',
    b.type_id
FROM bil_document b
LEFT JOIN bil_document_type dt ON b.type_id = dt.id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE so.type_id = 2 
  AND b.date >= '2025-10-01' 
  AND b.date <= '2025-11-30'
  AND b.is_deleted = b'0'
"""
df_docs = pd.read_sql(query, connection)
connection.close()

# Rendo negativi i totali delle Note di Credito e Rimborsi (type_id 2 o 4)
mask_nc = df_docs['type_id'].isin([2, 4])
df_docs.loc[mask_nc, 'Fatturato Lordo (Kanguro)'] = -df_docs.loc[mask_nc, 'Fatturato Lordo (Kanguro)'].abs()
df_docs = df_docs.drop(columns=['type_id'])

# Inizializza colonne
df_docs['Incasso Gateway (€)'] = 0.0
df_docs['Commissioni Gateway (€)'] = 0.0
df_docs['Incasso Netto (€)'] = 0.0
df_docs['Credito da Incassare (€)'] = df_docs['Fatturato Lordo (Kanguro)']
df_docs['Gateway Match'] = ''
df_docs['Metodo Pagamento v2'] = df_docs['Metodo Pagamento'] # Inizializziamo con quello di Kanguro come fallback

print(f"Fatture Kanguro caricate: {len(df_docs)}")

# 1. PAYPLUG MATCH
file_pp = '/root/.openclaw/media/inbound/2025_11_10_-_Accounting_Report_Payplug_2026-03-12---b1e94e55-c874-4003-91eb-1f7ba7acc62c.xlsx'
try:
    df_pp = pd.read_excel(file_pp)
    # Prendiamo pagamenti e rimborsi per avere il netto
    df_pp = df_pp[df_pp['Tipo'].isin(['Pagamento', 'Rimborso'])]
    df_pp_agg = df_pp.groupby('metadata_Order').agg({
        'Importo (€)': 'sum',
        'Commissioni excl. IVA (€)': 'sum',
        'Channel': 'first' # Estraiamo il sub-circuito per la transcodifica
    }).reset_index()
    df_pp_agg['Numero Ordine'] = df_pp_agg['metadata_Order'].fillna(0).astype(int).astype(str)
    
    # Merge on Numero Ordine
    for idx, row in df_pp_agg.iterrows():
        mask = df_docs['Numero Ordine'] == row['Numero Ordine']
        if mask.any():
            df_docs.loc[mask, 'Incasso Gateway (€)'] += float(row['Importo (€)'])
            df_docs.loc[mask, 'Commissioni Gateway (€)'] += float(row['Commissioni excl. IVA (€)'])
            df_docs.loc[mask, 'Gateway Match'] = 'Payplug'
            
            # Applica transcodifica da file PayPlug
            channel_val = str(row['Channel']).strip()
            if pd.notna(channel_val) and channel_val != 'nan' and channel_val != '':
                df_docs.loc[mask, 'Metodo Pagamento v2'] = f"Payplug - {channel_val}"
            else:
                df_docs.loc[mask, 'Metodo Pagamento v2'] = "Payplug"
                
    print("Match PayPlug completato.")
except Exception as e:
    print("Errore PayPlug:", e)

# 2. KLARNA MATCH
file_klarna = '/root/.openclaw/media/inbound/NOV25_klarna---b608cd4d-d7fe-447c-bbd0-eae73c0c8813.xlsx'
try:
    df_kl = pd.read_excel(file_klarna, skiprows=4)
    df_kl = df_kl.dropna(subset=['merchant_reference2'])
    
    # Rimborsi (RETURN) and Vendite (SALE)
    df_kl_sale = df_kl[df_kl['type'].isin(['SALE', 'RETURN'])].groupby('merchant_reference2')['amount'].sum().reset_index()
    df_kl_fee = df_kl[df_kl['type'] == 'FEE'].groupby('merchant_reference2')['amount'].sum().reset_index()
    
    df_kl_sale['Numero Ordine'] = df_kl_sale['merchant_reference2'].astype(str)
    df_kl_fee['Numero Ordine'] = df_kl_fee['merchant_reference2'].astype(str)
    
    for idx, row in df_kl_sale.iterrows():
        mask = df_docs['Numero Ordine'] == row['Numero Ordine']
        if mask.any():
            df_docs.loc[mask, 'Incasso Gateway (€)'] += float(row['amount'])
            df_docs.loc[mask, 'Gateway Match'] = 'Klarna'
            df_docs.loc[mask, 'Metodo Pagamento v2'] = 'Klarna' # Transcodifica fissa
            
    for idx, row in df_kl_fee.iterrows():
        mask = df_docs['Numero Ordine'] == row['Numero Ordine']
        if mask.any():
            df_docs.loc[mask, 'Commissioni Gateway (€)'] += float(row['amount'])
    print("Match Klarna completato.")
except Exception as e:
    print("Errore Klarna:", e)

# Calcolo Crediti e Netto
df_docs['Incasso Netto (€)'] = df_docs['Incasso Gateway (€)'] - df_docs['Commissioni Gateway (€)']
df_docs['Credito da Incassare (€)'] = df_docs['Fatturato Lordo (Kanguro)'] - df_docs['Incasso Gateway (€)']

# Sort
df_docs = df_docs.sort_values(by='Data Documento')

out_file = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v2.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_docs.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)
    
print("File finale salvato:", out_file)
