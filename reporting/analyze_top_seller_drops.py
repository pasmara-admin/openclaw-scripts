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

def analyze_top_seller_drops(days=15):
    try:
        conn = mysql.connector.connect(**config)
        
        # 1. Get daily sales for all products in the last 15 days + buffer for prior sales
        date_start = (datetime.now() - timedelta(days=days + 1)).strftime('%Y-%m-%d')
        
        query_daily_sales = f"""
        SELECT 
            so.date,
            sor.product_id, 
            sor.reference, 
            SUM(sor.qty) as units_sold
        FROM sal_order_row sor
        JOIN sal_order so ON sor.order_id = so.id
        WHERE so.date >= '{date_start}'
          AND so.is_deleted = 0
          AND sor.is_deleted = 0
          AND so.type_id = 2 -- ProduceShop channel
          AND sor.reference IS NOT NULL
          AND sor.reference NOT IN ('', '0')
        GROUP BY so.date, sor.product_id, sor.reference
        """
        df_daily = pd.read_sql(query_daily_sales, conn)
        df_daily['date'] = pd.to_datetime(df_daily['date']).dt.date
        
        # 2. Identify top 3 sellers per day
        unique_days = sorted(df_daily['date'].unique())
        top_sellers_history = []
        
        for d in unique_days:
            day_data = df_daily[df_daily['date'] == d].sort_values(by='units_sold', ascending=False).head(3)
            top_sellers_history.extend(day_data.to_dict('records'))
        
        df_top_daily = pd.DataFrame(top_sellers_history)
        unique_top_pids = df_top_daily['product_id'].unique()
        
        # 3. Check stock levels for these products during those days
        # We look at inv_inventory_stock_date to see if they hit 0
        pids_str = ",".join(map(str, [int(pid) for pid in unique_top_pids]))
        query_stock_history = f"""
        SELECT 
            date,
            product_id,
            final_qty
        FROM inv_inventory_stock_date
        WHERE product_id IN ({pids_str})
          AND date >= '{date_start}'
          AND is_deleted = 0
        """
        df_stock_history = pd.read_sql(query_stock_history, conn)
        df_stock_history['date'] = pd.to_datetime(df_stock_history['date']).dt.date
        
        # 4. Analyze drops > 50%
        results = []
        # We iterate through each unique top seller found
        for pid in unique_top_pids:
            pid_sales = df_daily[df_daily['product_id'] == pid].sort_values('date')
            ref = pid_sales['reference'].iloc[0]
            
            for i in range(len(pid_sales) - 1):
                day_t = pid_sales.iloc[i]
                day_t1 = pid_sales.iloc[i+1]
                
                sales_t = day_t['units_sold']
                sales_t1 = day_t1['units_sold']
                
                # Check if this product was a top 3 seller on day_t
                is_top_on_t = not df_top_daily[(df_top_daily['date'] == day_t['date']) & (df_top_daily['product_id'] == pid)].empty
                
                if is_top_on_t and sales_t > 2: # Ignore very small numbers to avoid noise
                    drop = (sales_t - sales_t1) / sales_t
                    if drop > 0.5:
                        # Check if it was a stockout on day_t1
                        stock_t1 = df_stock_history[(df_stock_history['date'] == day_t1['date']) & (df_stock_history['product_id'] == pid)]
                        stock_val = stock_t1['final_qty'].iloc[0] if not stock_t1.empty else 10 # Assume in stock if missing
                        
                        if stock_val > 0:
                            results.append({
                                'Data': day_t['date'],
                                'Referenza': ref,
                                'Vendite T': sales_t,
                                'Vendite T+1': sales_t1,
                                'Drop %': round(drop * 100, 1),
                                'Stock T+1': stock_val
                            })
        
        conn.close()
        return pd.DataFrame(results)
        
    except Exception as e:
        return f"Errore: {str(e)}"

if __name__ == "__main__":
    res = analyze_top_seller_drops(15)
    if isinstance(res, pd.DataFrame):
        if res.empty:
            print("Nessun calo > 50% rilevato per i top seller senza stock-out.")
        else:
            print(res.to_string(index=False))
    else:
        print(res)
