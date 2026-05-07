import pandas as pd
import pymysql
import os
import re
from datetime import datetime

# Database connection
def get_connection():
    return pymysql.connect(
        host='34.38.166.212',
        user='john',
        password='3rmiCyf6d~MZDO41',
        database='kanguro'
    )

def identify_categories(df):
    """Identify RAEE categories based on name and dimensions."""
    # Ensure dimensions are numeric
    for col in ['long_side', 'short_side', 'height']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['max_side'] = df[['long_side', 'short_side', 'height']].max(axis=1)
    
    def classify(row):
        name = str(row['name']).lower()
        max_dim = row['max_side']
        
        # 1. Air-conditioners, heat pumps, dehumidifiers
        if re.search(r'(climatizzatore|condizionatore|pompa di calore|deumidificatore|clima|fancoil)', name):
            return "1. Apparecchiature per lo scambio di temperatura"
        
        # 2. Large lighting equipment > 50 cm
        if re.search(r'(lampada|lampadario|applique|plafoniera|faretto|illuminazione|lanterna)', name) and max_dim > 50:
            return "2. Apparecchiature di illuminazione (> 50 cm)"
        
        # 3. Large equipment > 50 cm (Stoves, heating, etc.)
        if re.search(r'(stufa|radiatore|caldaia|forno|lavatrice|asciugatrice|lavastoviglie|frigorifero|congelatore|cucina)', name) and max_dim > 50:
            return "3. Grandi apparecchiature (> 50 cm)"
        
        # 4. Body-care appliances < 50 cm
        if re.search(r'(asciugacapelli|rasoio|epilatore|tagliacapelli|piastra|spazzolino|massaggiatore|manicure|pedicure)', name) and max_dim <= 50:
            return "4. Apparecchiature di piccole dimensioni per la cura del corpo (< 50 cm)"
        
        # 5. Small equipment < 50 cm (Stoves, fryers, blenders, etc.)
        if re.search(r'(frullatore|friggitrice|mixer|tostapane|bollitore|macchina caffè|ferro da stiro|aspirapolvere|centrifuga|microonde|sandwich|waffle|griglia|frusta|stufetta)', name) and max_dim <= 50:
            return "5. Piccole apparecchiature (< 50 cm)"
        
        # 6. Lithium accumulators - Portable
        if re.search(r'(lithium|li-ion|li-po|power bank|batteria portatile|accumulatore)', name):
            return "6. Piccoli accumulatori portatili al litio"
            
        return "Altro / Non RAEE"

    df['RAEE_Category'] = df.apply(classify, axis=1)
    return df

def main():
    conn = get_connection()
    
    print("Fetching active products...")
    # Get only active products
    query_products = """
    SELECT id, reference, name, long_side, short_side, height, unit_weight_g 
    FROM dat_product 
    WHERE is_active = b'1' AND is_deleted = b'0'
    """
    df_products = pd.read_sql(query_products, conn)
    
    print("Identifying categories...")
    df_products = identify_categories(df_products)
    
    # Filter only RAEE products
    df_raee = df_products[df_products['RAEE_Category'] != "Altro / Non RAEE"].copy()
    
    if df_raee.empty:
        print("No RAEE products found with current logic.")
        conn.close()
        return

    print(f"Found {len(df_raee)} RAEE products. Fetching sales data for 2026...")
    
    # Fetch sales (Order rows) for 2026
    # Note: excluding cancelled orders (state_id != '10' usually, but let's check common active states)
    # Kanguro states: '01' New, '02' Validated, '03' Processing, '04' Ready, '05' Shipped, '06' Delivered, '09' Cancelled, '10' To Invoice
    query_sales = """
    SELECT 
        sor.product_id,
        SUM(sor.qty) as total_qty,
        SUM(sor.total_price) as total_value
    FROM sal_order_row sor
    JOIN sal_order so ON sor.order_id = so.id
    WHERE so.date >= '2026-01-01' 
      AND so.state_id NOT IN ('09') -- Excluding Cancelled
      AND sor.is_deleted = b'0'
      AND so.is_deleted = b'0'
    GROUP BY sor.product_id
    """
    df_sales = pd.read_sql(query_sales, conn)
    
    print("Fetching refunds data for 2026...")
    # In Kanguro, refunds can be seen in total_refunded in sal_order, 
    # but for per-product net sales, we should ideally look at Credit Notes (bil_document) 
    # and their rows, or sal_order_row linked to credit notes.
    # Simplified: looking for 'Credit Note' documents in 2026
    query_refunds = """
    SELECT 
        bdr.product_id,
        SUM(bdr.qty) as refund_qty,
        SUM(bdr.total_price_tax_excl) as refund_value
    FROM bil_document_row bdr
    JOIN bil_document bd ON bdr.document_id = bd.id
    WHERE bd.date >= '2026-01-01' 
      AND bd.type_id IN (2, 4) -- 2 = Credit Note, 4 = Receipt Refund?
      AND bd.is_deleted = 0
      AND bdr.is_deleted = 0
    GROUP BY bdr.product_id
    """
    df_refunds = pd.read_sql(query_refunds, conn)
    
    conn.close()
    
    # Merge data
    df_final = df_raee.merge(df_sales, left_on='id', right_on='product_id', how='left')
    df_final = df_final.merge(df_refunds, left_on='id', right_on='product_id', how='left', suffixes=('_s', '_r'))
    
    # Clean and calculate net
    df_final['total_qty'] = df_final['total_qty'].fillna(0)
    df_final['total_value'] = df_final['total_value'].fillna(0)
    df_final['refund_qty'] = df_final['refund_qty'].fillna(0)
    df_final['refund_value'] = df_final['refund_value'].fillna(0)
    
    df_final['Pezzi Venduti Netto'] = df_final['total_qty'] - df_final['refund_qty']
    df_final['Valore Venduto Netto'] = df_final['total_value'] - df_final['refund_value']
    
    # Convert weight to kg
    df_final['Peso (kg)'] = df_final['unit_weight_g'].fillna(0) / 1000
    
    # Final cleanup for Export
    export_cols = [
        'RAEE_Category', 'reference', 'name', 
        'Pezzi Venduti Netto', 'Valore Venduto Netto', 'Peso (kg)'
    ]
    df_export = df_final[export_cols].sort_values(['RAEE_Category', 'Valore Venduto Netto'], ascending=[True, False])
    
    # Rename columns for clarity
    df_export.columns = [
        'Categoria RAEE', 'SKU', 'Prodotto', 
        'Pezzi Venduti (Netto)', 'Valore Venduto (Netto €)', 'Peso Unitario (kg)'
    ]
    
    out_file = '/root/.openclaw/workspace-finance/Analisi_RAEE_Vendite_2026.xlsx'
    df_export.to_excel(out_file, index=False)
    print(f"File saved: {out_file}")

if __name__ == "__main__":
    main()
