import pandas as pd
import sys
import os
import json
from datetime import datetime, timedelta
import mysql.connector

# Configuration - should be loaded from env or config file in real production
DB_CONFIG = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def check_invoice(supplier_id, skus_data, period_days=7, start_date=None, end_date=None):
    """
    skus_data: list of dicts {'sku': '...', 'invoice_price': float, 'qty': int}
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    results = []
    
    # 1. Get latest price list for supplier
    cursor.execute("""
        SELECT id FROM pch_price_list 
        WHERE supplier_id = %s AND is_deleted = 0 
        ORDER BY date DESC LIMIT 1
    """, (supplier_id,))
    price_list = cursor.fetchone()
    list_id = price_list['id'] if price_list else None
    
    # 2. Define period for sales check
    if not start_date:
        end_dt = datetime.now() if not end_date else datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=period_days)
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')

    for item in skus_data:
        sku = item['sku']
        inv_price = item['invoice_price']
        inv_qty = item['qty']
        
        # Get product ID and list price
        list_price = None
        if list_id:
            query = """
                SELECT pld.net_price, p.id as product_id
                FROM pch_price_list_detail pld
                JOIN dat_product p ON pld.product_id = p.id
                WHERE pld.list_id = %s AND p.reference = %s AND pld.is_deleted = 0
            """
            cursor.execute(query, (list_id, sku))
            price_row = cursor.fetchone()
            if price_row:
                list_price = float(price_row['net_price'])
                product_id = price_row['product_id']
            else:
                # Try finding product without list price
                cursor.execute("SELECT id FROM dat_product WHERE reference = %s", (sku,))
                p_row = cursor.fetchone()
                product_id = p_row['id'] if p_row else None
        else:
            cursor.execute("SELECT id FROM dat_product WHERE reference = %s", (sku,))
            p_row = cursor.fetchone()
            product_id = p_row['id'] if p_row else None

        # Get sales in period
        sales_qty = 0
        if product_id:
            cursor.execute("""
                SELECT SUM(sor.qty) as total_sold
                FROM sal_order_row sor
                JOIN sal_order so ON sor.order_id = so.id
                WHERE sor.product_id = %s 
                  AND so.date BETWEEN %s AND %s
                  AND so.is_deleted = 0 AND sor.is_deleted = 0
            """, (product_id, start_date, end_date))
            sales_row = cursor.fetchone()
            sales_qty = float(sales_row['total_sold']) if sales_row and sales_row['total_sold'] else 0

        results.append({
            'SKU': sku,
            'Prezzo Fattura': inv_price,
            'Prezzo Listino': list_price,
            'Diff. Prezzo': (inv_price - list_price) if list_price is not None else "N/D",
            'Qty Fattura': inv_qty,
            'Qty Venduta': sales_qty,
            'Periodo Check': f"{start_date} - {end_date}"
        })

    cursor.close()
    conn.close()
    return pd.DataFrame(results)

if __name__ == "__main__":
    # This script is designed to be called with a JSON input of extracted data
    # Usage: python check-fattura.py '<json_data>'
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            supplier_id = data.get('supplier_id')
            skus = data.get('skus', [])
            start = data.get('start_date')
            end = data.get('end_date')
            
            df = check_invoice(supplier_id, skus, start_date=start, end_date=end)
            
            output_file = f"check_fattura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(output_file, index=False)
            print(f"SUCCESS:{output_file}")
        except Exception as e:
            print(f"ERROR:{str(e)}")
    else:
        print("Usage: python check-fattura.py '<json_data>'")
