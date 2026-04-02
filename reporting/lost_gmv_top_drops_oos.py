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

def analyze_lost_gmv_v2():
    try:
        conn = mysql.connector.connect(**config)
        
        # 1. Get GMV for W10 and W14 (Mon-Wed) to identify top drops
        query_weeks = """
        SELECT 
            sor.product_id,
            sor.reference,
            YEARWEEK(so.date, 1) as year_week,
            SUM(sor.total_price) as gmv_net
        FROM sal_order_row sor
        JOIN sal_order so ON sor.order_id = so.id
        WHERE so.is_deleted = 0
          AND sor.is_deleted = 0
          AND so.type_id = 2
          AND sor.reference IS NOT NULL
          AND sor.reference NOT IN ('', '0')
          AND (
            (so.date BETWEEN '2026-03-02' AND '2026-03-04')
            OR 
            (so.date BETWEEN '2026-03-30' AND '2026-04-01')
          )
        GROUP BY sor.product_id, sor.reference, year_week
        """
        df_weeks = pd.read_sql(query_weeks, conn)
        df_weeks['week_label'] = df_weeks['year_week'].apply(lambda x: 'W10' if str(x).endswith('10') else 'W14')
        pivot_weeks = df_weeks.pivot(index=['product_id', 'reference'], columns='week_label', values='gmv_net').fillna(0).reset_index()
        
        if 'W10' not in pivot_weeks.columns or 'W14' not in pivot_weeks.columns:
            return "Dati insufficienti."

        pivot_weeks['Drop_GMV'] = pivot_weeks['W10'] - pivot_weeks['W14']
        # Filter for drops and get top 20
        top_drops = pivot_weeks[pivot_weeks['Drop_GMV'] > 0].sort_values(by='Drop_GMV', ascending=False).head(20)
        
        # 2. Check current stock for these top drops
        pids = [str(int(pid)) for pid in top_drops['product_id'].tolist()]
        query_stock = f"SELECT product_id, SUM(qty) as stock FROM inv_inventory_stock WHERE product_id IN ({','.join(pids)}) AND is_deleted = 0 GROUP BY product_id"
        df_stock = pd.read_sql(query_stock, conn)
        
        df_merged = pd.merge(top_drops, df_stock, on='product_id', how='left').fillna(0)
        df_oos = df_merged[df_merged['stock'] <= 0]
        
        if df_oos.empty:
            return "Nessuna delle referenze con calo maggiore è attualmente senza stock."

        # 3. For OOS ones, calculate daily baseline GMV (30d before soldout)
        results = []
        for _, row in df_oos.iterrows():
            pid = int(row['product_id'])
            ref = row['reference']
            
            # Find soldout date
            query_soldout = f"SELECT MAX(date) as soldout_date FROM inv_inventory_stock_date WHERE product_id = {pid} AND final_qty <= 0 AND is_deleted = 0"
            soldout_res = pd.read_sql(query_soldout, conn)
            soldout_date = soldout_res['soldout_date'].iloc[0]
            if pd.isna(soldout_date): soldout_date = datetime.now().date()
            
            # Baseline (30d prior)
            start_date = soldout_date - timedelta(days=30)
            end_date = soldout_date - timedelta(days=1)
            
            query_baseline = f"""
            SELECT SUM(total_price) as total_gmv
            FROM sal_order_row sor
            JOIN sal_order so ON sor.order_id = so.id
            WHERE sor.product_id = {pid} AND so.date BETWEEN '{start_date}' AND '{end_date}'
              AND so.is_deleted = 0 AND sor.is_deleted = 0 AND so.type_id = 2
            """
            baseline_res = pd.read_sql(query_baseline, conn)
            total_gmv = baseline_res['total_gmv'].iloc[0] or 0
            avg_daily_gmv = float(total_gmv) / 30.0
            
            results.append({
                'Referenza': ref,
                'Drop W10-W14 (L-M-M)': round(row['Drop_GMV'], 2),
                'Data Sold-out': soldout_date,
                'GMV Medio Giornaliero (Baseline)': round(avg_daily_gmv, 2)
            })
            
        conn.close()
        return pd.DataFrame(results).sort_values(by='GMV Medio Giornaliero (Baseline)', ascending=False)
        
    except Exception as e:
        return f"Errore: {str(e)}"

if __name__ == "__main__":
    res = analyze_lost_gmv_v2()
    if isinstance(res, pd.DataFrame):
        print(res.to_string(index=False))
    else:
        print(res)
