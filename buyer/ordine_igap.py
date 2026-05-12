import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import os

# Configurazione database
db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def run_query(query):
    conn = mysql.connector.connect(**db_config)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def generate_igap_order():
    print("Avvio elaborazione ORDINE IGAP...")
    
    # 1. Recupero prodotti IGAP (Supplier ID 3)
    # Prendiamo tutti i prodotti attivi o con stock
    query_products = """
    SELECT 
        p.id, 
        p.reference as sku, 
        p.name, 
        p.packaging_pieces as pack_qty,
        p.is_active
    FROM dat_product p
    WHERE p.supplier_id = 3 AND p.is_deleted = 0
    """
    df_products = run_query(query_products)
    
    # 2. Trend Vendite (Ultimi 60 giorni) con ESPLOSIONE SET
    # Prendiamo tutte le vendite di qualsiasi prodotto
    # E se il prodotto è un bundle, lo esplodiamo nei suoi componenti IGAP
    query_sales = """
    SELECT 
        COALESCE(pc.component_product_id, r.product_id) as final_product_id,
        SUM(r.qty * COALESCE(pc.component_qty, 1)) as total_sold
    FROM sal_order_row r
    JOIN sal_order s ON r.order_id = s.id
    LEFT JOIN dat_product_combination pc ON r.product_id = pc.product_id AND pc.is_deleted = 0
    WHERE s.date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
      AND s.is_deleted = 0
    GROUP BY final_product_id
    HAVING final_product_id IN (SELECT id FROM dat_product WHERE supplier_id = 3 AND is_deleted = 0)
    """
    df_sales = run_query(query_sales)
    
    # 3. Stock Fisico
    query_stock = """
    SELECT 
        product_id, 
        SUM(qty) as stock_fisico
    FROM inv_inventory_stock
    WHERE is_deleted = 0
    GROUP BY product_id
    """
    df_stock = run_query(query_stock)
    
    # 4. In Arrivo (Ordini fornitori aperti)
    # Escludiamo ordini Chiusi (99) e Annullati (00)
    query_incoming = """
    SELECT 
        r.product_id, 
        SUM(r.qty - COALESCE((SELECT SUM(qty) FROM pch_warehouse_receipt_row WHERE order_row_id = r.id AND is_deleted = 0), 0)) as incoming_qty
    FROM pch_order_row r
    JOIN pch_order o ON r.order_id = o.id
    WHERE o.supplier_id = 3 
      AND o.state_id NOT IN ('99', '00') 
      AND o.is_deleted = 0
      AND r.is_deleted = 0
    GROUP BY r.product_id
    """
    df_incoming = run_query(query_incoming)
    
    # 5. Impegnato Smart
    # Ordini non ancora evasi (Stati: PR, AP, PA)
    # Ribaltiamo bundle/set sulle singole componenti
    query_committed = """
    SELECT 
        COALESCE(pc.component_product_id, r.product_id) as final_product_id,
        SUM(r.qty * COALESCE(pc.component_qty, 1)) as impegnato
    FROM sal_order_row r
    JOIN sal_order s ON r.order_id = s.id
    LEFT JOIN dat_product_combination pc ON r.product_id = pc.product_id AND pc.is_deleted = 0
    WHERE s.state_id IN ('PR', 'AP', 'PA') 
      AND s.is_deleted = 0
    GROUP BY final_product_id
    HAVING final_product_id IN (SELECT id FROM dat_product WHERE supplier_id = 3 AND is_deleted = 0)
    """
    df_committed = run_query(query_committed)

    # Merge dei dati
    df = df_products.merge(df_sales, left_on='id', right_on='final_product_id', how='left').fillna(0)
    df = df.merge(df_stock, left_on='id', right_on='product_id', how='left').fillna(0)
    df = df.merge(df_incoming, left_on='id', right_on='product_id', how='left').fillna(0)
    df = df.merge(df_committed, left_on='id', right_on='final_product_id', how='left').fillna(0)
    
    # Pulizia colonne post-merge
    df = df.drop(columns=['final_product_id_x', 'final_product_id_y', 'product_id_x', 'product_id_y'], errors='ignore')
    
    # Calcoli Protocollo IGAP
    # Orizzonte: 21 giorni
    df['media_giornaliera'] = df['total_sold'] / 60
    df['fabbisogno_21gg'] = df['media_giornaliera'] * 21
    
    # Pareto & Volatilità (+15% se top seller - qui applichiamo a tutti per sicurezza o calcoliamo pareto)
    # Calcolo Pareto 80%
    df = df.sort_values(by='total_sold', ascending=False)
    df['cum_sales'] = df['total_sold'].cumsum()
    total_sales_sum = df['total_sold'].sum()
    df['pareto_top'] = df['cum_sales'] <= (total_sales_sum * 0.8)
    
    df['buffer_volatilta'] = df.apply(lambda x: x['fabbisogno_21gg'] * 0.15 if x['pareto_top'] else 0, axis=1)
    
    # Safe Stock (Lead Time 4gg)
    df['safe_stock'] = df['media_giornaliera'] * 4
    
    # Stock Virtuale = Fisico + In Arrivo - Impegnato
    df['stock_virtuale'] = df['stock_fisico'] + df['incoming_qty'] - df['impegnato']
    
    # Proposta d'acquisto
    # Fabbisogno Totale = Fabbisogno 21gg + Buffer + Safe Stock
    df['fabbisogno_totale'] = df['fabbisogno_21gg'] + df['buffer_volatilta'] + df['safe_stock']
    
    df['qty_proposta'] = df['fabbisogno_totale'] - df['stock_virtuale']
    df.loc[df['qty_proposta'] < 0, 'qty_proposta'] = 0
    
    # Vincoli Acquisto: Arrotondamento pack_qty (min 20 se mancante o < 10)
    def adjust_qty(row):
        if row['qty_proposta'] <= 0:
            return 0
        pack = row['pack_qty']
        if pack < 10 or pd.isna(pack):
            pack = 20
        
        import math
        return math.ceil(row['qty_proposta'] / pack) * pack

    df['qty_acquisto_finale'] = df.apply(adjust_qty, axis=1)
    
    # Filtro Finale: Escludiamo i SET/Bundles dal report finale come richiesto da Simone
    # Un prodotto è un set se è marcato come composite o se ha componenti nella tabella combinations
    query_composites = "SELECT product_id FROM dat_product_combination WHERE is_deleted = 0 GROUP BY product_id"
    df_composites = run_query(query_composites)
    df = df[~df['id'].isin(df_composites['product_id'])]

    # Output Files
    report_path = f"/root/.openclaw/workspace-buyer/Analisi_Ordine_IGAP_{datetime.now().strftime('%Y%m%d')}.xlsx"
    import_path = f"/root/.openclaw/workspace-buyer/Import_Ordine_IGAP_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    df.to_excel(report_path, index=False)
    df[df['qty_acquisto_finale'] > 0][['sku', 'qty_acquisto_finale']].to_excel(import_path, index=False)
    
    return report_path, import_path

if __name__ == "__main__":
    report, imp = generate_igap_order()
    print(f"REPORT_READY:{report}")
    print(f"IMPORT_READY:{imp}")
