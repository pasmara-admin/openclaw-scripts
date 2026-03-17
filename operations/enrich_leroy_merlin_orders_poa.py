import pandas as pd
import mysql.connector
import sys

# Database configuration
db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def process_file(input_path, output_path):
    # Load the input Excel file
    df_input = pd.read_excel(input_path)
    
    # Ensure order_id is string and strip whitespace
    df_input['order_id'] = df_input['order_id'].astype(str).str.strip()
    order_ids = df_input['order_id'].unique().tolist()
    
    if not order_ids:
        print("Nessun order_id trovato nel file.")
        return

    # Connect to database
    conn = mysql.connector.connect(**db_config)
    
    # Prepare placeholders for IN clause
    format_strings = ','.join(['%s'] * len(order_ids))
    
    # Query to fetch shipment and tracking info
    # We use GROUP_CONCAT to handle multiple products in a single shipment
    query = f"""
    SELECT 
        o.external_reference as order_id,
        s.number as shipment_number,
        t.number as tracking_number,
        w.name as warehouse_name,
        GROUP_CONCAT(DISTINCT s.product_reference SEPARATOR '; ') as products
    FROM sal_order o
    JOIN lgs_shipment s ON o.id = s.order_id
    LEFT JOIN lgs_tracking t ON s.tracking_id = t.id
    LEFT JOIN inv_warehouse w ON s.warehouse_id = w.id
    WHERE o.external_reference IN ({format_strings})
    GROUP BY o.external_reference, s.number, t.number, w.name
    """
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, tuple(order_ids))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    df_db = pd.DataFrame(rows)
    
    if df_db.empty:
        print("Nessuna corrispondenza trovata nel database.")
        # Just add empty columns if no matches
        for col in ['shipment_number', 'tracking_number', 'warehouse_name', 'products']:
            df_input[col] = None
        df_output = df_input
    else:
        # Merge results back to original dataframe
        # If an order has multiple shipments, this might create multiple rows in output
        df_output = pd.merge(df_input, df_db, on='order_id', how='left')
    
    # Rename columns to user requested names
    column_mapping = {
        'shipment_number': 'Numero Spedizione',
        'tracking_number': 'Numero Tracking',
        'warehouse_name': 'Magazzino',
        'products': 'Prodotti'
    }
    df_output = df_output.rename(columns=column_mapping)
    
    # Save to Excel
    df_output.to_excel(output_path, index=False)
    print(f"File salvato in: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Utilizzo: python3 script.py <input_xlsx> <output_xlsx>")
    else:
        process_file(sys.argv[1], sys.argv[2])
