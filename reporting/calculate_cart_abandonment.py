import mysql.connector
from datetime import datetime, timedelta

def get_db_data():
    config = {
        'host': '62.84.190.199',
        'user': 'john',
        'password': 'qARa6aRozi6I',
        'database': 'produceshop'
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    shops = {
        'Italia': 1,
        'Francia': 5,
        'Germania': 4,
        'Spagna': 6,
        'Austria': 9
    }
    
    results = {}
    
    for country, shop_id in shops.items():
        # Ieri (rispetto ad oggi)
        cursor.execute(f"""
            SELECT 
                COUNT(id_cart) as total,
                SUM(CASE WHEN id_cart NOT IN (SELECT id_cart FROM ps_orders) THEN 1 ELSE 0 END) as abandoned
            FROM ps_cart 
            WHERE id_shop = {shop_id} 
              AND date_add >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) 
              AND date_add < CURDATE()
        """)
        yesterday = cursor.fetchone()
        
        # Ultimi 7 giorni (escluso oggi)
        cursor.execute(f"""
            SELECT 
                COUNT(id_cart) as total,
                SUM(CASE WHEN id_cart NOT IN (SELECT id_cart FROM ps_orders) THEN 1 ELSE 0 END) as abandoned
            FROM ps_cart 
            WHERE id_shop = {shop_id} 
              AND date_add >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
              AND date_add < CURDATE()
        """)
        prev_7d = cursor.fetchone()

        # Ultimi 30 giorni (escluso oggi)
        cursor.execute(f"""
            SELECT 
                COUNT(id_cart) as total,
                SUM(CASE WHEN id_cart NOT IN (SELECT id_cart FROM ps_orders) THEN 1 ELSE 0 END) as abandoned
            FROM ps_cart 
            WHERE id_shop = {shop_id} 
              AND date_add >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) 
              AND date_add < CURDATE()
        """)
        prev_30d = cursor.fetchone()
        
        results[country] = {
            'yesterday': yesterday,
            'prev_7d': prev_7d,
            'prev_30d': prev_30d
        }
    
    conn.close()
    return results

def format_report(db_data, marketing_data=None):
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
    report = f"🛒 **REPORT PERFORMANCE & ABBANDONO ({yesterday_str})**\n\n"
    report += "Dati riferiti all'intera giornata di ieri (PreSales Traffic vs Database):\n\n"
    
    for country, stats in db_data.items():
        y_rate = (stats['yesterday']['abandoned'] / stats['yesterday']['total'] * 100) if stats['yesterday']['total'] > 0 else 0
        s_rate = (stats['prev_7d']['abandoned'] / stats['prev_7d']['total'] * 100) if stats['prev_7d']['total'] > 0 else 0
        m_rate = (stats['prev_30d']['abandoned'] / stats['prev_30d']['total'] * 100) if stats['prev_30d']['total'] > 0 else 0
        
        report += f"📍 **{country}**\n"
        report += f"• Abbandono Ieri: **{y_rate:.1f}%** (7gg: {s_rate:.1f}% | 30gg: {m_rate:.1f}%)\n"
        
        if marketing_data and country in marketing_data:
            m_stats = marketing_data[country]
            report += f"• **Conversion Rate (PreSales): {m_stats['cr']}**\n"
            report += f"• Sessioni PreSales: {m_stats['sessions']} | Ordini: {m_stats['orders']}\n"
        
        report += "\n"
    
    report += "--- \n*Nota: Il Conversion Rate è calcolato sul traffico PreSales (escl. assistenza/post-vendita).* "
    return report

if __name__ == "__main__":
    # Dati ricevuti da John Marketing per il 17/03/2026
    # In produzione questi verranno recuperati tramite API o script dedicato
    marketing_data = {
        'Italia': {'sessions': 13680, 'orders': 48, 'cr': '1,87%'},
        'Germania': {'sessions': 8973, 'orders': 11, 'cr': '0,37%'},
        'Francia': {'sessions': 5203, 'orders': 12, 'cr': '1,56%'},
        'Spagna': {'sessions': 2243, 'orders': 7, 'cr': '2,50%'},
        'Austria': {'sessions': 561, 'orders': 9, 'cr': '3,03%'}
    }
    
    db_data = get_db_data()
    print(format_report(db_data, marketing_data))
