#!/usr/bin/env python3
import sys
import mysql.connector

# Database connection details
DB_CONFIG = {
    'host': '62.84.190.199',
    'user': 'john',
    'password': 'qARa6aRozi6I',
    'database': 'produceshop',
    'raise_on_warnings': True
}

def get_delivery_estimate(order_reference=None, id_order=None):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if order_reference:
            query = "SELECT id_order FROM ps_orders WHERE reference = %s"
            cursor.execute(query, (order_reference,))
            res = cursor.fetchone()
            if not res:
                return f"Order reference {order_reference} not found."
            id_order = res['id_order']
        
        if not id_order:
            return "Please provide an Order Reference or ID."

        # Fetch details from ps_order_delivery_date_stamp
        query = """
            SELECT 
                ds.id_order,
                ds.id_order_detail,
                od.product_name,
                od.product_reference,
                ds.delivery_date,
                ds.delivery_type,
                ds.date_add AS stamp_recorded_at
            FROM ps_order_delivery_date_stamp ds
            JOIN ps_order_detail od ON ds.id_order_detail = od.id_order_detail
            WHERE ds.id_order = %s
        """
        cursor.execute(query, (id_order,))
        rows = cursor.fetchall()

        if not rows:
            return f"No delivery stamp found for Order ID {id_order}."

        output = []
        for row in rows:
            output.append(f"Product: {row['product_name']} (SKU: {row['product_reference']})")
            output.append(f"Estimated Delivery: {row['delivery_date']}")
            output.append(f"Recorded At: {row['stamp_recorded_at']} (Type: {row['delivery_type']})")
            output.append("-" * 20)
        
        return "\n".join(output)

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 get_order_delivery_estimate.py <order_reference_or_id>")
        sys.exit(1)
    
    param = sys.argv[1]
    if param.isdigit() and len(param) < 9: # Simple check for ID vs Reference
        print(get_delivery_estimate(id_order=int(param)))
    else:
        print(get_delivery_estimate(order_reference=param))
