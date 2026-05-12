import pandas as pd
import pymysql
import warnings
import sys
import datetime

warnings.filterwarnings('ignore')

def main():
    connection = pymysql.connect(
        host='34.38.166.212',
        user='john',
        password='3rmiCyf6d~MZDO41',
        database='kanguro'
    )

    query = """
    SELECT 
        d.id AS id_documento,
        d.order_number AS numero_ordine,
        DATE_FORMAT(d.date, '%d/%m/%Y') AS data,
        d.total AS totale,
        CONCAT(ROUND(d.tax_rate, 0), '%') AS iva_percentuale,
        d.total_tax AS iva_importo,
        pm.name AS metodo_di_pagamento,
        ct.name AS tipo_cliente,
        d.customer_name AS cliente,
        COALESCE(d.customer_vat_number, d.customer_fiscal_code) AS cliente_cf_piva,
        d.destination_name AS destinatario
    FROM bil_document d
    LEFT JOIN dat_payment_method pm ON d.payment_method_id = pm.id
    LEFT JOIN dat_customer_type ct ON d.customer_type_id = ct.id
    WHERE d.state_id = '20' AND d.is_deleted = 0
    ORDER BY d.date ASC, d.id ASC
    """

    df = pd.read_sql(query, connection)
    connection.close()

    output_path = '/tmp/ordini_attesa_piva_attivi.csv'
    if len(sys.argv) > 1:
        output_path = sys.argv[1]

    df.to_csv(output_path, index=False)
    print(f"Exported {len(df)} active orders to {output_path}")

if __name__ == "__main__":
    main()
