import mysql.connector
import csv
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Database connections
db_produceshop = {
    "host": "62.84.190.199",
    "user": "john",
    "password": "qARa6aRozi6I",
    "database": "produceshop"
}

db_kanguro = {
    "host": "34.38.166.212",
    "user": "john",
    "password": "3rmiCyf6d~MZDO41",
    "database": "kanguro"
}

def is_business_day(date, holidays):
    # Sabato = 5, Domenica = 6
    if date.weekday() >= 5:
        return False
    if date in holidays:
        return False
    return True

def add_business_days(start_date, days_to_add, holidays):
    current_date = start_date
    added_days = 0
    while added_days < days_to_add:
        current_date += datetime.timedelta(days=1)
        if is_business_day(current_date, holidays):
            added_days += 1
    return current_date

def get_holidays():
    # Definiamo i giorni rossi standard per il 2026 (Italia)
    year = 2026
    holidays = [
        datetime.date(year, 1, 1),   # Capodanno
        datetime.date(year, 1, 6),   # Epifania
        datetime.date(year, 4, 5),   # Pasqua
        datetime.date(year, 4, 6),   # Lunedì dell'Angelo
        datetime.date(year, 4, 25),  # Liberazione
        datetime.date(year, 5, 1),   # Lavoro
        datetime.date(year, 6, 2),   # Repubblica
        datetime.date(year, 8, 15),  # Ferragosto
        datetime.date(year, 11, 1),  # Ognissanti
        datetime.date(year, 12, 8),  # Immacolata
        datetime.date(year, 12, 25), # Natale
        datetime.date(year, 12, 26), # S. Stefano
    ]
    return holidays

def get_delivery_times():
    conn = mysql.connector.connect(**db_produceshop)
    cursor = conn.cursor(dictionary=True)
    
    # Prendi shop delivery (Italia = 1)
    cursor.execute("SELECT days FROM ps_delivery_shop WHERE id_shop = 1")
    row = cursor.fetchone()
    shop_days = row['days'] if row else 0
    
    # Prendi tutti i tempi prodotto (per SKU/reference)
    cursor.execute("""
        SELECT p.id_product, p.reference as p_ref, pa.id_product_attribute, pa.reference as pa_ref 
        FROM ps_product p
        LEFT JOIN ps_product_attribute pa ON p.id_product = pa.id_product
    """)
    ref_rows = cursor.fetchall()
    
    ref_to_ids = {}
    for r in ref_rows:
        if r['pa_ref']:
            ref_to_ids[r['pa_ref']] = (r['id_product'], r['id_product_attribute'])
        if r['p_ref']:
            ref_to_ids[r['p_ref']] = (r['id_product'], 0)
            
    cursor.execute("SELECT id_product, id_product_attribute, days FROM ps_delivery_product")
    delivery_rows = cursor.fetchall()
    
    id_delivery_map = {}
    for d in delivery_rows:
        pid = d['id_product']
        aid = d['id_product_attribute']
        if pid not in id_delivery_map:
            id_delivery_map[pid] = {}
        id_delivery_map[pid][aid] = d['days']
        
    final_delivery_map = {}
    for ref, (pid, aid) in ref_to_ids.items():
        if pid in id_delivery_map:
            if aid > 0 and aid in id_delivery_map[pid]:
                final_delivery_map[ref] = id_delivery_map[pid][aid]
            elif 0 in id_delivery_map[pid]:
                final_delivery_map[ref] = id_delivery_map[pid][0]
            else:
                final_delivery_map[ref] = 0
        else:
            final_delivery_map[ref] = 0
            
    conn.close()
    return shop_days, final_delivery_map

def run_analysis():
    shop_days, delivery_map = get_delivery_times()
    holidays = get_holidays()
    today = datetime.date.today()
    
    conn_k = mysql.connector.connect(**db_kanguro)
    cursor_k = conn_k.cursor(dictionary=True)
    
    cursor_k.execute("""
        SELECT 
            s.number, 
            s.date AS shipment_date, 
            s.transmission_date,
            s.customer_name, 
            s.product_reference, 
            sol.name as order_state_name,
            so.state_id as order_state_id,
            so.date AS order_date,
            w.display_name AS warehouse_name,
            c.name AS carrier_name,
            cn.name AS country_name,
            psl.name AS post_sales_state_name
        FROM lgs_shipment s 
        JOIN sal_order so ON s.order_id = so.id 
        JOIN sal_order_state_lang sol ON so.state_id = sol.state_id AND sol.lang_id = 1
        JOIN inv_warehouse w ON s.warehouse_id = w.id
        LEFT JOIN lgs_carrier c ON s.calc_carrier_id = c.id
        LEFT JOIN dat_country_lang cn ON s.delivery_country_id = cn.id AND cn.lang_id = 1
        LEFT JOIN lgs_shipment_post p ON s.number = p.shipment_number AND p.is_deleted = 0
        LEFT JOIN lgs_shipment_post_state_lang psl ON p.state_id = psl.state_id AND psl.lang_id = 1
        WHERE s.is_deleted = 0 
            AND s.tracking_id IS NULL 
            AND s.state_id != '99' 
            AND so.state_id != '00'
    """)
    
    shipments = cursor_k.fetchall()
    
    grouped = {}
    for s in shipments:
        num = s['number']
        if num not in grouped:
            transmission_dt = s['transmission_date']
            extra_day_cutoff = 0
            time_str = ""
            if transmission_dt:
                time_str = transmission_dt.strftime("%H:%M:%S")
                if transmission_dt.hour >= 13:
                    extra_day_cutoff = 1
            
            grouped[num] = {
                'number': num,
                'shipment_date': s['shipment_date'],
                'transmission_time': time_str,
                'extra_day_cutoff': extra_day_cutoff,
                'order_date': s['order_date'],
                'warehouse': s['warehouse_name'],
                'carrier': s['carrier_name'],
                'country': s['country_name'],
                'customer': s['customer_name'],
                'state': s['order_state_name'],
                'post_sales_state': psl.name if 'psl' in locals() and psl else s.get('post_sales_state_name'),
                'max_prep_days': 0,
                'skus': []
            }
        
        prep_days = delivery_map.get(s['product_reference'], 0)
        if prep_days > grouped[num]['max_prep_days']:
            grouped[num]['max_prep_days'] = prep_days
        
        grouped[num]['skus'].append(f"{s['product_reference']} ({prep_days}d)")

    final_list = []
    for num, data in grouped.items():
        total_business_days_to_wait = data['max_prep_days'] + shop_days + 1 + data['extra_day_cutoff']
        limit_date = add_business_days(data['shipment_date'], total_business_days_to_wait, holidays)
        
        if today > limit_date:
            delay_days = (today - limit_date).days
            final_list.append({
                'Numero Spedizione': data['number'],
                'Data Ordine': data['order_date'],
                'Data Invio Flussi': data['shipment_date'],
                'Ora Invio Flussi': data['transmission_time'],
                'Magazzino': data['warehouse'],
                'Corriere': data['carrier'],
                'Giorni di Ritardo': delay_days,
                'Ritardo aggiuntivo fornitore': data['max_prep_days'],
                'Limite Attesa': limit_date,
                'Nazione': data['country'],
                'Stato Ordine': data['state'],
                'Stato Post-Sales': data['post_sales_state'],
                'Cliente': data['customer'],
                'SKUs': ", ".join(data['skus'])
            })

    report_path = f'/tmp/report_no_tracking_{today.strftime("%Y%m%d")}.csv'
    if final_list:
        with open(report_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=final_list[0].keys(), delimiter=';')
            writer.writeheader()
            writer.writerows(final_list)
    else:
        with open(report_path, 'w', newline='', encoding='utf-8-sig') as f:
            f.write("Nessun ritardo trovato")
        
    conn_k.close()
    return len(final_list), report_path

def send_email(count, report_path):
    sender_email = "john@produceshop.com"
    receiver_email = "ivan.cianci@produceshop.com"
    
    msg = MIMEMultipart()
    msg['From'] = f"John Operations <{sender_email}>"
    msg['To'] = receiver_email
    msg['Subject'] = f"Report Tracking Delays - {datetime.date.today().strftime('%d/%m/%Y')} ({count} anomalie)"

    body = f"Ciao Ivan,\n\nIn allegato trovi il report aggiornato ad oggi delle spedizioni senza tracking oltre le 48 ore lavorative.\n\nTotale anomalie riscontrate: {count}\n\nUn saluto,\nJohn Operations"
    msg.attach(MIMEText(body, 'plain'))

    if os.path.exists(report_path):
        with open(report_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(report_path)}",
            )
            msg.attach(part)

    try:
        with smtplib.SMTP("127.0.0.1") as server:
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

if __name__ == "__main__":
    count, path = run_analysis()
    success = send_email(count, path)
    print(f"Count: {count}, Success: {success}")
