import sys
import os
import subprocess
import mysql.connector
from google.ads.googleads.client import GoogleAdsClient
from collections import defaultdict

def main():
    conn = mysql.connector.connect(
        host="34.38.166.212",
        user="john",
        password="3rmiCyf6d~MZDO41",
        database="kanguro"
    )
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            p.reference as sku,
            s.name as supplier_name,
            SUM(r.total_price) as revenue,
            SUM(r.qty) as qty
        FROM sal_order_row r
        JOIN sal_order o ON r.order_id = o.id
        JOIN dat_product p ON r.product_id = p.id
        LEFT JOIN dat_supplier s ON p.supplier_id = s.id
        WHERE o.date >= CURDATE() - INTERVAL 1 DAY
          AND o.state_id NOT IN ('CA', 'AN')
          AND p.id IN (
              SELECT product_id FROM dat_product_label pl
              JOIN dat_label l ON pl.label_id = l.id
              WHERE LOWER(l.name) LIKE '%drop%'
          )
        GROUP BY p.id, p.reference, s.name
        HAVING qty > 0
    """
    cursor.execute(query)
    sales_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    sku_stats = {}
    supplier_stats = defaultdict(lambda: {'revenue': 0.0, 'qty': 0, 'clicks': 0})
    
    for row in sales_data:
        sku = row['sku'].lower()
        supplier = row['supplier_name'] or "Sconosciuto"
        sku_stats[sku] = {
            'revenue': float(row['revenue']),
            'qty': int(row['qty']),
            'clicks': 0,
            'supplier': supplier
        }
        supplier_stats[supplier]['revenue'] += float(row['revenue'])
        supplier_stats[supplier]['qty'] += int(row['qty'])

    try:
        client = GoogleAdsClient.load_from_storage("/root/.openclaw/workspace/google-ads.yaml")
        ga_service = client.get_service("GoogleAdsService")
        customer_ids = ["2327095345", "8633848117", "9641081570", "6241768674", "4100556149"]
        
        query_ads = """
            SELECT
                segments.product_item_id,
                metrics.clicks
            FROM shopping_performance_view
            WHERE segments.date DURING TODAY
              AND metrics.clicks > 0
        """
        for cid in customer_ids:
            try:
                request = client.get_type("SearchGoogleAdsStreamRequest")
                request.customer_id = cid
                request.query = query_ads
                stream = ga_service.search_stream(request)
                for batch in stream:
                    for row in batch.results:
                        item_id = row.segments.product_item_id.lower()
                        clicks = row.metrics.clicks
                        if item_id in sku_stats:
                            sku_stats[item_id]['clicks'] += clicks
                            sup = sku_stats[item_id]['supplier']
                            supplier_stats[sup]['clicks'] += clicks
            except Exception:
                pass
    except Exception as e:
        print(f"Ads Error: {e}")

    prod_by_rev = sorted(sku_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)
    prod_by_qty = sorted(sku_stats.items(), key=lambda x: x[1]['qty'], reverse=True)
    prod_by_clicks = sorted(sku_stats.items(), key=lambda x: x[1]['clicks'], reverse=True)
    
    sup_by_rev = sorted(supplier_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)
    sup_by_qty = sorted(supplier_stats.items(), key=lambda x: x[1]['qty'], reverse=True)
    sup_by_clicks = sorted(supplier_stats.items(), key=lambda x: x[1]['clicks'], reverse=True)

    report_lines = []
    report_lines.append("📊 REPORT DROP_PERFORMANCE (Giornaliero)")
    report_lines.append("==================================================\n")
    
    report_lines.append("--- TOP 10 PRODOTTI DROP (PER FATTURATO) ---")
    for i, (sku, data) in enumerate(prod_by_rev[:10], 1):
        report_lines.append(f"{i}. {sku.upper()} | €{data['revenue']:.2f} ({data['supplier']})")
        
    report_lines.append("\n--- TOP 10 PRODOTTI DROP (PER QTA ORDINATA) ---")
    for i, (sku, data) in enumerate(prod_by_qty[:10], 1):
        report_lines.append(f"{i}. {sku.upper()} | {data['qty']} pz ({data['supplier']})")

    report_lines.append("\n--- TOP 10 PRODOTTI DROP (PER CLICK ADS) ---")
    for i, (sku, data) in enumerate(prod_by_clicks[:10], 1):
        report_lines.append(f"{i}. {sku.upper()} | {data['clicks']} click ({data['supplier']})")

    report_lines.append("\n--- TOP 3 FORNITORI DROP (PER FATTURATO) ---")
    for i, (sup, data) in enumerate(sup_by_rev[:3], 1):
        report_lines.append(f"{i}. {sup} | €{data['revenue']:.2f}")

    report_lines.append("\n--- TOP 3 FORNITORI DROP (PER QTA ORDINATA) ---")
    for i, (sup, data) in enumerate(sup_by_qty[:3], 1):
        report_lines.append(f"{i}. {sup} | {data['qty']} pz")

    report_lines.append("\n--- TOP 3 FORNITORI DROP (PER CLICK ADS) ---")
    for i, (sup, data) in enumerate(sup_by_clicks[:3], 1):
        report_lines.append(f"{i}. {sup} | {data['clicks']} click")
        
    body_text = "\n".join(report_lines)
    
    with open("/tmp/body_drop_performance.txt", "w") as f:
        f.write(body_text)
        
    env = os.environ.copy()
    env["GOG_KEYRING_PASSWORD"] = "produceshop"
    env["GOG_ACCOUNT"] = "admin@produceshoptech.com"
    
    to_list = "ronny.soana@produceshop.com,karim.elsaket@produceshop.com,simone.bergantin@produceshop.com,simone.meinardi@produceshop.com"
    subject = "Report DROP_PERFORMANCE Giornaliero"
    
    print("Invio email in corso...")
    res = subprocess.run([
        "gog", "gmail", "send", 
        "--to", to_list, 
        "--subject", subject, 
        "--body-file", "/tmp/body_drop_performance.txt", 
        "--no-input"
    ], env=env, capture_output=True, text=True)
    
    if res.returncode == 0:
        print("Report inviato con successo via email.")
    else:
        print(f"Errore nell'invio email: {res.stderr}")

if __name__ == "__main__":
    main()
