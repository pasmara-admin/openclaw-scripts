import pandas as pd
import pymysql
import sys
import os
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--start_date', type=str, required=True)
parser.add_argument('--end_date', type=str, required=True)
args = parser.parse_args()

start_date = args.start_date
end_date = args.end_date

connection = pymysql.connect(host='34.38.166.212', user='john', password='3rmiCyf6d~MZDO41', database='kanguro')

query = f"""
SELECT 
    b.full_number AS 'Invoice Number',
    b.order_number AS 'Order Number',
    DATE(b.date) AS 'Invoice Date',
    t.name AS 'Order Sales Channel',
    b.destination_country AS 'Order Shipping Country',
    so.payment_method_name AS 'Order Payment Method',
    b.customer_name AS 'Customer Name',
    bdr.name AS 'Invoice Reason',
    b.type_id,
    b.related_id,
    dt.name AS 'Tax Name',
    SUM(br.total_price_tax_excl) AS 'Document Revenue Net',
    SUM(br.total_tax) AS 'Document VAT',
    br.tax_rate AS 'VAT Percentage',
    SUM(br.total_price_tax_incl) AS 'Document Revenue Gross'
FROM bil_document b
LEFT JOIN bil_document_reason bdr ON b.reason_id = bdr.id
LEFT JOIN bil_document_row br ON b.id = br.document_id
LEFT JOIN dat_tax dt ON br.tax_id = dt.id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE b.date >= '{start_date}' AND b.date <= '{end_date} 23:59:59' 
AND b.is_deleted = 0 AND br.is_deleted = 0
GROUP BY b.id, br.tax_rate, dt.name, bdr.name
"""
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore', UserWarning)
    df = pd.read_sql(query, connection)

if len(df) == 0:
    print("No data found!")
    sys.exit(0)

country_map = {'Italia': 'Italy', 'Italie': 'Italy', 'Italien': 'Italy', 'Francia': 'France', 'Frankreich': 'France', 'Germania': 'Germany', 'Deutschland': 'Germany', 'Spagna': 'Spain', 'España': 'Spain', 'Espana': 'Spain', 'Svizzera': 'Switzerland', 'Schweiz': 'Switzerland', 'Suisse': 'Switzerland', 'Austria': 'Austria', 'Osterreich': 'Austria', 'Österreich': 'Austria', 'Belgio': 'Belgium', 'Belgique': 'Belgium', 'Belgien': 'Belgium'}
df['Order Shipping Country'] = df['Order Shipping Country'].map(lambda x: country_map.get(x, x))

mask_negative = df['type_id'].isin([2, 4])
df.loc[mask_negative, 'Document Revenue Net'] *= -1
df.loc[mask_negative, 'Document VAT'] *= -1
df.loc[mask_negative, 'Document Revenue Gross'] *= -1

cn_mask = mask_negative
df_cn = df[cn_mask].copy()

orig_ids = tuple(int(x) for x in df_cn['related_id'].dropna().unique()) if len(df_cn) > 0 else ()
if orig_ids:
    q_orig = f"""
    SELECT 
        id,
        full_number AS 'Original Invoice Number',
        DATE(date) AS 'Original Invoice Date',
        total AS 'Original Invoice Gross Amount',
        total_refunded AS 'Total Refunded on Invoice'
    FROM bil_document WHERE id IN {orig_ids_str if len(orig_ids)==1 else str(orig_ids)}
    """
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        df_orig = pd.read_sql(q_orig, connection)
    
    df_cn = df_cn.merge(df_orig, left_on='related_id', right_on='id', how='left').drop(columns=['id', 'related_id', 'type_id'])
    df = df.merge(df_orig, left_on='related_id', right_on='id', how='left')
else:
    for col in ['Original Invoice Number', 'Original Invoice Date', 'Original Invoice Gross Amount', 'Total Refunded on Invoice']:
        df[col] = ''
        df_cn[col] = ''
    df_cn = df_cn.drop(columns=['related_id', 'type_id'], errors='ignore')

df['Residual Document Value'] = ''
df_cn['Residual Document Value'] = ''

db_unico_cols = ['Invoice Number', 'Order Number', 'Invoice Date', 'Order Sales Channel', 'Order Shipping Country', 'Order Payment Method', 'Customer Name', 'Invoice Reason', 'Document Revenue Net', 'Tax Name', 'Document VAT', 'VAT Percentage', 'Document Revenue Gross', 'Original Invoice Number', 'Original Invoice Date', 'Original Invoice Gross Amount', 'Total Refunded on Invoice', 'Residual Document Value']
monthly_cols = ['Invoice Number', 'Order Number', 'Invoice Date', 'Order Sales Channel', 'Order Shipping Country', 'Order Payment Method', 'Customer Name', 'Invoice Reason', 'Document Revenue Net', 'Tax Name', 'Document VAT', 'VAT Percentage', 'Document Revenue Gross']

cn_cols = ['Invoice Number', 'Invoice Date', 'Order Sales Channel', 'Order Shipping Country', 'Order Payment Method', 'Customer Name', 'Order Number', 'Invoice Reason', 'Document Revenue Net', 'Tax Name', 'Document VAT', 'VAT Percentage', 'Document Revenue Gross', 'Original Invoice Number', 'Original Invoice Date', 'Original Invoice Gross Amount', 'Total Refunded on Invoice', 'Residual Document Value']
cn_rename = {'Invoice Number': 'Credit Note Number', 'Invoice Date': 'Credit Note Date', 'Invoice Reason': 'Credit Note Reason', 'Document Revenue Net': 'Credit Note Revenue Net', 'Document VAT': 'Credit Note VAT', 'Document Revenue Gross': 'Credit Note Revenue Gross'}

df_unico = df[db_unico_cols].copy()
df_cn_final = df_cn[cn_cols].rename(columns=cn_rename)

file_name = f'Report_Revenue_{start_date.replace("-","")}_to_{end_date.replace("-","")}.xlsx'
file_path = f'/tmp/{file_name}'

with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    df_unico.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)
    
    df['Temp_Month'] = pd.to_datetime(df['Invoice Date']).dt.strftime('%B %Y')
    m_map = {'October': 'Ottobre', 'November': 'Novembre', 'December': 'Dicembre', 'January': 'Gennaio', 'February': 'Febbraio', 'March': 'Marzo'}
    for m_eng, m_ita in m_map.items(): df['Temp_Month'] = df['Temp_Month'].str.replace(m_eng, m_ita)

    for m in df['Temp_Month'].unique():
        df_m = df[df['Temp_Month'] == m][monthly_cols]
        df_m.to_excel(writer, sheet_name=m, index=False)
    
    df_cn_final.to_excel(writer, sheet_name='Note Credito', index=False)
    ws = writer.sheets['Note Credito']
    if 'Original Invoice Gross Amount' in df_cn_final.columns and 'Total Refunded on Invoice' in df_cn_final.columns:
        idx_gross = df_cn_final.columns.get_loc('Original Invoice Gross Amount') + 1
        idx_ref = df_cn_final.columns.get_loc('Total Refunded on Invoice') + 1
        idx_res = df_cn_final.columns.get_loc('Residual Document Value') + 1
        for row in range(2, len(df_cn_final)+2):
            ws.cell(row=row, column=idx_res).value = f"={ws.cell(row=row, column=idx_gross).coordinate}-{ws.cell(row=row, column=idx_ref).coordinate}"

connection.close()

with open("/tmp/body_report_rev.txt", "w") as f: f.write("In allegato quanto in oggetto.\\n\\nJohn Finance 📊")
env = os.environ.copy()
env["GOG_KEYRING_PASSWORD"] = "produceshop"
env["GOG_ACCOUNT"] = "admin@produceshoptech.com"
subprocess.run(["gog", "gmail", "send", "--to", "mario.spina@produceshop.com", "--subject", file_name.replace(".xlsx", ""), "--body-file", "/tmp/body_report_rev.txt", "--attach", file_path, "--no-input"], env=env)
print("Sent successfully to Mario! File:", file_path)
