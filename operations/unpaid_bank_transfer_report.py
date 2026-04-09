#!/usr/bin/env python3
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Database configuration
db_config = {
    'host': '34.38.166.212',
    'user': 'john',
    'password': '3rmiCyf6d~MZDO41',
    'database': 'kanguro'
}

def get_unpaid_bank_transfers():
    try:
        conn = mysql.connector.connect(**db_config)
        query = """
        SELECT 
            number AS 'Ordine', 
            date AS 'Data', 
            customer_name AS 'Cliente', 
            customer_email AS 'Email', 
            customer_tel AS 'Telefono',
            total AS 'Totale', 
            payment_method_name AS 'Metodo Pagamento'
        FROM sal_order 
        WHERE payment_method_name IN ('Bonifico bancario', 'Bank Transfer') 
          AND payment_state_id NOT IN ('99') 
          AND date < DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
          AND total > 500 
          AND is_deleted = 0
        ORDER BY date DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def send_email(df, recipient_emails):
    filename = f"report_bonifici_pendenti_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    
    # Using gog CLI for sending email
    body = "Ciao,\\n\\nin allegato il report degli ordini con pagamento in bonifico non saldati da più di 7 giorni con importo superiore a 500 Euro.\\n\\nJohn Operations"
    subject = "Report Settimanale Ordini Bonifico Pendenti"
    
    cmd = f'source /root/.openclaw/workspace-shared/setup_gog_env.sh && export GOG_KEYRING_PASSWORD="produceshop" && export GOG_ACCOUNT="admin@produceshoptech.com" && gog gmail send --to "{recipient_emails}" --subject "{subject}" --body "{body}" --attach "{filename}"'
    
    try:
        os.system(cmd)
        print(f"Email sent successfully to {recipient_emails}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    report_df = get_unpaid_bank_transfers()
    if report_df is not None and not report_df.empty:
        send_email(report_df, "baldassare.gulotta@produceshop.com, support@produceshop.com, ivan.cianci@produceshop.com")
    else:
        print("No pending bank transfers found matching criteria.")
