import pandas as pd
import pymysql
import re
import warnings
warnings.filterwarnings('ignore')

f = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v8_PayPal.xlsx'
df_docs = pd.read_excel(f)
df_docs['Numero Ordine'] = df_docs['Numero Ordine'].astype(str)

# 4. INTESA (Bonifici Diretti)
file_intesa = '/root/.openclaw/media/inbound/202510_11_-_Intesa_17962---b2cadf54-c89b-415d-80cc-7412c99ccb76.xlsx'

def extract_order(desc):
    if pd.isna(desc): return None
    match = re.search(r'(72502\d{4})', str(desc))
    if match:
        return match.group(1)
    return None

try:
    df_in = pd.read_excel(file_intesa, skiprows=9)
    df_in = df_in[df_in['Avere'] > 0]
    
    df_in['Numero Ordine'] = df_in['Descrizioni Aggiuntive'].apply(extract_order)
    df_matched = df_in.dropna(subset=['Numero Ordine'])
    
    df_in_agg = df_matched.groupby('Numero Ordine').agg({
        'Avere': 'sum'
    }).reset_index()
    
    matched_count = 0
    for idx, row in df_in_agg.iterrows():
        mask = df_docs['Numero Ordine'] == row['Numero Ordine']
        if mask.any() and pd.isna(df_docs.loc[mask, 'Gateway Match'].iloc[0]):
            df_docs.loc[mask, 'Incasso Gateway (€)'] += float(row['Avere'])
            df_docs.loc[mask, 'Gateway Match'] = 'Intesa'
            df_docs.loc[mask, 'Metodo Pagamento v2'] = 'Bonifico bancario'
            matched_count += 1
            
    print(f"Match Intesa completato: {matched_count} bonifici incrociati.")
except Exception as e:
    print("Errore Intesa:", e)

# Ricalcolo
df_docs['Incasso Netto (€)'] = df_docs['Incasso Gateway (€)'] - df_docs['Commissioni Gateway (€)']
df_docs['Credito da Incassare (€)'] = df_docs['Fatturato Lordo (Kanguro)'] - df_docs['Incasso Gateway (€)']

out_file = '/root/.openclaw/workspace-finance/reconciliation/Master_Reconciliation_Fatture_Sito_Ott_Nov_2025_v9_Intesa.xlsx'
with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
    df_docs.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)

print("Export completato con Intesa.")
