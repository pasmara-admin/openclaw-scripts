import subprocess
import datetime
import re

def format_eur(val):
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# --- QUERIES ---

query_main = """
SELECT 
    ot.name AS mp_name,
    CASE 
        WHEN ot.id = 2 THEN 'Sito (ProduceShop)' 
        WHEN ot.is_internal = b'1' AND ot.id != 2 THEN 'Altri Canali Interni' 
        ELSE 'Marketplaces' 
    END AS macro_canale,
    SUM(o.total) as totale, 
    COUNT(o.id) as ordini 
FROM sal_order o 
JOIN sal_order_type ot ON o.type_id = ot.id 
WHERE o.date = CURDATE() AND o.is_deleted = 0 
GROUP BY ot.id, macro_canale
ORDER BY totale DESC;
"""

query_drop = """
SELECT SUM(r.total_price)
FROM sal_order o
JOIN sal_order_row r ON o.id = r.order_id
WHERE o.date = CURDATE() AND o.is_deleted = 0 AND r.is_deleted = 0
AND EXISTS (
    SELECT 1 FROM dat_product_label pl
    JOIN dat_label l ON pl.label_id = l.id
    WHERE pl.product_id = r.product_id AND l.name LIKE '%drop%'
);
"""

query_drop_suppliers = """
SELECT s.name, SUM(r.total_price) as tot 
FROM sal_order o 
JOIN sal_order_row r ON o.id = r.order_id 
JOIN dat_product p ON r.product_id = p.id
JOIN dat_supplier s ON p.supplier_id = s.id
WHERE o.date = CURDATE() AND o.is_deleted = 0 AND r.is_deleted = 0
AND EXISTS (
    SELECT 1 FROM dat_product_label pl
    JOIN dat_label l ON pl.label_id = l.id
    WHERE pl.product_id = r.product_id AND l.name LIKE '%drop%'
)
GROUP BY s.id, s.name 
ORDER BY tot DESC 
LIMIT 3;
"""

query_nazioni = """
SELECT 
    CASE 
        WHEN delivery_country = 'Francia' THEN 'France' 
        WHEN delivery_country = 'Spagna' THEN 'España' 
        WHEN delivery_country = 'Germania' THEN 'Deutschland'
        ELSE delivery_country 
    END AS nazione, 
    SUM(total) as tot 
FROM sal_order 
WHERE date=CURDATE() AND is_deleted=0 
GROUP BY nazione 
ORDER BY tot DESC;
"""

query_top_10 = """
SELECT 
    r.reference, 
    SUBSTRING(r.description, 1, 45) as desc_short, 
    SUM(r.total_price) as r_tot 
FROM sal_order o 
JOIN sal_order_row r ON o.id = r.order_id 
WHERE o.date = CURDATE() AND o.is_deleted = 0 AND r.is_deleted = 0 
GROUP BY r.reference, desc_short 
ORDER BY r_tot DESC 
LIMIT 10;
"""

query_mk_history = """
SELECT DISTINCT ot.name
FROM sal_order o 
JOIN sal_order_type ot ON o.type_id = ot.id 
WHERE o.date >= CURDATE() - INTERVAL 3 DAY 
AND o.date < CURDATE()
AND o.is_deleted = 0 
AND ot.is_internal = b'0' AND ot.id != 2;
"""

# Santorini KPI tracking using the base reference logic to group variants
# Changing to use from Jan 1st 2026 to Mar 9th for the "before" average
query_santorini = """
SELECT 
    CASE
        WHEN r.reference LIKE '%20PZ%' THEN 'Stock 20'
        WHEN r.reference LIKE '%4PZ%' THEN '4 Pezzi'
        WHEN r.reference LIKE '%2PZ%' THEN '2 Pezzi'
        WHEN r.reference LIKE 'SA800TEX%' THEN '1 Pezzo'
        ELSE 'Altro'
    END as gruppo,
    SUM(CASE WHEN o.date BETWEEN '2026-03-03' AND '2026-03-09' THEN r.qty ELSE 0 END) as qty_before,
    SUM(CASE WHEN o.date >= '2026-03-10' THEN r.qty ELSE 0 END) as qty_after,
    SUM(CASE WHEN o.date = '2026-03-04' THEN r.qty ELSE 0 END) as qty_last_week_same_day,
    SUM(CASE WHEN o.date = CURDATE() THEN r.qty ELSE 0 END) as qty_today
FROM sal_order o
JOIN sal_order_row r ON o.id = r.order_id
WHERE r.reference LIKE 'SA800TEX%' AND r.reference NOT LIKE '%20PZ%'
AND o.is_deleted = 0 AND r.is_deleted = 0
GROUP BY gruppo;
"""

query_yesterday_now = "SELECT SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 1 DAY AND is_deleted = 0 AND TIME(time) <= TIME(NOW());"
query_yesterday_tot = "SELECT SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 1 DAY AND is_deleted = 0;"
query_lastweek_now = "SELECT SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 7 DAY AND is_deleted = 0 AND TIME(time) <= TIME(NOW());"
query_lastweek_tot = "SELECT SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 7 DAY AND is_deleted = 0;"

def run_query(q):
    cmd = ["mysql", "-h", "34.38.166.212", "-u", "john", "-p3rmiCyf6d~MZDO41", "kanguro", "-sN", "-e", q]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

# --- FETCH DATA ---

res_main = run_query(query_main)
res_drop = run_query(query_drop)
res_drop_supp = run_query(query_drop_suppliers)
res_nazioni = run_query(query_nazioni)
res_top_10 = run_query(query_top_10)
res_mk_history = run_query(query_mk_history)
res_santorini = run_query(query_santorini)

y_now = float(run_query(query_yesterday_now) or 0)
y_tot = float(run_query(query_yesterday_tot) or 0)
w_now = float(run_query(query_lastweek_now) or 0)
w_tot = float(run_query(query_lastweek_tot) or 0)

# --- PROCESS MAIN ---
grand_total = 0.0
total_orders = 0
macros = {"Sito (ProduceShop)": {"tot": 0.0, "ord": 0}, "Marketplaces": {"tot": 0.0, "ord": 0}, "Altri Canali Interni": {"tot": 0.0, "ord": 0}}
mps = []
active_mps_today = set()

for line in res_main.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) < 4: continue
    name, macro, tot, ord_cnt = r[0], r[1], float(r[2] if r[2] != 'NULL' else 0), int(r[3] if r[3] != 'NULL' else 0)
    
    grand_total += tot
    total_orders += ord_cnt
    if macro in macros:
        macros[macro]["tot"] += tot
        macros[macro]["ord"] += ord_cnt
    else:
        macros[macro] = {"tot": tot, "ord": ord_cnt}
    if macro == "Marketplaces":
        mps.append((name, tot, ord_cnt))
        if tot > 0:
            active_mps_today.add(name)

# --- PROCESS ALERTS ---
historical_mps = set(line for line in res_mk_history.split('\n') if line)
zero_mps = historical_mps - active_mps_today

alert_msg = ""
if zero_mps:
    alert_msg = f"🔴 **ALLARME KPI MARKETPLACE:** Zero vendite oggi per: {', '.join(zero_mps)}"
else:
    alert_msg = "🟢 **Stato Marketplaces:** Nessuna anomalia rilevata"

# --- PROCESS DROP ---
drop_tot = float(res_drop) if res_drop and res_drop != 'NULL' else 0.0
drop_suppliers = []
for line in res_drop_supp.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) == 2:
        drop_suppliers.append((r[0], float(r[1] if r[1] != 'NULL' else 0)))

# --- PROCESS NAZIONI ---
nazioni = []
for line in res_nazioni.split('\n'):
    if not line: continue
    r = line.split('\t')
    nazioni.append((r[0], float(r[1] if r[1] != 'NULL' else 0)))

# --- PROCESS TOP 10 ---
top_10 = []
for line in res_top_10.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) == 3:
        top_10.append((r[0], r[1], float(r[2] if r[2] != 'NULL' else 0)))

# --- PROCESS SANTORINI ---
santorini_data = []

today = datetime.datetime.now().date()
price_change_date = datetime.date(2026, 3, 10)
days_after = (today - price_change_date).days + 1
days_before = 7

for line in res_santorini.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) >= 5 and r[0] != 'Altro':
        gruppo = r[0]
        qty_before = float(r[1] if r[1] != 'NULL' else 0)
        qty_after = float(r[2] if r[2] != 'NULL' else 0)
        qty_last_week = float(r[3] if r[3] != 'NULL' else 0)
        qty_today = float(r[4] if r[4] != 'NULL' else 0)
        
        avg_before = qty_before / days_before
        avg_after = qty_after / days_after
        
        diff = 0
        if avg_before > 0:
            diff = ((avg_after - avg_before) / avg_before) * 100
            
        santorini_data.append({
            'name': gruppo,
            'avg_before': avg_before,
            'avg_after': avg_after,
            'diff': diff,
            'last_week': qty_last_week,
            'today': qty_today
        })

# --- CALCULATE PROJECTION ---
mult_y = (y_tot / y_now) if y_now > 0 else 1
mult_w = (w_tot / w_now) if w_now > 0 else 1
avg_mult = (mult_y + mult_w) / 2
proj_tot = grand_total * avg_mult

# --- BUILD MESSAGE ---
today_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

msg = f"📊 **Resoconto Fatturato** ({today_str})\n\n"
msg += f"{alert_msg}\n\n"
msg += f"💰 **Fatturato Attuale:** {format_eur(grand_total)} ({total_orders} ordini)\n"
msg += f"🔮 **Proiezione Chiusura:** ~{format_eur(proj_tot)}\n\n"

if santorini_data:
    msg += f"📈 **KPI Santorini (Medie YTD vs dal cambio prezzo):**\n"
    msg += f"   *(Nota: media ultimi 7gg pre-cambio vs media post-cambio, e confronto oggi vs stesso giorno settimana scorsa)*\n"
    for s in sorted(santorini_data, key=lambda x: x['name']):
        diff_str = f"+{s['diff']:.1f}%" if s['diff'] > 0 else f"{s['diff']:.1f}%"
        msg += f"   • {s['name']}: {s['avg_after']:.1f} pz/gg (vs {s['avg_before']:.1f} prec.) -> {diff_str} | [Oggi: {s['today']:.0f} pz vs {s['last_week']:.0f} pz mercoledì scorso]\n"
    msg += "\n"


drop_perc = (drop_tot / grand_total * 100) if grand_total > 0 else 0
msg += f"📦 **Prodotti Drop:** {format_eur(drop_tot)} ({drop_perc:.1f}% del totale)\n"
if drop_suppliers:
    msg += "   *Top 3 Fornitori Drop:*\n"
    for s_name, s_tot in drop_suppliers:
        s_perc = (s_tot / drop_tot * 100) if drop_tot > 0 else 0
        msg += f"   - {s_name}: {format_eur(s_tot)} ({s_perc:.1f}% del drop)\n"
msg += "\n"

msg += "🛒 **Ripartizione Canali (Sito vs MK):**\n"
for m_name in ["Sito (ProduceShop)", "Marketplaces", "Altri Canali Interni"]:
    mtot = macros[m_name]["tot"]
    mord = macros[m_name]["ord"]
    perc = (mtot / grand_total * 100) if grand_total > 0 else 0
    if mtot > 0 or m_name == "Sito (ProduceShop)":
        msg += f"• **{m_name}:** {format_eur(mtot)} ({perc:.1f}%) - {mord} ordini\n"

if mps:
    msg += "\n🛍 **Dettaglio Marketplaces:**\n"
    for name, tot, ord_cnt in mps:
        if tot > 0:
            msg += f"• {name}: {format_eur(tot)} ({ord_cnt} ordini)\n"

msg += "\n🌍 **Spaccato per Nazione:**\n"
for naz, tot in nazioni:
    perc = (tot / grand_total * 100) if grand_total > 0 else 0
    msg += f"• {naz}: {format_eur(tot)} ({perc:.1f}%)\n"

msg += "\n🔥 **Top 10 Prodotti (per fatturato):**\n"
for i, (ref, desc, tot) in enumerate(top_10, 1):
    msg += f"{i}. {ref} - {desc}... ({format_eur(tot)})\n"

print(msg.strip())
