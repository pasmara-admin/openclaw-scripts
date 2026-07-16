import mysql.connector
import pandas as pd
from datetime import datetime

# Database connection details
config = {
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'host': '34.38.166.212',
    'database': 'kanguro'
}

def get_data():
    conn = mysql.connector.connect(**config)
    
    query = """
    SELECT 
        ls.number AS numero_spedizione,
        lw.number AS numero_lettera_vettura,
        lw.creation_time AS creation_time,
        ls.order_number AS numero_ordine,
        lc.name AS nome_corriere,
        lt.number AS tracking_number,
        sosl.name AS stato_ordine,
        lssl.name AS stato_spedizione,
        so.date AS data_ordine,
        ls.transmission_date AS data_invio_logistica,
        iw.name AS magazzino
    FROM lgs_waybill lw
    JOIN lgs_shipment ls ON lw.shipment_number = ls.number
    LEFT JOIN lgs_carrier lc ON lw.carrier_id = lc.id
    LEFT JOIN lgs_tracking lt ON ls.tracking_id = lt.id
    LEFT JOIN sal_order so ON ls.order_id = so.id
    LEFT JOIN sal_order_state_lang sosl ON so.state_id = sosl.state_id AND sosl.lang_id = 1
    LEFT JOIN lgs_shipment_state_lang lssl ON ls.state_id = lssl.state_id AND lssl.lang_id = 1
    LEFT JOIN inv_warehouse iw ON ls.warehouse_id = iw.id
    WHERE lw.creation_time >= '2025-10-01'
      AND ls.warehouse_id IN (3, 4, 38)
      AND lw.is_deleted = 0
      AND ls.is_deleted = 0
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

if __name__ == "__main__":
    try:
        df = get_data()
        if not df.empty:
            output_path_xlsx = "/root/.openclaw/workspace-marketing/ritorni_save_2025.xlsx"
            output_path_csv = "/root/.openclaw/workspace-marketing/ritorni_save_2025.csv"
            df.to_excel(output_path_xlsx, index=False)
            df.to_csv(output_path_csv, index=False, sep=';', encoding='utf-8-sig')
            print(f"SUCCESS: Reports generated at {output_path_xlsx} and {output_path_csv}")
            print(f"Rows found: {len(df)}")
        else:
            print("No data found for the given criteria.")
    except Exception as e:
        print(f"ERROR: {e}")
