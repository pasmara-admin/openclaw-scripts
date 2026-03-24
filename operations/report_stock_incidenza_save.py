import pandas as pd
import mysql.connector
import os
import sys

db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def generate_report(output_path):
    conn = mysql.connector.connect(**db_config)
    
    # Warehouses: Melzo (3), Roma (4), Viadana (38)
    # Country IT: 10
    
    query = """
    SELECT 
        p.reference as sku,
        w.name as warehouse,
        s.qty as quantity,
        kpi.sale_price as price_it,
        lc.total_price as transport_cost_it,
        IFNULL(sq.total_sold, 0) as historical_sold_qty
    FROM inv_inventory_stock s
    JOIN dat_product p ON s.product_id = p.id
    JOIN inv_warehouse w ON s.warehouse_id = w.id
    LEFT JOIN dat_product_kpi_shop kpi ON p.id = kpi.product_id AND kpi.shop_id = 1 AND kpi.is_deleted = 0
    LEFT JOIN (
        SELECT product_id, total_price
        FROM lgs_product_cost
        WHERE delivery_country_id = 10 AND is_deleted = 0
        AND id IN (SELECT MAX(id) FROM lgs_product_cost WHERE delivery_country_id = 10 AND is_deleted = 0 GROUP BY product_id)
    ) lc ON p.id = lc.product_id
    LEFT JOIN (
        SELECT product_id, SUM(qty) as total_sold
        FROM sal_order_row
        WHERE is_deleted = 0
        GROUP BY product_id
    ) sq ON p.id = sq.product_id
    WHERE s.warehouse_id IN (3, 4, 38)
      AND s.qty > 0
      AND s.is_deleted = 0
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print("No data found.")
        return

    # Calculate incidence
    df['price_it'] = pd.to_numeric(df['price_it'], errors='coerce')
    df['transport_cost_it'] = pd.to_numeric(df['transport_cost_it'], errors='coerce')
    
    df['incidenza_italia_attesa_val'] = (df['transport_cost_it'] / df['price_it']).fillna(0)
    
    # Sort by incidence descending
    df = df.sort_values(by='incidenza_italia_attesa_val', ascending=False)
    
    # Format incidence for display
    df['incidenza_italia_attesa'] = df['incidenza_italia_attesa_val'].apply(lambda x: f"{round(x*100, 2)}%")
    
    # Prepare final columns order
    report_df = df[['sku', 'warehouse', 'price_it', 'transport_cost_it', 'incidenza_italia_attesa', 'quantity', 'historical_sold_qty']].copy()
    
    # Rename columns for clarity
    report_df = report_df.rename(columns={
        'price_it': 'Prezzo Italia',
        'transport_cost_it': 'Costo Trasporto IT',
        'incidenza_italia_attesa': 'Incidenza IT Attesa',
        'quantity': 'Stock Attuale',
        'historical_sold_qty': 'Vendite Storiche (Tot)'
    })
    
    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for wh in report_df['warehouse'].unique():
            wh_df = report_df[report_df['warehouse'] == wh].drop(columns=['warehouse'])
            # Remove invalid sheet characters: \ / * ? : [ ]
            sheet_title = wh[:31].replace('/', '_').replace('\\', '_').replace('*', '_').replace('?', '_').replace(':', '_').replace('[', '_').replace(']', '_')
            wh_df.to_excel(writer, sheet_name=sheet_title, index=False)
            
    print(f"Report saved to {output_path}")

if __name__ == "__main__":
    generate_report("/root/.openclaw/workspace-operations/report_stock_incidenza_save.xlsx")
