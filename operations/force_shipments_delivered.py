import mysql.connector
import sys

# Database configuration
db_config = {
    "host": "34.38.166.212",
    "user": "john",
    "password": "3rmiCyf6d~MZDO41",
    "database": "kanguro"
}

def force_delivered(shipment_numbers):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        for number in shipment_numbers:
            # 1. Fetch relevant rows to log history
            cursor.execute("SELECT id, state_id FROM lgs_shipment WHERE number = %s", (number,))
            rows = cursor.fetchall()
            
            if not rows:
                print(f"Warning: Shipment {number} not found.")
                continue
            
            print(f"Updating shipment {number} ({len(rows)} rows)...")
            
            # 2. Update status
            update_query = "UPDATE lgs_shipment SET state_id = '99' WHERE number = %s"
            cursor.execute(update_query, (number,))
            
            # 3. Log history for each shipment ID
            for shipment_id, old_state in rows:
                if old_state != '99':
                    history_query = """
                        INSERT INTO lgs_shipment_history (shipment_id, description, field_name, new_value, creation_time)
                        VALUES (%s, %s, %s, %s, NOW())
                    """
                    cursor.execute(history_query, (shipment_id, "Forzato a consegnato da John Operations su richiesta di Ivan", "state_id", "99"))
            
            conn.commit()
            print(f"Shipment {number} successfully set to Delivered (99).")
            
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 force_shipments_delivered.py [number1] [number2] ...")
    else:
        force_delivered(sys.argv[1:])
