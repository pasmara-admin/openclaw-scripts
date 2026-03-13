import sys
import mysql.connector
import pandas as pd
from datetime import datetime
import os

def get_prestashop_conn():
    return mysql.connector.connect(
        host="62.84.190.199",
        user="john",
        password="qARa6aRozi6I",
        database="produceshop"
    )

def get_kanguro_conn():
    return mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )

def query_sku(sku):
    result = {
        'SKU': sku,
        'Stock Prestashop (id_shop=1)': 0,
        'Vendite dal 01/10/2025': 0,
        'Prezzo di vendita Italia': 0.0,
        'Purchase Price': 'N/A'
    }

    # 1. Prestashop Data (Stock & Price)
    try:
        ps_conn = get_prestashop_conn()
        ps_cursor = ps_conn.cursor(dictionary=True)
        
        # Stock
        ps_cursor.execute("""
            SELECT SUM(sa.quantity) as stock 
            FROM ps_stock_available sa 
            JOIN ps_product p ON sa.id_product = p.id_product 
            LEFT JOIN ps_product_attribute pa ON sa.id_product_attribute = pa.id_product_attribute 
            WHERE (p.reference = %s OR pa.reference = %s) AND sa.id_shop = 1
        """, (sku, sku))
        stock_row = ps_cursor.fetchone()
        if stock_row and stock_row['stock'] is not None:
            result['Stock Prestashop (id_shop=1)'] = int(stock_row['stock'])
            
        # Price
        ps_cursor.execute("""
            SELECT p.price AS base_price, pa.price AS attr_price, sp.reduction, sp.reduction_type
            FROM ps_product p 
            LEFT JOIN ps_product_attribute pa ON (p.id_product = pa.id_product AND pa.reference = %s)
            LEFT JOIN ps_specific_price sp ON (p.id_product = sp.id_product AND sp.id_shop = 1 AND (sp.id_product_attribute = IFNULL(pa.id_product_attribute, 0) OR sp.id_product_attribute = 0))
            WHERE p.reference = %s OR pa.reference = %s
            ORDER BY sp.id_specific_price DESC LIMIT 1
        """, (sku, sku, sku))
        price_row = ps_cursor.fetchone()
        if price_row:
            base = float(price_row['base_price'] or 0)
            attr = float(price_row['attr_price'] or 0)
            red = float(price_row['reduction'] or 0)
            
            final_price = base + attr - red
            result['Prezzo di vendita Italia'] = round(final_price, 2)
            
        ps_conn.close()
    except Exception as e:
        print(f"Error Prestashop for {sku}: {e}")

    # 2. Kanguro Data (Sales & Purchase Price)
    try:
        kg_conn = get_kanguro_conn()
        kg_cursor = kg_conn.cursor(dictionary=True)
        
        # Sales since Oct 1 2025
        kg_cursor.execute("""
            SELECT SUM(r.qty) as sales 
            FROM sal_order_row r 
            JOIN sal_order o ON r.order_id = o.id 
            WHERE r.reference = %s AND o.date >= '2025-10-01'
        """, (sku,))
        sales_row = kg_cursor.fetchone()
        if sales_row and sales_row['sales'] is not None:
            result['Vendite dal 01/10/2025'] = int(sales_row['sales'])
            
        # Purchase Price
        kg_cursor.execute("""
            SELECT r.price_fob, o.currency_iso_code 
            FROM pch_order_row r 
            JOIN pch_order o ON r.order_id = o.id 
            WHERE r.reference = %s 
            ORDER BY o.date DESC LIMIT 1
        """, (sku,))
        pch_row = kg_cursor.fetchone()
        if pch_row:
            price_fob = float(pch_row['price_fob'])
            currency = pch_row['currency_iso_code']
            result['Purchase Price'] = f"{price_fob:.2f} {currency}"
            
        kg_conn.close()
    except Exception as e:
        print(f"Error Kanguro for {sku}: {e}")

    return result

if __name__ == '__main__':
    skus = sys.argv[1:]
    if not skus:
        print("Usage: python3 analisi-sku.py SKU1 SKU2 ...")
        sys.exit(1)
        
    data = []
    for sku in skus:
        print(f"Analyzing {sku}...")
        data.append(query_sku(sku))
        
    df = pd.DataFrame(data)
    out_file = "/root/.openclaw/workspace-buyer/analisi_sku_output.xlsx"
    df.to_excel(out_file, index=False)
    print(f"Saved to {out_file}")
