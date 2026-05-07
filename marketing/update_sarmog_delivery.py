import sys
import os
import subprocess

def run_query(query):
    cmd = [
        'mysql', '--skip-ssl-verify-server-cert',
        '-h', '62.84.190.199',
        '-u', 'john',
        '-pqARa6aRozi6I',
        'produceshop',
        '-e', query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def update_sarmog_delivery():
    print("🚀 Inizio aggiornamento delivery date per Sarmog (10 giorni)...")
    
    # 1. Trova ID Manufacturer per Sarmog
    m_out = run_query("SELECT id_manufacturer FROM ps_manufacturer WHERE name LIKE '%Sarmog%';")
    if '84' not in m_out:
        print("❌ Errore: ID Manufacturer Sarmog non trovato.")
        return
    
    m_id = 84
    
    # 2. Genera la query di INSERT/UPDATE
    # Usiamo INSERT INTO ... ON DUPLICATE KEY UPDATE per gestire sia nuovi inserimenti che aggiornamenti
    query = f"""
    INSERT INTO ps_delivery_product (id_product, id_product_attribute, days)
    SELECT p.id_product, IFNULL(pa.id_product_attribute, 0), 10
    FROM ps_product p
    LEFT JOIN ps_product_attribute pa ON p.id_product = pa.id_product
    WHERE p.id_manufacturer = {m_id}
    ON DUPLICATE KEY UPDATE days = 10;
    """
    
    print("📝 Query generata. Eseguo...")
    # Nota: Come John Marketing, accedo in Read-Only di default ma posso proporre la query.
    # Se Damiano (Papà) ha dato il via libera ("Se va bene digli di memorizzare lo script"), 
    # procedo a creare lo script eseguibile.
    
    with open('/root/.openclaw/workspace-shared/openclaw-scripts/marketing/update_sarmog_delivery.sql', 'w') as f:
        f.write(query)
    
    print(f"✅ Query salvata in /root/.openclaw/workspace-shared/openclaw-scripts/marketing/update_sarmog_delivery.sql")
    print("\nPROPOSTA QUERY SQL:")
    print("-" * 30)
    print(query.strip())
    print("-" * 30)

if __name__ == "__main__":
    update_sarmog_delivery()
