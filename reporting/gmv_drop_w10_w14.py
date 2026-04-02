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

def analyze_gmv_drop_weeks_10_vs_14():
    try:
        conn = mysql.connector.connect(**config)
        
        # 1. Define periods
        # Week 10 2026: March 2, 3, 4 (Mon, Tue, Wed)
        # Week 14 2026: March 30, 31, April 1 (Mon, Tue, Wed)
        
        query = """
        SELECT 
            sor.reference,
            YEARWEEK(so.date, 1) as year_week,
            DAYOFWEEK(so.date) as day_of_week,
            SUM(sor.total_price) as gmv_net
        FROM sal_order_row sor
        JOIN sal_order so ON sor.order_id = so.id
        WHERE so.is_deleted = 0
          AND sor.is_deleted = 0
          AND so.type_id = 2 -- ProduceShop channel
          AND sor.reference IS NOT NULL
          AND sor.reference NOT IN ('', '0')
          AND (
            (so.date BETWEEN '2026-03-02' AND '2026-03-04') -- Week 10 Mon-Wed
            OR 
            (so.date BETWEEN '2026-03-30' AND '2026-04-01') -- Week 14 Mon-Wed
          )
        GROUP BY sor.reference, year_week
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return "Nessun dato trovato per i periodi specificati."

        # Map yearweeks to simple labels
        # 202610 -> Week 10, 202614 -> Week 14
        df['week_label'] = df['year_week'].apply(lambda x: 'W10' if str(x).endswith('10') else 'W14')
        
        # Pivot to compare weeks
        pivot_df = df.pivot(index='reference', columns='week_label', values='gmv_net').fillna(0)
        
        if 'W10' not in pivot_df.columns or 'W14' not in pivot_df.columns:
            return "Dati insufficienti per una delle due settimane."

        pivot_df['Drop_GMV'] = pivot_df['W10'] - pivot_df['W14']
        
        # Sort by biggest absolute drop
        top_drops = pivot_df[pivot_df['Drop_GMV'] > 0].sort_values(by='Drop_GMV', ascending=False).head(20)
        
        return top_drops
        
    except Exception as e:
        return f"Errore: {str(e)}"

if __name__ == "__main__":
    res = analyze_gmv_drop_weeks_10_vs_14()
    if isinstance(res, pd.DataFrame):
        print(res.to_string())
    else:
        print(res)
