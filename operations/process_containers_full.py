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
        
        mapping = {}
        for pf in proforma_list:
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
                descriptions = list(set([row['description'] for row in rows if row['description']]))
                if not descriptions:
                    descriptions = list(set([row['reference'] for row in rows if row['reference']]))
                mapping[pf] = ", ".join(descriptions[:3])
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
    
    col_proforma = 'Proforma'
    col_arrival = 'Data prevista arrivo in porto'
    
    # Copy all rows
    df_result = df.copy()
    
    # Temporary datetime column for sorting (NaT will go to the end)
    df_result['arrival_dt'] = pd.to_datetime(df_result[col_arrival], errors='coerce', dayfirst=True)
    
    # Sort: populated dates first (chronological), then NaT
    df_result = df_result.sort_values(by='arrival_dt', na_position='last')
    
    # Get mapping for all proformas
    proformas = df_result[col_proforma].unique().tolist()
    product_mapping = get_product_info(proformas)
    
    # Add Tipologia Merce column
    df_result['Tipologia Merce'] = df_result[col_proforma].map(product_mapping)
    
    # Format dates back for the final file
    # We keep the original string if it was there but not parsable, 
    # or use the formatted one if it was parsable.
    # To be safe, we only format the ones that are valid datetimes.
    mask = df_result['arrival_dt'].notna()
    df_result.loc[mask, col_arrival] = df_result.loc[mask, 'arrival_dt'].dt.strftime('%d/%m/%Y')
    
    # Drop temp column
    df_result = df_result.drop(columns=['arrival_dt'])
    
    output_file = 'Monitoraggio_Container_Completo_Tipologia.xlsx'
    df_result.to_excel(output_file, index=False)
    print(f"SUCCESS:{output_file}")

if __name__ == "__main__":
    main()
