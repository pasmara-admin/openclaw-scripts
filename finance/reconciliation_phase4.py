import pandas as pd
import pymysql
import re
import warnings
warnings.filterwarnings('ignore')

f = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v9_Intesa.xlsx'
df_docs = pd.read_excel(f)
df_docs['Numero Ordine'] = df_docs['Numero Ordine'].astype(str)

# SECONDO CONTO INTESA (17868)
file_intesa2 = '/root/.openclaw/media/inbound/202510_11_-_Intesa_17868---ee5b6281-7459-43ab-99b1-52ef5d0ad4ce.xlsx'

def extract_order(desc):
    if pd.isna(desc): return None
    match = re.search(r'(72502\d{4})', str(desc))
    if match:
        return match.group(1)
    return None

try:
    df_in2 = pd.read_excel(file_intesa2, skiprows=9)
    df_in2 = df_in2[df_in2['Avere'] > 0]
    
    df_in2['Numero Ordine'] = df_in2['Descrizioni Aggiuntive'].apply(extract_order)
    df_matched2 = df_in2.dropna(subset=['Numero Ordine'])
    
    df_in_agg2 = df_matched2.groupby('Numero Ordine').agg({
        'Avere': 'sum'
    }).reset_index()
    
    matched_count = 0
    for idx, row in df_in_agg2.iterrows():
        mask = df_docs['Numero Ordine'] == row['Numero Ordine']
        # Usiamo pd.isna o string vuota per controllare se non c'è match
        if mask.any() and pd.isna(df_docs.loc[mask, 'Gateway Match'].iloc[0]):
            df_docs.loc[mask, 'Incasso Gateway (€)'] += float(row['Avere'])
            df_docs.loc[mask, 'Gateway Match'] = 'Intesa_17868'
            df_docs.loc[mask, 'Metodo Pagamento v2'] = 'Bonifico bancario'
            matched_count += 1
            
    print(f"Match Intesa (Conto 17868) completato: {matched_count} bonifici aggiuntivi incrociati.")
except Exception as e:
    print("Errore Intesa 2:", e)

# Ricalcolo Netto e Crediti
df_docs['Incasso Netto (€)'] = df_docs['Incasso Gateway (€)'] - df_docs['Commissioni Gateway (€)']
df_docs['Credito da Incassare (€)'] = df_docs['Fatturato Lordo (Kanguro)'] - df_docs['Incasso Gateway (€)']

out_file = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v10_Intesa_All.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_docs.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)

print("Export completato con entrambi i conti Intesa.")
