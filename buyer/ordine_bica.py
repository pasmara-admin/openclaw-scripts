import pymysql
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Database Kanguro
db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_order_bica():
    conn = pymysql.connect(**db_config)
    try:
        # 1. Carico i prodotti del fornitore BICA (ID 252)
        query_products = """
            SELECT 
                p.id, p.reference as sku, p.name, p.packaging_pieces as pack_qty, 
                p.is_active, CAST(p.composite AS UNSIGNED) as composite
            FROM dat_product p
            WHERE p.supplier_id = 252 AND p.is_deleted = 0
        """
        df_products = pd.read_sql(query_products, conn)

        # 2. Esplosione SET (dat_product_combination)
        # parent_product_id: il SET
        # component_product_id: il componente singolo
        query_combos = """
            SELECT product_id as parent_product_id, component_product_id as child_product_id, component_qty as qty
            FROM dat_product_combination
            WHERE is_deleted = 0
        """
        df_combos = pd.read_sql(query_combos, conn)

        # 3. Trend Vendite (Ultimi 30 giorni) - USCITE REALI (scarichi stock)
        date_limit = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        query_sales = f"""
            SELECT `row`.product_id, SUM(`row`.qty) as total_sold
            FROM sal_order_row `row`
            JOIN sal_order o ON `row`.order_id = o.id
            WHERE o.date >= '{date_limit}'
            AND o.state_id IN ('90', '99')
            AND `row`.is_deleted = 0
            GROUP BY `row`.product_id
        """
        df_sales = pd.read_sql(query_sales, conn)

        # 4. Stock e Impegnato
        # Stock Fisico e Impegnato (Smart)
        query_stock = """
            SELECT 
                product_id, 
                SUM(qty) as physical_stock
            FROM inv_inventory_stock
            WHERE is_deleted = 0
            GROUP BY product_id
        """
        df_stock = pd.read_sql(query_stock, conn)

        # Impegnato (ordini in stati intermedi tra Bozza e Spedito)
        query_reserved = """
            SELECT `row`.product_id, SUM(`row`.qty) as reserved_qty
            FROM sal_order_row `row`
            JOIN sal_order o ON `row`.order_id = o.id
            WHERE o.state_id NOT IN ('00', '10', '90', '99')
            AND `row`.is_deleted = 0
            GROUP BY `row`.product_id
        """
        df_reserved = pd.read_sql(query_reserved, conn)

        # 5. In Arrivo (non chiusi)
        # Calcoliamo la differenza tra ordinato e ricevuto per ordini fornitore non chiusi/annullati
        query_incoming = """
            SELECT 
                r.product_id, 
                SUM(r.qty - IFNULL(recv.received_qty, 0)) as incoming_qty
            FROM pch_order_row r
            JOIN pch_order o ON r.order_id = o.id
            LEFT JOIN (
                SELECT order_row_id, SUM(qty) as received_qty
                FROM pch_warehouse_receipt_row
                WHERE is_deleted = 0
                GROUP BY order_row_id
            ) recv ON r.id = recv.order_row_id
            WHERE o.state_id NOT IN ('00', '99')
            AND r.is_deleted = 0
            GROUP BY r.product_id
        """
        df_incoming = pd.read_sql(query_incoming, conn)

        # --- ELABORAZIONE ---
        
        # Merge dati vendite sui prodotti
        df = df_products.merge(df_sales, left_on='id', right_on='product_id', how='left').fillna(0)
        
        # Ribaltamento vendite SET sui componenti
        # Per ogni SET (composite=1), prendiamo le vendite e le aggiungiamo ai figli
        for idx, row in df[df['composite'] == 1].iterrows():
            if row['total_sold'] > 0:
                children = df_combos[df_combos['parent_product_id'] == row['id']]
                for c_idx, c_row in children.iterrows():
                    child_id = c_row['child_product_id']
                    child_qty_in_set = c_row['qty']
                    added_sales = row['total_sold'] * child_qty_in_set
                    df.loc[df['id'] == child_id, 'total_sold'] += added_sales

        # Rimuoviamo i SET dal report finale (come richiesto in IGAP e solitamente in questi ordini componenti)
        df_final = df[df['composite'] == 0].copy()

        # Merge Stock, Reserved, Incoming, etc.
        df_final = df_final.merge(df_stock, left_on='id', right_on='product_id', how='left').fillna(0)
        df_final = df_final.drop(columns=['product_id_y'], errors='ignore')
        
        df_final = df_final.merge(df_reserved, left_on='id', right_on='product_id', how='left').fillna(0)
        df_final = df_final.drop(columns=['product_id'], errors='ignore')
        
        df_final = df_final.merge(df_incoming, left_on='id', right_on='product_id', how='left').fillna(0)
        df_final = df_final.drop(columns=['product_id'], errors='ignore')
        
        # Calcoli Protocollo BICA
        df_final['media_giornaliera'] = df_final['total_sold'] / 30.0
        df_final['fabbisogno_30gg'] = df_final['media_giornaliera'] * 30
        
        df_final = df_final.sort_values(by='total_sold', ascending=False)
        df_final['cum_sales'] = df_final['total_sold'].cumsum()
        total_sum = df_final['total_sold'].sum()
        df_final['pareto_top'] = df_final['cum_sales'] <= (total_sum * 0.8)
        
        df_final['buffer_volatilta'] = df_final.apply(lambda x: x['fabbisogno_30gg'] * 0.15 if x['pareto_top'] else 0, axis=1)
        df_final['safe_stock'] = df_final['media_giornaliera'] * 10
        df_final['stock_virtuale'] = df_final['physical_stock'] + df_final['incoming_qty'] - df_final['reserved_qty']
        df_final['fabbisogno_totale'] = df_final['fabbisogno_30gg'] + df_final['buffer_volatilta'] + df_final['safe_stock'] - df_final['stock_virtuale']
        df_final['qty_proposta'] = df_final['fabbisogno_totale'].apply(lambda x: max(0, x))
        
        def round_pack(r):
            qty = r['qty_proposta']
            pack = r['pack_qty']
            if qty <= 0: return 0.0
            p = float(pack) if (pack and float(pack) > 0) else 20.0
            if p < 10: p = 20.0
            import math
            return float(math.ceil(qty / p) * p)

        # Usiamo list() e forziamo il tipo numerico
        df_final['qty_acquisto_finale'] = pd.to_numeric(list(df_final.apply(round_pack, axis=1)), errors='coerce')
        df_final['qty_acquisto_finale'] = df_final['qty_acquisto_finale'].fillna(0)

        # Output Excel
        today_str = datetime.now().strftime('%Y%m%d')
        output_analisi = f'/root/.openclaw/workspace-buyer/Analisi_Ordine_BICA_{today_str}.xlsx'
        output_import = f'/root/.openclaw/workspace-buyer/Import_Ordine_BICA_{today_str}.xlsx'
        
        df_final.to_excel(output_analisi, index=False)
        
        df_import = df_final[df_final['qty_acquisto_finale'] > 0][['sku', 'qty_acquisto_finale']]
        df_import.to_excel(output_import, index=False)
        
        return output_analisi, output_import

    finally:
        conn.close()

if __name__ == "__main__":
    a, i = get_order_bica()
    print(f"REPORT_READY:{a}")
    print(f"IMPORT_READY:{i}")
