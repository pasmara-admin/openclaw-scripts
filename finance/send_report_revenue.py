import pandas as pd
import pymysql
import sys
import os
import argparse
from datetime import datetime
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--start_date', type=str, required=True)
parser.add_argument('--end_date', type=str, required=True)
args = parser.parse_args()

start_date = args.start_date
end_date = args.end_date

connection = pymysql.connect(
    host='34.38.166.212',
    user='john',
    password='3rmiCyf6d~MZDO41',
    database='kanguro'
)

query_main = f"""
SELECT 
    b.id,
    b.type_id,
    b.related_id,
    b.order_number AS 'Order Number',
    b.full_number AS 'Document Number',
    b.date AS 'Invoice Date',
    t.name AS 'Order Sales Channel',
    b.destination_country AS 'Order Shipping Country',
    so.payment_method_name AS 'Order Payment Method',
    b.customer_name AS 'Customer Name',
    br.reference AS 'Item Reference',
    br.description AS 'Item Name',
    br.qty AS 'Sold Quantity',
    br.total_price_tax_excl AS 'Revenue Net',
    br.total_tax AS 'Vat',
    br.tax_rate AS 'Vat Percentage',
    br.total_price_tax_incl AS 'Revenue Gross'
FROM bil_document b
LEFT JOIN bil_document_row br ON b.id = br.document_id
LEFT JOIN sal_order so ON b.order_id = so.id
LEFT JOIN sal_order_type t ON so.type_id = t.id
WHERE b.date >= '{start_date}' AND b.date <= '{end_date}' 
AND b.is_deleted = 0 AND br.is_deleted = 0
"""

import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore', UserWarning)
    df_main = pd.read_sql(query_main, connection)

if len(df_main) == 0:
    print("No data found!")
    sys.exit(0)

# Country mapping
country_map = {
    'Italia': 'Italy', 'Italie': 'Italy', 'Italien': 'Italy',
    'Francia': 'France', 'Frankreich': 'France',
    'Germania': 'Germany', 'Deutschland': 'Germany',
    'Spagna': 'Spain', 'España': 'Spain', 'Espana': 'Spain',
    'Svizzera': 'Switzerland', 'Schweiz': 'Switzerland', 'Suisse': 'Switzerland',
    'Austria': 'Austria', 'Osterreich': 'Austria', 'Österreich': 'Austria',
    'Belgio': 'Belgium', 'Belgique': 'Belgium', 'Belgien': 'Belgium'
}
df_main['Order Shipping Country'] = df_main['Order Shipping Country'].map(lambda x: country_map.get(x, x))

# Invert values for Credit Notes (2) and Refunds (4)
mask_negative = df_main['type_id'].isin([2, 4])
df_main.loc[mask_negative, 'Revenue Net'] *= -1
df_main.loc[mask_negative, 'Vat'] *= -1
df_main.loc[mask_negative, 'Revenue Gross'] *= -1

# Drop internal columns for the output
df_out = df_main.drop(columns=['id', 'type_id', 'related_id'])

# Prepare Credit Notes sheet
query_cn = f"""
SELECT 
    b.full_number AS 'Credit Note Number',
    b.date AS 'Credit Note Date',
    b.related_id,
    b.total AS 'Refund Amount'
FROM bil_document b
WHERE b.type_id IN (2, 4) AND b.date >= '{start_date}' AND b.date <= '{end_date}' AND b.is_deleted = 0
"""
with warnings.catch_warnings():
    warnings.simplefilter('ignore', UserWarning)
    df_cn = pd.read_sql(query_cn, connection)

if len(df_cn) > 0 and pd.notnull(df_cn['related_id']).any():
    rel_ids = tuple(int(x) for x in df_cn['related_id'].dropna().unique())
    if len(rel_ids) == 1:
        rel_ids_str = f"({rel_ids[0]})"
    else:
        rel_ids_str = str(rel_ids)
    
    query_orig = f"""
    SELECT 
        id,
        full_number AS 'Original Invoice Number',
        date AS 'Original Invoice Date',
        total AS 'Original Gross',
        total_refunded AS 'Total Refunded'
    FROM bil_document
    WHERE id IN {rel_ids_str}
    """
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        df_orig = pd.read_sql(query_orig, connection)
    
    df_cn = df_cn.merge(df_orig, left_on='related_id', right_on='id', how='left')
    df_cn = df_cn.drop(columns=['related_id', 'id'])
else:
    df_cn = pd.DataFrame(columns=['Credit Note Number', 'Credit Note Date', 'Refund Amount', 'Original Invoice Number', 'Original Invoice Date', 'Original Gross', 'Total Refunded', 'Residual Document Value'])

file_name = f'Report_Revenue_{start_date.replace("-","")}_to_{end_date.replace("-","")}.xlsx'
file_path = f'/tmp/{file_name}'
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    df_out.to_excel(writer, sheet_name='Database Unico (Per Pivot)', index=False)
    
    # Sheet name based on start_date month
    month_str = start_date.replace("-", "")[:6]
    df_out.to_excel(writer, sheet_name=month_str, index=False)
    
    if len(df_cn) > 0:
        if 'Residual Document Value' not in df_cn.columns:
            df_cn['Residual Document Value'] = ''
        df_cn.to_excel(writer, sheet_name='Note Credito', index=False)
        worksheet = writer.sheets['Note Credito']
        # Add formula: =Original Gross - Total Refunded
        orig_gross_col = df_cn.columns.get_loc('Original Gross') + 1
        tot_ref_col = df_cn.columns.get_loc('Total Refunded') + 1
        res_val_col = df_cn.columns.get_loc('Residual Document Value') + 1
        
        for row in range(2, len(df_cn) + 2):
            orig_gross_cell = worksheet.cell(row=row, column=orig_gross_col).coordinate
            tot_ref_cell = worksheet.cell(row=row, column=tot_ref_col).coordinate
            worksheet.cell(row=row, column=res_val_col).value = f"={orig_gross_cell}-{tot_ref_cell}"
    else:
        df_cn.to_excel(writer, sheet_name='Note Credito', index=False)

connection.close()

# Send email
subject = f"{month_str} - Report_Revenue from {start_date.replace('-', '')} to {end_date.replace('-', '')}"
body = "In allegato quanto in oggetto.\n\nJohn Finance 📊"
body_path = "/tmp/body_report_rev.txt"
with open(body_path, "w") as f:
    f.write(body)

cmd = [
    "gog", "gmail", "send",
    "--to", "mario.spina@produceshop.com",
    "--subject", subject,
    "--body-file", body_path,
    "--attach", file_path,
    "--no-input"
]
env = os.environ.copy()
env["GOG_KEYRING_PASSWORD"] = "produceshop"
env["GOG_ACCOUNT"] = "admin@produceshoptech.com"
subprocess.run(cmd, env=env)

print(f"Sent successfully to Mario! File: {file_path}")
