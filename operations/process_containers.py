import pandas as pd
import mysql.connector
import sys
from datetime import datetime

# Database config
db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_product_info(proforma_list):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # We'll build a mapping: proforma -> list of descriptions
        mapping = {}
        for pf in proforma_list:
            # Try to match external_reference or number
            query = """
                SELECT r.description, r.reference 
                FROM pch_order o 
                JOIN pch_order_row r ON o.id = r.order_id 
                WHERE (o.external_reference = %s OR o.number = %s)
                AND o.is_deleted = 0 AND r.is_deleted = 0
            """
            cursor.execute(query, (pf, pf))
            rows = cursor.fetchall()
            if rows:
                # Deduplicate and join first few descriptions or references
                descriptions = list(set([row['description'] for row in rows if row['description']]))
                if not descriptions:
                    descriptions = list(set([row['reference'] for row in rows if row['reference']]))
                mapping[pf] = ", ".join(descriptions[:3]) # Limit to 3 items
            else:
                mapping[pf] = "N/A"
        
        cursor.close()
        conn.close()
        return mapping
    except Exception as e:
        print(f"DB Error: {e}")
        return {pf: f"Error: {e}" for pf in proforma_list}

def main():
    file_path = '/root/.openclaw/media/inbound/Monitoraggio_Container---febc7e3b-5230-4ed3-bae4-623290376ef1.xlsx'
    df = pd.read_excel(file_path)
    
    # Column names based on inspection
    col_proforma = 'Proforma'
    col_arrival = 'Data prevista arrivo in porto'
    
    # Filter rows with arrival date
    # Some dates might be strings or NaN
    df_filtered = df.dropna(subset=[col_arrival]).copy()
    
    # Try to convert to datetime for sorting
    df_filtered[col_arrival] = pd.to_datetime(df_filtered[col_arrival], errors='coerce', dayfirst=True)
    df_filtered = df_filtered.dropna(subset=[col_arrival])
    
    # Sort by arrival date
    df_filtered = df_filtered.sort_values(by=col_arrival)
    
    # Get unique proformas for DB query
    proformas = df_filtered[col_proforma].unique().tolist()
    product_mapping = get_product_info(proformas)
    
    # Add Tipologia Merce column
    df_filtered['Tipologia Merce'] = df_filtered[col_proforma].map(product_mapping)
    
    # Format dates back to string for readability in Excel
    df_filtered[col_arrival] = df_filtered[col_arrival].dt.strftime('%d/%m/%Y')
    
    # Save to new Excel
    output_file = 'Container_Arrivo_Porto_Tipologia.xlsx'
    df_filtered.to_excel(output_file, index=False)
    print(f"SUCCESS:{output_file}")

if __name__ == "__main__":
    main()
