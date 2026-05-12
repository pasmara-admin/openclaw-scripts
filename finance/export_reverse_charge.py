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

    # Query 1: Ordini DA rimborsare (Differenza > 0.01)
    query_da_rimborsare = """
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

    # Query 2: Ordini GIA' rimborsati (Differenza <= 0.01, e rimborso > 0)
    query_gia_rimborsati = """
    SELECT 
        o.number AS 'Numero Ordine',
        DATE_FORMAT(o.date, '%d/%m/%Y') AS 'Data Ordine',
        o.delivery_country AS 'Paese',
        d_inv.full_number AS 'Fattura Reverse Charge',
        DATE_FORMAT(d_inv.date, '%d/%m/%Y') AS 'Data Fattura RC',
        ROUND(o.total, 2) AS 'Totale Pagato (con IVA)',
        ROUND(d_inv.total, 2) AS 'Totale Fatturato RC (Senza IVA)',
        ROUND(o.total_refunded, 2) AS 'Totale Rimborsato (Attuale)',
        o.source_srv AS '_source'
    FROM sal_order o
    JOIN bil_document d_inv ON d_inv.order_id = o.id AND d_inv.type_id = 1 AND d_inv.is_deleted = 0
    WHERE o.total > d_inv.total + 0.01 
      AND ROUND((o.total - d_inv.total) - o.total_refunded, 2) <= 0.01
      AND o.total_refunded > 0.01
      AND d_inv.tax_id IN (SELECT id FROM dat_tax WHERE class_id = 7 OR rate = 0)
    ORDER BY d_inv.date DESC, o.date DESC;
    """

    conn = mysql.connector.connect(**db_config)
    df_da_rimborsare = pd.read_sql(query_da_rimborsare, conn)
    df_gia_rimborsati = pd.read_sql(query_gia_rimborsati, conn)
    conn.close()

    # Split the "da rimborsare" dataframe
    df_sito_da_rimborsare = df_da_rimborsare[df_da_rimborsare['_source'] == 'PS'].drop(columns=['_source'])
    df_mk_da_rimborsare = df_da_rimborsare[df_da_rimborsare['_source'] == 'MK'].drop(columns=['_source'])

    # Split the "gia rimborsati" dataframe
    df_sito_gia_rimborsati = df_gia_rimborsati[df_gia_rimborsati['_source'] == 'PS'].drop(columns=['_source'])
    df_mk_gia_rimborsati = df_gia_rimborsati[df_gia_rimborsati['_source'] == 'MK'].drop(columns=['_source'])

    output_path = '/tmp/ordini_reverse_charge.xlsx'
    if len(sys.argv) > 1:
        output_path = sys.argv[1]

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_sito_da_rimborsare.to_excel(writer, sheet_name='DA Rimborsare - Sito', index=False)
        df_mk_da_rimborsare.to_excel(writer, sheet_name='DA Rimborsare - MK', index=False)
        df_sito_gia_rimborsati.to_excel(writer, sheet_name='GIA Rimborsati - Sito', index=False)
        df_mk_gia_rimborsati.to_excel(writer, sheet_name='GIA Rimborsati - MK', index=False)

    print(f"Exported to {output_path}")
    print(f"Sito (Da rimborsare: {len(df_sito_da_rimborsare)}, Già rimborsati: {len(df_sito_gia_rimborsati)})")
    print(f"MK (Da rimborsare: {len(df_mk_da_rimborsare)}, Già rimborsati: {len(df_mk_gia_rimborsati)})")

if __name__ == "__main__":
    main()
