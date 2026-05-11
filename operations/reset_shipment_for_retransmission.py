import mysql.connector
import sys

# Database configuration
db_config = {
    "host": "34.38.166.212",
    "user": "john",
    "password": "3rmiCyf6d~MZDO41",
    "database": "kanguro"
}

def reset_shipment(shipment_number):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check current status
        check_query = "SELECT id, state_id, sent_to_logistics FROM lgs_shipment WHERE number = %s"
        cursor.execute(check_query, (shipment_number,))
        result = cursor.fetchone()
        
        if not result:
            print(f"Error: Shipment {shipment_number} not found.")
            return

        shipment_id, current_state, current_sent = result
        print(f"Current Status for {shipment_number}: State={current_state}, Sent={current_sent}")

        # Update query
        update_query = """
            UPDATE lgs_shipment 
            SET sent_to_logistics = 0, 
                transmission_date = NULL, 
                state_id = '10' 
            WHERE number = %s
        """
        cursor.execute(update_query, (shipment_number,))
        conn.commit()
        
        print(f"Success: Shipment {shipment_number} (ID: {shipment_id}) has been reset to state '10' for retransmission.")
        
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 reset_shipment_for_retransmission.py [shipment_number]")
    else:
        reset_shipment(sys.argv[1])
