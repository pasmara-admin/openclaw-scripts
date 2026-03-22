import mysql.connector
import csv
import os
from datetime import datetime

# Database connection details
DB_CONFIG = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def run_report():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            so.number AS 'Ordine', 
            so.date AS 'Data Ordine', 
            rs.rma AS 'RMA', 
            rsl.name AS 'Stato RMA', 
            DATE_FORMAT(rr.creation_time, '%Y-%m-%d %H:%i') AS 'Data Conferma RMA' 
        FROM ret_return rr 
        JOIN ret_shipping rs ON rr.shipping_id = rs.id 
        JOIN sal_order so ON rs.order_id = so.id 
        JOIN ret_return_state_lang rsl ON rr.return_state_id = rsl.return_state_id AND rsl.lang_id = 1 
        WHERE rr.return_state_id IN ('80', '90') 
          AND rr.is_deleted = 0 
          AND rs.is_deleted = 0 
          AND rs.order_id IS NOT NULL 
          AND rr.creation_time >= '2026-02-01' 
          AND NOT EXISTS (
              SELECT 1 FROM bil_document bd 
              WHERE bd.order_id = rs.order_id 
                AND bd.type_id IN (2, 4) 
                AND bd.is_deleted = 0
          ) 
        ORDER BY rr.creation_time DESC;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            filename = 'report_resi_senza_nota.csv'
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            print(f"Report generato con successo: {filename}")
        else:
            print("Nessun dato trovato per i criteri specificati.")

    except Exception as e:
        print(f"Errore durante l'esecuzione dello script: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_report()
