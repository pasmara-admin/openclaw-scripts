import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

# Database configuration
config_kanguro = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

config_ps = {
    'host': '62.84.190.199',
    'user': 'john',
    'password': 'qARa6aRozi6I',
    'database': 'produceshop'
}

def get_ps_refs_with_stock():
    """Returns a set of references that have qty > 0 on PrestaShop (IT shop)."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(**config_ps)
        query = """
        SELECT p.reference
        FROM ps_product p
        JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
        WHERE sa.id_shop = 1 AND sa.quantity > 0
        UNION
        SELECT pa.reference
        FROM ps_product_attribute pa
        JOIN ps_stock_available sa ON pa.id_product_attribute = sa.id_product_attribute
        WHERE sa.id_shop = 1 AND sa.quantity > 0
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return set(df['reference'].dropna().unique())
    except Exception as e:
        print(f"Error fetching PrestaShop stock: {e}")
        return set()

def analyze_lost_gmv_for_out_of_stock(refs):
    try:
        conn = mysql.connector.connect(**config_kanguro)
        
        # 0. Get PS refs with stock to exclude them
        exclude_ps_refs = get_ps_refs_with_stock()
        
        # 1. Identify which of these are currently stock 0 in Kanguro
        # First get product_ids for the references
        refs_formatted = ",".join([f"'{r}'" for r in refs])
        query_pids = f"SELECT DISTINCT product_id, reference FROM sal_order_row WHERE reference IN ({refs_formatted}) AND is_deleted = 0"
        df_refs = pd.read_sql(query_pids, conn)
        
        pids = df_refs['product_id'].tolist()
        pids_str = ",".join(map(str, [int(p) for p in pids]))
        
        # Check current stock
        query_stock = f"SELECT product_id, SUM(qty) as stock FROM inv_inventory_stock WHERE product_id IN ({pids_str}) AND is_deleted = 0 GROUP BY product_id"
        df_stock = pd.read_sql(query_stock, conn)
        
        # Filter only those with stock <= 0
        df_oos = pd.merge(df_refs, df_stock, on='product_id', how='left').fillna(0)
        df_oos = df_oos[df_oos['stock'] <= 0]
        
        # EXCLUSION RULE: Exclude items with qty > 0 on PrestaShop
        df_oos = df_oos[~df_oos['reference'].isin(exclude_ps_refs)]
        
        if df_oos.empty:
            conn.close()
            return "Nessuna delle referenze indicate è attualmente fuori stock (o sono ancora disponibili su PrestaShop)."

        oos_pids = df_oos['product_id'].tolist()
        results = []
        
        for pid in oos_pids:
            ref = df_oos[df_oos['product_id'] == pid]['reference'].iloc[0]
            
            # Find soldout date
            query_soldout = f"SELECT MAX(date) as soldout_date FROM inv_inventory_stock_date WHERE product_id = {pid} AND final_qty <= 0 AND is_deleted = 0"
            soldout_res = pd.read_sql(query_soldout, conn)
            soldout_date = soldout_res['soldout_date'].iloc[0]
            
            if pd.isna(soldout_date):
                soldout_date = datetime.now().date()
            
            # Calculate average GMV in the 30 days PRIOR to soldout
            start_date = soldout_date - timedelta(days=30)
            end_date = soldout_date - timedelta(days=1)
            
            query_avg = f"""
            SELECT SUM(total_price) as total_gmv
            FROM sal_order_row sor
            JOIN sal_order so ON sor.order_id = so.id
            WHERE sor.product_id = {pid}
              AND so.date BETWEEN '{start_date}' AND '{end_date}'
              AND so.is_deleted = 0
              AND sor.is_deleted = 0
              AND so.type_id = 2
            """
            avg_res = pd.read_sql(query_avg, conn)
            total_gmv = avg_res['total_gmv'].iloc[0] or 0
            avg_daily_gmv = float(total_gmv) / 30.0
            
            results.append({
                'Referenza': ref,
                'Soldout Date': soldout_date,
                'GMV Medio Giornaliero (Pre-Soldout)': round(avg_daily_gmv, 2)
            })
            
        conn.close()
        return pd.DataFrame(results)
        
    except Exception as e:
        return f"Errore: {str(e)}"

if __name__ == "__main__":
    refs = [
        'SADIZ712TEBJ', 'DI8092MIGS', 'S6217BA22PZ', 'SR6201FVC', 
        'SADIZ712TEGS', '893RAN3348', '56586', 'SG613PPR', 
        'DI3552SG', 'PFA129LS', 'TA50NMNE4SWTM', 'PA6870TEXG', 
        'SPP838BI', 'AF90451806GC', 'S6316AC'
    ]
    res = analyze_lost_gmv_for_out_of_stock(refs)
    if isinstance(res, pd.DataFrame):
        print(res.to_string(index=False))
    else:
        print(res)
