import pandas as pd
import pymysql
import re

def get_connection():
    return pymysql.connect(
        host='34.38.166.212',
        user='john',
        password='3rmiCyf6d~MZDO41',
        database='kanguro'
    )

def identify_categories_es(df):
    for col in ['long_side', 'short_side', 'height']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['max_side'] = df[['long_side', 'short_side', 'height']].max(axis=1) * 100
    
    def classify(row):
        name = str(row['name']).lower()
        max_dim = row['max_side']
        weight_kg = pd.to_numeric(row['unit_weight_g'], errors='coerce') / 1000.0
        
        if max_dim == 0:
            if weight_kg > 10:
                max_dim = 100
            else:
                max_dim = 30
                
        # Exclusions for Spain
        if re.search(r'(pedana|parascintille|portalegna|supporto|palo|staffa|kit installazione|cornice|sassi|legnetti|pentola|padella|tegame|casseruola|batteria di pentole|copri|copertura|custodia|telo|ricambio|filtro)', name):
            return None
            
        if re.search(r'(sedia|sedie|sgabello|sgabelli|tavolo|tavoli|mobile|credenza|madia|poltrona|divano|letto|materasso|armadio|scrivania|mensola|coperchio|postazione|comodino)', name):
            if not re.search(r'(ventola|aspiratore|led|elettrica|massaggi)', name):
                return None

        if re.search(r'(climatizzatore|condizionatore|pompa di calore|deumidificatore|clima|fancoil)', name):
            return "Cat1"
            
        if re.search(r'(lampada|lampadario|applique|plafoniera|faretto|illuminazione|lanterna|luce|luci solari)', name) and not re.search(r'(specchio|mobile|ombrellone|valigetta|trolley|postazione|comodino)', name):
            if max_dim > 50:
                return "Cat3"
                
        if re.search(r'(asciugacapelli|rasoio|epilatore|tagliacapelli|piastra|spazzolino|massaggiatore|manicure|pedicure|fornetto|lampada uv|aspiratore unghie)', name):
            if max_dim <= 50:
                return "Cat5"
            else:
                return "Cat4"
                
        if re.search(r'(power bank|batteria portatile|accumulatore)', name) and re.search(r'(litio|lithium|li-ion|li-po)', name):
            return "Cat6"

        is_appliance = re.search(r'(stufa|radiatore|caldaia|forno|lavatrice|asciugatrice|lavastoviglie|frigorifero|congelatore|piano cottura|cucina a gas|cucina elettrica|frullatore|friggitrice|mixer|tostapane|bollitore|macchina caffè|ferro da stiro|aspirapolvere|centrifuga|microonde|sandwich|waffle|griglia|frusta elettrica|stufetta|idromassaggio|doccia solare)', name)
        
        is_led_furniture = re.search(r'(poltrona|sedia|mobile|valigetta|postazione|comodino).*led|led.*(poltrona|sedia|mobile|valigetta|postazione|comodino)', name)
        is_electric_furniture = re.search(r'(poltrona|sedia|mobile|postazione|comodino).*(elettrica|massaggi|wireless usb|caricatore wireless)', name)
        
        if is_appliance or is_led_furniture or is_electric_furniture or re.search(r'(lampada|luce)', name):
            if max_dim > 50:
                return "Cat4"
            else:
                return "Cat5"
                
        return None

    df['Category'] = df.apply(classify, axis=1)
    return df

def main():
    conn = get_connection()
    
    query_products = """
    SELECT dp.id, dp.reference, dp.name, dp.long_side, dp.short_side, dp.height, dp.unit_weight_g
    FROM dat_product dp
    WHERE dp.is_active = b'1' AND dp.is_deleted = b'0'
    """
    df_products = pd.read_sql(query_products, conn)
    
    df_products = identify_categories_es(df_products)
    df_raee = df_products[df_products['Category'].notnull()].copy()
    
    query_sales = """
    SELECT 
        sor.product_id,
        SUM(sor.qty) as total_qty
    FROM sal_order_row sor
    JOIN sal_order so ON sor.order_id = so.id
    WHERE so.date >= '2026-01-01' AND so.date <= '2026-03-31'
      AND so.delivery_country = 'Espana'
      AND so.source_srv = 'PS'
      AND so.state_id NOT IN ('09') 
      AND sor.is_deleted = b'0'
      AND so.is_deleted = b'0'
    GROUP BY sor.product_id
    """
    df_sales = pd.read_sql(query_sales, conn)
    
    query_refunds = """
    SELECT 
        bdr.product_id,
        SUM(bdr.qty) as refund_qty
    FROM bil_document_row bdr
    JOIN bil_document bd ON bdr.document_id = bd.id
    JOIN sal_order so ON bd.order_id = so.id
    WHERE bd.date >= '2026-01-01' AND bd.date <= '2026-03-31'
      AND so.delivery_country = 'Espana'
      AND so.source_srv = 'PS'
      AND bd.type_id IN (2, 4) 
      AND bd.is_deleted = 0
      AND bdr.is_deleted = 0
    GROUP BY bdr.product_id
    """
    df_refunds = pd.read_sql(query_refunds, conn)
    
    conn.close()
    
    df_final = df_raee.merge(df_sales, left_on='id', right_on='product_id', how='left')
    df_final = df_final.merge(df_refunds, left_on='id', right_on='product_id', how='left')
    
    df_final['total_qty'] = df_final['total_qty'].fillna(0)
    df_final['refund_qty'] = df_final['refund_qty'].fillna(0)
    
    df_final['Pezzi Venduti Netto'] = df_final['total_qty'] - df_final['refund_qty']
    df_final = df_final[df_final['Pezzi Venduti Netto'] > 0]
    
    df_final.to_csv('/root/.openclaw/workspace-shared/openclaw-scripts/finance/spain_output.csv', index=False)

if __name__ == "__main__":
    main()
