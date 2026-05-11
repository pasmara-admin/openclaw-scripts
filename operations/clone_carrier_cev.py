import sys
import mysql.connector
import uuid
from datetime import datetime

# Configurazione DB
config = {
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'host': '34.38.166.212',
    'database': 'kanguro',
}

def clone_carrier_and_rate(source_carrier_id, source_rate_id, new_carrier_id, new_rate_name):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        print(f"Cloning {source_carrier_id} to {new_carrier_id}...")

        # 1. Recupera dati Carrier sorgente
        cursor.execute("SELECT * FROM lgs_carrier WHERE id = %s", (source_carrier_id,))
        source_carrier = cursor.fetchone()
        if not source_carrier:
            print(f"Error: Source carrier {source_carrier_id} not found.")
            return

        # 2. Crea nuovo Carrier
        new_carrier = source_carrier.copy()
        new_carrier['id'] = new_carrier_id
        new_carrier['name'] = 'CEV'
        new_carrier['display_name'] = 'CEV'
        new_carrier['concurrency_stamp'] = str(uuid.uuid4())
        
        cols = ", ".join(new_carrier.keys())
        placeholders = ", ".join(["%s"] * len(new_carrier))
        sql_carrier = f"INSERT INTO lgs_carrier ({cols}) VALUES ({placeholders})"
        cursor.execute(sql_carrier, list(new_carrier.values()))

        # 3. Recupera dati Rate sorgente
        cursor.execute("SELECT * FROM lgs_shipping_rate WHERE id = %s", (source_rate_id,))
        source_rate = cursor.fetchone()
        if not source_rate:
            print(f"Error: Source rate {source_rate_id} not found.")
            conn.rollback()
            return

        # 4. Crea nuova Rate
        new_rate = source_rate.copy()
        new_rate.pop('id') # Auto-increment
        new_rate['carrier_id'] = new_carrier_id
        new_rate['name'] = new_rate_name
        new_rate['description'] = f"Tariffa {new_rate_name} per {new_carrier_id}"
        new_rate['concurrency_stamp'] = str(uuid.uuid4())

        cols_rate = ", ".join(new_rate.keys())
        placeholders_rate = ", ".join(["%s"] * len(new_rate))
        sql_rate = f"INSERT INTO lgs_shipping_rate ({cols_rate}) VALUES ({placeholders_rate})"
        cursor.execute(sql_rate, list(new_rate.values()))
        new_rate_id = cursor.lastrowid
        print(f"New rate created with ID: {new_rate_id}")

        # 5. Clona lgs_shipping_rate_price
        cursor.execute("SELECT * FROM lgs_shipping_rate_price WHERE rate_id = %s", (source_rate_id,))
        prices = cursor.fetchall()
        for p in prices:
            p.pop('id')
            p['rate_id'] = new_rate_id
            p['carrier_id'] = new_carrier_id
            p['rate_name'] = new_rate_name
            p['concurrency_stamp'] = str(uuid.uuid4())
            
            cols_p = ", ".join(p.keys())
            placeholders_p = ", ".join(["%s"] * len(p))
            sql_p = f"INSERT INTO lgs_shipping_rate_price ({cols_p}) VALUES ({placeholders_p})"
            cursor.execute(sql_p, list(p.values()))
        
        print(f"Cloned {len(prices)} price entries.")

        # 6. Clona lgs_shipping_rate_country (anche se vuote per ITM/34, utile come logica generale)
        cursor.execute("SELECT * FROM lgs_shipping_rate_country WHERE rate_id = %s", (source_rate_id,))
        countries = cursor.fetchall()
        for c in countries:
            c.pop('id')
            c['rate_id'] = new_rate_id
            c['concurrency_stamp'] = str(uuid.uuid4())
            cols_c = ", ".join(c.keys())
            placeholders_c = ", ".join(["%s"] * len(c))
            cursor.execute(f"INSERT INTO lgs_shipping_rate_country ({cols_c}) VALUES ({placeholders_c})", list(c.values()))

        conn.commit()
        print("Done! Everything committed.")

    except Exception as e:
        print(f"Fatal Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    clone_carrier_and_rate('ITM', 34, 'CEV', 'ITA')
