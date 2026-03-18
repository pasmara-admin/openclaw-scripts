import mysql.connector
from datetime import datetime, timedelta

def get_data():
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

def format_report(data):
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
    report = f"🛒 **Analisi Tasso di Abbandono Carrello ({yesterday_str})**\n\n"
    report += "Dati riferiti all'intera giornata di ieri, confrontati con la media degli ultimi 7 e 30 giorni:\n\n"
    
    for country, stats in data.items():
        y_rate = (stats['yesterday']['abandoned'] / stats['yesterday']['total'] * 100) if stats['yesterday']['total'] > 0 else 0
        s_rate = (stats['prev_7d']['abandoned'] / stats['prev_7d']['total'] * 100) if stats['prev_7d']['total'] > 0 else 0
        m_rate = (stats['prev_30d']['abandoned'] / stats['prev_30d']['total'] * 100) if stats['prev_30d']['total'] > 0 else 0
        
        # Utilizzo una formattazione testuale per Telegram (evito tabelle markdown pure)
        report += f"📍 **{country}**\n"
        report += f"• Ieri: **{y_rate:.1f}%**\n"
        report += f"• Media 7gg: {s_rate:.1f}%\n"
        report += f"• Media 30gg: {m_rate:.1f}%\n\n"
    
    return report

if __name__ == "__main__":
    data = get_data()
    print(format_report(data))
