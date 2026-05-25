import mysql.connector
import sys
import os

# Configurazione Database Kanguro
DB_CONFIG = {
    "host": "34.38.166.212",
    "user": "john",
    "password": "3rmiCyf6d~MZDO41",
    "database": "kanguro"
}

# Lista SKU da monitorare
SKUS = [
    '956LCS1538','909NRD1109','909NRD1105','909NRD1104','909NRD1103','909NRD1102',
    '893RAN5409','893RAN5401','893RAN3349','893RAN3348','893RAN3347','893RAN3303',
    '893RAN3110','893RAN2711','855DTE3513','845HCT4224','845HCT4222','845HCT4220',
    '845HCT4219','776HMS3678','776HMS3614','746NRD1109','746NRD1108','668NRD1122',
    '668NRD1120','668NRD1119','618BLY1275','618BLY1266','618BLY1262','618BLY1261',
    '618BLY1179','618BLY1175','618BLY1106','618BLY1104','618BLY1103','543WRN1516',
    '495SSE2115','382NRC2508','353NRD1126','353NRD1124','353NRD1123','353NRD1122',
    '241NRD1316','241NRD1218','241NRD1110','241NRD1101'
]

W_ID_CICOGNOLO = 11

def check_stock():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        sku_list_str = "('" + "','".join(SKUS) + "')"
        
        # Query per identificare i prodotti con stock 0 a Cicognolo (sia master che componenti)
        query = f"""
        SELECT 
            p.reference,
            p.name,
            CASE 
                WHEN p.composite = 1 THEN 
                    (SELECT MIN(IFNULL(s.qty, 0)) 
                     FROM dat_product_combination comb 
                     LEFT JOIN inv_inventory_stock s ON comb.component_product_id = s.product_id AND s.warehouse_id = {W_ID_CICOGNOLO}
                     WHERE comb.product_id = p.id)
                ELSE 
                    IFNULL((SELECT s.qty FROM inv_inventory_stock s WHERE s.product_id = p.id AND s.warehouse_id = {W_ID_CICOGNOLO} LIMIT 1), 0)
            END as real_stock
        FROM dat_product p
        WHERE p.reference IN {sku_list_str}
        HAVING real_stock = 0 OR real_stock IS NULL;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    results = check_stock()
    if results is None:
        return

    msg = "📦 *Aggiornamento Stock Cicognolo (Lunedì)*\n\n"
    if not results:
        msg += "Tutti i prodotti dell'elenco hanno ancora disponibilità (master o colli) a Cicognolo."
    else:
        msg += "I seguenti prodotti risultano a *stock 0* (sia master che colli) a Cicognolo:\n\n"
        for row in results:
            msg += f"• `{row['reference']}` - {row['name']}\n"

    # Invia il messaggio tramite OpenClaw message tool (simulato via CLI se necessario, o delegato al bot)
    # In questo contesto di script standalone, usiamo l'utility openclaw message se disponibile o invochiamo il gateway.
    # Per semplicità e coerenza, lo script scriverà l'output che verrà catturato dal cron di OpenClaw.
    print(msg)

if __name__ == "__main__":
    main()
