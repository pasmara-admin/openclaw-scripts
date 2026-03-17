import pandas as pd
import mysql.connector
import os
import subprocess

db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_data():
    conn = mysql.connector.connect(**db_config)
    
    # Query A: Anomalie Storni (Febbraio) - Solo senza riemissione
    query_a = """
    SELECT 
        o.number AS 'Numero Ordine',
        d.full_number AS 'Numero Documento Storno',
        d.date AS 'Data Storno',
        t.name AS 'Tipo Documento',
        o.total AS 'Totale Ordine',
        o.total_refunded AS 'Totale Rimborsato',
        o.delivery_country AS 'Paese',
        'Storno senza riemissione e senza rimborso' AS 'Nota Anomalia'
    FROM bil_document d
    JOIN sal_order o ON d.order_id = o.id
    JOIN bil_document_type_lang t ON d.type_id = t.type_id AND t.lang_id = 1
    WHERE d.type_id IN (2, 4) 
      AND d.date BETWEEN '2026-02-01' AND '2026-02-28'
      AND o.total_refunded < 0.01
      AND NOT EXISTS (
          SELECT 1 FROM bil_document d2 
          WHERE d2.order_id = d.order_id 
            AND d2.type_id IN (1, 3) 
            AND (d2.date > d.date OR (d2.date = d.date AND d2.id > d.id))
      )
    """
    
    # Query B: Analisi Rimborsi (Febbraio) - Solo Reverse Charge isolati
    # Escludiamo i casi con documenti emessi (anche se a marzo)
    query_b = """
    SELECT 
        o.number AS 'Numero Ordine',
        o.date AS 'Data Ordine',
        o.total AS 'Totale Ordine',
        o.total_invoiced AS 'Totale Fatturato',
        o.total_refunded AS 'Totale Rimborsato',
        o.delivery_country AS 'Paese Destinazione',
        ROUND(o.total - o.total_invoiced, 2) AS 'IVA Non Esposta',
        'Reverse Charge / IVA Estero' AS 'Stato / Nota'
    FROM sal_order o
    WHERE o.total_refunded > 0.01 
      AND o.date BETWEEN '2026-02-01' AND '2026-02-28'
      AND NOT EXISTS (
          SELECT 1 FROM bil_document d 
          WHERE d.order_id = o.id 
            AND d.type_id IN (2, 4)
      )
      AND ABS((o.total - o.total_invoiced) - o.total_refunded) < 0.1
    """
    
    df_a = pd.read_sql(query_a, conn)
    df_b = pd.read_sql(query_b, conn)
    
    conn.close()
    return df_a, df_b

def main():
    df_a, df_b = get_data()
    
    file_a = 'Lista_A_Anomalie_Storni_Febbraio.xlsx'
    file_b = 'Lista_B_Analisi_Rimborsi_Febbraio.xlsx'
    
    df_a.to_excel(file_a, index=False)
    df_b.to_excel(file_b, index=False)
    
    recipient = 'ivan.cianci@produceshop.com'
    subject = 'Report Anomalie Contabili - Febbraio 2026 (Versione Corretta)'
    body = """Ciao Ivan,

Ecco i report corretti come da tue indicazioni:

1. Lista A: Filtrati i casi di riemissione.
2. Lista B: Isolati esclusivamente i casi di Reverse Charge / IVA Estero, rimosse le segnalazioni sui ritardi di emissione e corretti i valori di IVA non esposta.

I file Excel sono allegati.

John Operations"""

    env = os.environ.copy()
    env["GOG_KEYRING_PASSWORD"] = "produceshop"
    env["GOG_ACCOUNT"] = "admin@produceshoptech.com"

    cmd = [
        'gog', 'gmail', 'send',
        '--to', recipient,
        '--subject', subject,
        '--body', body,
        '--attach', file_a,
        '--attach', file_b
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print("Report inviati.")
    else:
        print(f"Errore: {result.stderr}")

if __name__ == "__main__":
    main()
