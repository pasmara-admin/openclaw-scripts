import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

# Database configuration
config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_top_sellers_with_stock(days=15, limit=20):
    try:
        conn = mysql.connector.connect(**config)
        
        # 1. Get sales for the last N days
        date_start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query_sales = f"""
        SELECT 
            sor.product_id, 
            sor.reference, 
            SUM(sor.qty) as units_sold,
            SUM(sor.total_price) as total_gmv
        FROM sal_order_row sor
        JOIN sal_order so ON sor.order_id = so.id
        WHERE so.date >= '{date_start}'
          AND so.is_deleted = 0
          AND sor.is_deleted = 0
          AND so.type_id = 2 -- ProduceShop channel
          AND sor.reference IS NOT NULL
          AND sor.reference != ''
          AND sor.reference != '0'
        GROUP BY sor.product_id, sor.reference
        ORDER BY units_sold DESC
        LIMIT {limit}
        """
        df_sales = pd.read_sql(query_sales, conn)
        
        if df_sales.empty:
            conn.close()
            return "Nessuna vendita trovata negli ultimi 15 giorni."

        # Ensure we filter out any NaN or 0 IDs before querying stock
        product_ids = [str(int(pid)) for pid in df_sales['product_id'].dropna().unique() if pid > 0]
        
        if not product_ids:
            conn.close()
            return "Nessun ID prodotto valido trovato per il recupero dello stock."
        
        # 2. Get current stock for these products
        query_stock = f"""
        SELECT 
            product_id, 
            SUM(qty) as current_stock
        FROM inv_inventory_stock
        WHERE product_id IN ({','.join(product_ids)})
          AND is_deleted = 0
        GROUP BY product_id
        """
        df_stock = pd.read_sql(query_stock, conn)
        
        # Merge data (ensure types match for merge)
        df_sales['product_id'] = df_sales['product_id'].astype(float)
        df_stock['product_id'] = df_stock['product_id'].astype(float)
        
        df_final = pd.merge(df_sales, df_stock, on='product_id', how='left').fillna(0)
        df_final['current_stock'] = df_final['current_stock'].astype(int)
        
        conn.close()
        return df_final
        
    except Exception as e:
        return f"Errore durante l'estrazione dati: {str(e)}"

if __name__ == "__main__":
    df = get_top_sellers_with_stock(15, 20)
    if isinstance(df, pd.DataFrame):
        print(df[['reference', 'units_sold', 'current_stock', 'total_gmv']].to_string(index=False))
    else:
        print(df)
