import pandas as pd
import mysql.connector
import sys

def main():
    db_config = {
        'host': '34.38.166.212',
        'user': 'john',
        'password': '3rmiCyf6d~MZDO41',
        'database': 'kanguro'
    }

    query = """
    SELECT 
        o.number AS 'Numero Ordine',
        DATE_FORMAT(o.date, '%d/%m/%Y') AS 'Data Ordine',
        o.delivery_country AS 'Paese',
        d_inv.full_number AS 'Fattura Reverse Charge',
        DATE_FORMAT(d_inv.date, '%d/%m/%Y') AS 'Data Fattura RC',
        ROUND(o.total, 2) AS 'Totale Pagato (con IVA)',
        ROUND(d_inv.total, 2) AS 'Totale Fatturato RC (Senza IVA)',
        ROUND(o.total_refunded, 2) AS 'Totale Rimborsato (Attuale)',
        ROUND((o.total - d_inv.total) - o.total_refunded, 2) AS 'IVA da Rimborsare',
        o.source_srv AS '_source'
    FROM sal_order o
    JOIN bil_document d_inv ON d_inv.order_id = o.id AND d_inv.type_id = 1 AND d_inv.is_deleted = 0
    WHERE o.total > d_inv.total + 0.01 
      AND ROUND((o.total - d_inv.total) - o.total_refunded, 2) > 0.01
      AND d_inv.tax_id IN (SELECT id FROM dat_tax WHERE class_id = 7 OR rate = 0)
    ORDER BY d_inv.date DESC, o.date DESC;
    """

    conn = mysql.connector.connect(**db_config)
    df = pd.read_sql(query, conn)
    conn.close()

    # Split the dataframe
    df_sito = df[df['_source'] == 'PS'].drop(columns=['_source'])
    df_mk = df[df['_source'] == 'MK'].drop(columns=['_source'])

    output_path = '/tmp/ordini_reverse_charge_rimborsi.xlsx'
    if len(sys.argv) > 1:
        output_path = sys.argv[1]

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_sito.to_excel(writer, sheet_name='Vendite Sito', index=False)
        df_mk.to_excel(writer, sheet_name='Vendite Marketplace', index=False)

    print(f"Exported {len(df_sito)} sito and {len(df_mk)} marketplace orders to {output_path}")

if __name__ == "__main__":
    main()
