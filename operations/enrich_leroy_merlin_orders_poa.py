import pandas as pd
import mysql.connector
import sys
import os
import subprocess

# Database configuration
db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def process_file(input_path, output_path, email_recipient=None):
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
    
    # Query updated with order date and shipping status
    query = f"""
    SELECT 
        o.external_reference as order_id,
        o.date as order_date,
        o.total as order_total,
        o.total_refunded as total_refunded,
        s.number as shipment_number,
        t.number as tracking_number,
        w.name as warehouse_name,
        GROUP_CONCAT(DISTINCT s.product_reference SEPARATOR '; ') as products,
        ss.name as shipping_status,
        (
            SELECT GROUP_CONCAT(DISTINCT rs.name SEPARATOR '; ')
            FROM ret_shipping rsh
            JOIN ret_return rr ON rsh.id = rr.shipping_id
            JOIN ret_return_state_lang rs ON rr.return_state_id = rs.return_state_id AND rs.lang_id = 1
            WHERE rsh.order_id = o.id AND rr.is_deleted = 0
        ) as post_sales_return_status
    FROM sal_order o
    LEFT JOIN lgs_shipment s ON o.id = s.order_id
    LEFT JOIN lgs_tracking t ON s.tracking_id = t.id
    LEFT JOIN inv_warehouse w ON s.warehouse_id = w.id
    LEFT JOIN sal_order_shipping_state_lang ss ON o.shipping_state_id = ss.shipping_state_id AND ss.lang_id = 1
    WHERE o.external_reference IN ({format_strings})
    GROUP BY o.id, o.external_reference, o.date, o.total, o.total_refunded, s.number, t.number, w.name, ss.name
    """
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, tuple(order_ids))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    df_db = pd.DataFrame(rows)
    
    if df_db.empty:
        print("Nessuna corrispondenza trovata nel database.")
        df_output = df_input
    else:
        # Merge results back to original dataframe
        df_output = pd.merge(df_input, df_db, on='order_id', how='left')
    
    # Financial and Refund Calculations
    def calc_refund_type(row):
        total = float(row['order_total']) if pd.notnull(row['order_total']) else 0
        refunded = float(row['total_refunded']) if pd.notnull(row['total_refunded']) else 0
        if refunded <= 0:
            return "NESSUNO"
        if abs(refunded - total) < 0.01:
            return "TOTALE"
        return "PARZIALE"

    def calc_refund_percentage(row):
        total = float(row['order_total']) if pd.notnull(row['order_total']) else 0
        refunded = float(row['total_refunded']) if pd.notnull(row['total_refunded']) else 0
        if total <= 0:
            return "0%"
        pct = (refunded / total) * 100
        return f"{round(pct, 2)}%"

    df_output['Tipo Nota Credito'] = df_output.apply(calc_refund_type, axis=1)
    df_output['% Rimborso'] = df_output.apply(calc_refund_percentage, axis=1)
    
    # Combined Post-Sales Status: returns + shipping state
    def combine_status(row):
        ret_status = row['post_sales_return_status'] if pd.notnull(row['post_sales_return_status']) else ""
        ship_status = row['shipping_status'] if pd.notnull(row['shipping_status']) else ""
        if ret_status:
            return f"{ship_status} / Reso: {ret_status}"
        return ship_status

    df_output['Stato Post-Sales'] = df_output.apply(combine_status, axis=1)
    
    # Rename columns to user requested names
    column_mapping = {
        'order_date': 'Data Ordine',
        'shipment_number': 'Numero Spedizione',
        'tracking_number': 'Numero Tracking',
        'warehouse_name': 'Magazzino',
        'products': 'Prodotti',
        'order_total': 'Importo Ordine'
    }
    df_output = df_output.rename(columns=column_mapping)
    
    # Drop internal helper columns
    cols_to_drop = ['total_refunded', 'post_sales_return_status', 'shipping_status']
    for col in cols_to_drop:
        if col in df_output.columns:
            df_output = df_output.drop(columns=[col])
    
    # Save to Excel
    df_output.to_excel(output_path, index=False)
    print(f"File salvato in: {output_path}")

    if email_recipient:
        send_email(output_path, email_recipient)

def send_email(file_path, recipient):
    subject = "Dettagli ordini Leroy Merlin per PoA - Report Aggiornato v3"
    body = "Ciao Ivan,\n\nIn allegato trovi il report 'Dettagli ordini Leroy Merlin per PoA' aggiornato con:\n1. Data dell'ordine\n2. Stato Post-Sales completo (Stato spedizione + dettaglio Reso/RMA)\n3. Tutte le altre colonne finanziarie richieste.\n\nUn saluto,\nJohn Operations"
    
    env = os.environ.copy()
    env["GOG_KEYRING_PASSWORD"] = "produceshop"
    env["GOG_ACCOUNT"] = "admin@produceshoptech.com"

    cmd = [
        'gog', 'gmail', 'send',
        '--to', recipient,
        '--subject', subject,
        '--body', body,
        '--attach', file_path
    ]
    subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(f"Email inviata a {recipient}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Utilizzo: python3 script.py <input_xlsx> <output_xlsx> [email]")
    else:
        email = sys.argv[3] if len(sys.argv) > 3 else None
        process_file(sys.argv[1], sys.argv[2], email)
