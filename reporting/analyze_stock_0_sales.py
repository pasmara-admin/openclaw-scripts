import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
import os

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

def get_data(lookback_days, exclude_ps_refs):
    conn = mysql.connector.connect(**config_kanguro)
    
    # 1. Identify products with stock 0 today
    query_stock_0 = """
    SELECT product_id, SUM(qty) as total_qty
    FROM inv_inventory_stock
    WHERE is_deleted = 0
    GROUP BY product_id
    HAVING total_qty <= 0
    """
    df_stock_0 = pd.read_sql(query_stock_0, conn)
    stock_0_ids = df_stock_0['product_id'].tolist()
    
    if not stock_0_ids:
        conn.close()
        return None

    # 2. Check sales in the last N days for these products
    n_days_ago = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    
    # Filtering by type_id = 2 (ProduceShop) as per SOUL.md
    query_sales_nd = f"""
    SELECT sor.product_id, sor.reference, SUM(sor.qty) as units_nd
    FROM sal_order_row sor
    JOIN sal_order so ON sor.order_id = so.id
    WHERE sor.product_id IN ({','.join(map(str, stock_0_ids))})
      AND so.date >= '{n_days_ago}'
      AND so.is_deleted = 0
      AND sor.is_deleted = 0
      AND so.type_id = 2
    GROUP BY sor.product_id, sor.reference
    HAVING units_nd > 0
    """
    df_sales_nd = pd.read_sql(query_sales_nd, conn)
    
    if df_sales_nd.empty:
        conn.close()
        return None

    # Filter out references that still have stock on PrestaShop
    df_sales_nd = df_sales_nd[~df_sales_nd['reference'].isin(exclude_ps_refs)]
    
    if df_sales_nd.empty:
        conn.close()
        return None

    results = []
    for _, row in df_sales_nd.iterrows():
        pid = row['product_id']
        ref = row['reference']
        
        query_soldout = f"""
        SELECT MAX(date) as soldout_date
        FROM inv_inventory_stock_date
        WHERE product_id = {pid} AND final_qty <= 0 AND is_deleted = 0
        """
        soldout_res = pd.read_sql(query_soldout, conn)
        soldout_date = soldout_res['soldout_date'].iloc[0]
        
        if pd.isna(soldout_date):
            soldout_date = datetime.now().date()
        
        start_date = soldout_date - timedelta(days=30)
        end_date = soldout_date - timedelta(days=1)
        
        # Modified to get GMV WITHOUT VAT (using bil_document_row and 1.22 fallback)
        query_stats_30d = f"""
        SELECT 
            SUM(sor.qty) as total_qty_30d,
            SUM(COALESCE(bdr.total_price_tax_excl, sor.total_price / 1.22)) as total_gmv_30d
        FROM sal_order_row sor
        JOIN sal_order so ON sor.order_id = so.id
        LEFT JOIN bil_document_row bdr ON sor.id = bdr.order_row_id
        WHERE sor.product_id = {pid}
          AND so.date BETWEEN '{start_date}' AND '{end_date}'
          AND so.is_deleted = 0
          AND sor.is_deleted = 0
          AND so.type_id = 2
        """
        stats_res = pd.read_sql(query_stats_30d, conn)
        total_qty = stats_res['total_qty_30d'].iloc[0] or 0
        total_gmv = stats_res['total_gmv_30d'].iloc[0] or 0
        
        avg_qty_day = total_qty / 30.0
        avg_gmv_day = float(total_gmv) / 30.0
        
        results.append({
            'reference': ref,
            'soldout_date': soldout_date,
            'units_last_period': row['units_nd'],
            'avg_qty_day_pre_30d': avg_qty_day,
            'avg_gmv_day_pre_30d_no_vat': avg_gmv_day
        })
    
    conn.close()
    return pd.DataFrame(results)

if __name__ == "__main__":
    summary = []
    all_data = []
    
    # Get refs with stock on PrestaShop to exclude them
    exclude_ps_refs = get_ps_refs_with_stock()
    print(f"Esclusi {len(exclude_ps_refs)} riferimenti con stock > 0 su PrestaShop.")
    
    for days in [7, 14, 30]:
        df = get_data(days, exclude_ps_refs)
        if df is not None:
            avg_qty = df['avg_qty_day_pre_30d'].sum()
            avg_gmv = df['avg_gmv_day_pre_30d_no_vat'].sum()
            summary.append({
                'Periodo (giorni)': f'Ultimi {days} giorni',
                'Pezzi Medi Giornalieri (Totale)': round(avg_qty, 2),
                'GMV Medio Giornaliero Senza IVA (Totale)': round(avg_gmv, 2)
            })
            df['lookback_period'] = days
            all_data.append(df)
    
    if all_data:
        full_df = pd.concat(all_data).drop_duplicates(subset=['reference', 'lookback_period'])
        full_df.to_excel('stock_0_analysis_extended.xlsx', index=False)
        print(pd.DataFrame(summary).to_string(index=False))
    else:
        print("Nessun dato trovato.")
