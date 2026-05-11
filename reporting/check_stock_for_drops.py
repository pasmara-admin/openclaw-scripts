import mysql.connector
import pandas as pd
from datetime import datetime

# Database configuration
config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_stock_for_references(refs):
    try:
        conn = mysql.connector.connect(**config)
        
        # Prepare refs for SQL
        refs_formatted = ",".join([f"'{r}'" for r in refs])
        
        query = f"""
        SELECT 
            iis.reference,
            SUM(iis.qty) as current_stock
        FROM inv_inventory_stock iis
        WHERE iis.reference IN ({refs_formatted})
          AND iis.is_deleted = 0
        GROUP BY iis.reference
        """
        
        # Wait, the error said "Unknown column 'reference' in 'field list'".
        # Let me check the table structure of inv_inventory_stock.
        cursor = conn.cursor()
        cursor.execute("DESCRIBE inv_inventory_stock")
        cols = [col[0] for col in cursor.fetchall()]
        print(f"Columns in inv_inventory_stock: {cols}")
        
        if 'reference' not in cols:
            # If reference is missing, we must use product_id
            # Let's get product_ids from sal_order_row for these refs
            query_pids = f"SELECT DISTINCT product_id, reference FROM sal_order_row WHERE reference IN ({refs_formatted}) AND is_deleted = 0"
            df_pids = pd.read_sql(query_pids, conn)
            pids = [str(int(pid)) for pid in df_pids['product_id'].tolist()]
            
            query_stock = f"SELECT product_id, SUM(qty) as current_stock FROM inv_inventory_stock WHERE product_id IN ({','.join(pids)}) AND is_deleted = 0 GROUP BY product_id"
            df_stock_raw = pd.read_sql(query_stock, conn)
            df_stock = pd.merge(df_pids, df_stock_raw, on='product_id', how='left').fillna(0)
        else:
            df_stock = pd.read_sql(query, conn)
            
        conn.close()
        return df_stock
        
    except Exception as e:
        return f"Errore: {str(e)}"

if __name__ == "__main__":
    top_drop_refs = [
        'SADIZ712TEBJ', 'DI8092MIGS', 'S6217BA22PZ', 'SR6201FVC', 
        'SADIZ712TEGS', '893RAN3348', '56586', 'SG613PPR', 
        'DI3552SG', 'PFA129LS', 'TA50NMNE4SWTM', 'PA6870TEXG', 
        'SPP838BI', 'AF90451806GC', 'S6316AC'
    ]
    
    res = get_stock_for_references(top_drop_refs)
    if isinstance(res, pd.DataFrame):
        print(res.to_string(index=False))
    else:
        print(res)
