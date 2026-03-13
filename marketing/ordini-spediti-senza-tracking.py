import mysql.connector
import pandas as pd

def main():
    conn = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor = conn.cursor(dictionary=True)
    
    # State 19 = Spedita
    query = """
        SELECT DISTINCT s.number as `Numero Ordine`
        FROM sal_order s 
        JOIN lgs_shipment l ON s.id = l.order_id 
        WHERE l.state_id = '19' 
          AND l.tracking_id IS NULL 
          AND s.is_deleted = 0 
          AND s.date >= CURDATE() - INTERVAL 14 DAY
          AND s.date < CURDATE()
        ORDER BY s.date DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(data)
    out_path = "/root/.openclaw/workspace-marketing/Ordini_Senza_Tracking.xlsx"
    df.to_excel(out_path, index=False)
    print(f"File salvato: {out_path} con {len(data)} ordini.")

if __name__ == "__main__":
    main()
