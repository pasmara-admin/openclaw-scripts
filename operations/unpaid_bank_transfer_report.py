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

def send_email(df, recipient_email):
    # This is a placeholder for the email sending logic. 
    # In a real scenario, SMTP details from environment or config would be used.
    # For now, we'll simulate the output.
    filename = f"report_bonifici_pendenti_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    print(f"Report generated: {filename}")
    print(f"Simulating email sent to {recipient_email} with {len(df)} records.")
    # Clean up
    # os.remove(filename)

if __name__ == "__main__":
    report_df = get_unpaid_bank_transfers()
    if report_df is not None and not report_df.empty:
        # Example recipient from user request
        send_email(report_df, "ivan.cianci@produceshop.com")
    else:
        print("No pending bank transfers found matching criteria.")
