import subprocess
import datetime
import re

def format_eur(val):
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# --- MAPPA IVA PER NAZIONE ---
vat_rates = {
    'Italia': 1.22,
    'France': 1.20,
    'Deutschland': 1.19,
    'Germania': 1.19,
    'España': 1.21,
    'Spagna': 1.21,
    'Austria': 1.20,
    'Österreich': 1.20,
    'Svizzera': 1.081,
    'Switzerland': 1.081,
    'CH': 1.081,
    'Belgio': 1.21,
    'Belgium': 1.21,
    'Olanda': 1.21,
    'Netherlands': 1.21,
    'Danmark': 1.25,
    'Denmark': 1.25,
    'DEFAULT': 1.21 
}

def get_netto(gross, country):
    c = str(country).strip()
    rate = vat_rates.get(c, vat_rates['DEFAULT'])
    return gross / rate

# --- QUERIES ---

query_main = """
SELECT 
    ot.name AS mp_name,
    CASE 
        WHEN ot.id = 2 THEN 'Sito (ProduceShop)' 
        WHEN ot.is_internal = b'1' AND ot.id != 2 THEN 'Altri Canali Interni' 
        ELSE 'Marketplaces' 
    END AS macro_canale,
    o.delivery_country,
    SUM(o.total) as totale_lordo, 
    COUNT(o.id) as ordini 
FROM sal_order o 
JOIN sal_order_type ot ON o.type_id = ot.id 
WHERE o.date = CURDATE() AND o.is_deleted = 0 
GROUP BY ot.id, macro_canale, o.delivery_country;
"""

query_drop = """
SELECT o.delivery_country, SUM(r.total_price) as lordo
FROM sal_order o
JOIN sal_order_row r ON o.id = r.order_id
WHERE o.date = CURDATE() AND o.is_deleted = 0 AND r.is_deleted = 0
AND EXISTS (
    SELECT 1 FROM dat_product_label pl
    JOIN dat_label l ON pl.label_id = l.id
    WHERE pl.product_id = r.product_id AND LOWER(l.name) LIKE '%drop%'
)
GROUP BY o.delivery_country;
"""

query_drop_suppliers = """
SELECT s.name, o.delivery_country, SUM(r.total_price) as lordo
FROM sal_order o 
JOIN sal_order_row r ON o.id = r.order_id 
JOIN dat_product p ON r.product_id = p.id
JOIN dat_supplier s ON p.supplier_id = s.id
WHERE o.date = CURDATE() AND o.is_deleted = 0 AND r.is_deleted = 0
AND EXISTS (
    SELECT 1 FROM dat_product_label pl
    JOIN dat_label l ON pl.label_id = l.id
    WHERE pl.product_id = r.product_id AND LOWER(l.name) LIKE '%drop%'
)
GROUP BY s.id, s.name, o.delivery_country;
"""

query_nazioni = """
SELECT 
    CASE 
        WHEN delivery_country = 'Francia' THEN 'France' 
        WHEN delivery_country = 'Spagna' THEN 'España' 
        WHEN delivery_country = 'Germania' THEN 'Deutschland'
        ELSE delivery_country 
    END AS nazione, 
    SUM(total) as lordo 
FROM sal_order 
WHERE date=CURDATE() AND is_deleted=0 
GROUP BY nazione;
"""

query_top_10 = """
SELECT 
    r.reference, 
    SUBSTRING(r.description, 1, 45) as desc_short, 
    o.delivery_country,
    SUM(r.total_price) as lordo 
FROM sal_order o 
JOIN sal_order_row r ON o.id = r.order_id 
WHERE o.date = CURDATE() AND o.is_deleted = 0 AND r.is_deleted = 0 
GROUP BY r.reference, desc_short, o.delivery_country;
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

query_yesterday_now = "SELECT delivery_country, SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 1 DAY AND is_deleted = 0 AND TIME(time) <= TIME(NOW()) GROUP BY delivery_country;"
query_yesterday_tot = "SELECT delivery_country, SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 1 DAY AND is_deleted = 0 GROUP BY delivery_country;"
query_lastweek_now = "SELECT delivery_country, SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 7 DAY AND is_deleted = 0 AND TIME(time) <= TIME(NOW()) GROUP BY delivery_country;"
query_lastweek_tot = "SELECT delivery_country, SUM(total) FROM sal_order WHERE date = CURDATE() - INTERVAL 7 DAY AND is_deleted = 0 GROUP BY delivery_country;"

def run_query(q):
    cmd = ["mysql", "-h", "34.38.166.212", "-u", "john", "-p3rmiCyf6d~MZDO41", "kanguro", "-sN", "-e", q]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def sum_net_from_country_group(res_str):
    total_net = 0.0
    for line in res_str.split('\n'):
        if not line: continue
        r = line.split('\t')
        if len(r) == 2:
            total_net += get_netto(float(r[1] if r[1] != 'NULL' else 0), r[0])
    return total_net

# --- FETCH DATA ---
res_main = run_query(query_main)
res_drop = run_query(query_drop)
res_drop_supp = run_query(query_drop_suppliers)
res_nazioni = run_query(query_nazioni)
res_top_10 = run_query(query_top_10)
res_mk_history = run_query(query_mk_history)

y_now = sum_net_from_country_group(run_query(query_yesterday_now))
y_tot = sum_net_from_country_group(run_query(query_yesterday_tot))
w_now = sum_net_from_country_group(run_query(query_lastweek_now))
w_tot = sum_net_from_country_group(run_query(query_lastweek_tot))

# --- PROCESS MAIN ---
grand_total_net = 0.0
total_orders = 0
macros = {"Sito (ProduceShop)": {"tot": 0.0, "ord": 0}, "Marketplaces": {"tot": 0.0, "ord": 0}, "Altri Canali Interni": {"tot": 0.0, "ord": 0}}

# Raggruppamento per MP
mp_dict = {}
active_mps_today = set()

for line in res_main.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) < 5: continue
    name, macro, country, tot_lordo, ord_cnt = r[0], r[1], r[2], float(r[3] if r[3] != 'NULL' else 0), int(r[4] if r[4] != 'NULL' else 0)
    
    tot_netto = get_netto(tot_lordo, country)
    grand_total_net += tot_netto
    total_orders += ord_cnt
    
    if macro in macros:
        macros[macro]["tot"] += tot_netto
        macros[macro]["ord"] += ord_cnt
    
    if macro == "Marketplaces":
        if name not in mp_dict:
            mp_dict[name] = {"tot": 0.0, "ord": 0}
        mp_dict[name]["tot"] += tot_netto
        mp_dict[name]["ord"] += ord_cnt
        if tot_netto > 0:
            active_mps_today.add(name)

mps = [(k, v["tot"], v["ord"]) for k, v in mp_dict.items()]
mps.sort(key=lambda x: x[1], reverse=True)

# --- PROCESS ALERTS ---
historical_mps = set(line for line in res_mk_history.split('\n') if line)
zero_mps = historical_mps - active_mps_today

alert_msg = ""
if zero_mps:
    alert_msg = f"🔴 **ALLARME KPI MARKETPLACE:** Zero vendite oggi per: {', '.join(zero_mps)}"
else:
    alert_msg = "🟢 **Stato Marketplaces:** Nessuna anomalia rilevata"

# --- PROCESS DROP ---
drop_tot_net = sum_net_from_country_group(res_drop)

supp_dict = {}
for line in res_drop_supp.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) == 3:
        sup_name, country, tot_lordo = r[0], r[1], float(r[2] if r[2] != 'NULL' else 0)
        netto = get_netto(tot_lordo, country)
        supp_dict[sup_name] = supp_dict.get(sup_name, 0.0) + netto

drop_suppliers = sorted(supp_dict.items(), key=lambda x: x[1], reverse=True)[:3]

# --- PROCESS NAZIONI ---
nazioni_dict = {}
for line in res_nazioni.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) == 2:
        naz, lordo = r[0], float(r[1] if r[1] != 'NULL' else 0)
        netto = get_netto(lordo, naz)
        nazioni_dict[naz] = nazioni_dict.get(naz, 0.0) + netto

nazioni = sorted(nazioni_dict.items(), key=lambda x: x[1], reverse=True)

# --- PROCESS TOP 10 ---
top10_dict = {}
desc_dict = {}
for line in res_top_10.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) == 4:
        ref, desc, country, lordo = r[0], r[1], r[2], float(r[3] if r[3] != 'NULL' else 0)
        netto = get_netto(lordo, country)
        top10_dict[ref] = top10_dict.get(ref, 0.0) + netto
        desc_dict[ref] = desc

top_10 = sorted([(k, desc_dict[k], v) for k,v in top10_dict.items()], key=lambda x: x[2], reverse=True)[:10]

# --- CALCULATE PROJECTION ---
mult_y = (y_tot / y_now) if y_now > 0 else 1
mult_w = (w_tot / w_now) if w_now > 0 else 1
avg_mult = (mult_y + mult_w) / 2
proj_tot = grand_total_net * avg_mult

# --- BUILD MESSAGE ---
today_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

msg = f"📊 **Resoconto Fatturato (NETTO IVA)** ({today_str})\n\n"
msg += f"{alert_msg}\n\n"
msg += f"💰 **Fatturato Attuale (Netto):** {format_eur(grand_total_net)} ({total_orders} ordini)\n"
msg += f"🔮 **Proiezione Chiusura (Netto):** ~{format_eur(proj_tot)}\n\n"


drop_perc = (drop_tot_net / grand_total_net * 100) if grand_total_net > 0 else 0
msg += f"📦 **Prodotti Drop (Netto):** {format_eur(drop_tot_net)} ({drop_perc:.1f}% del totale)\n"
if drop_suppliers:
    msg += "   *Top 3 Fornitori Drop:*\n"
    for s_name, s_tot in drop_suppliers:
        s_perc = (s_tot / drop_tot_net * 100) if drop_tot_net > 0 else 0
        msg += f"   - {s_name}: {format_eur(s_tot)} ({s_perc:.1f}% del drop)\n"
msg += "\n"

msg += "🛒 **Ripartizione Canali (Sito vs MK) [Netto]:**\n"
for m_name in ["Sito (ProduceShop)", "Marketplaces", "Altri Canali Interni"]:
    mtot = macros[m_name]["tot"]
    mord = macros[m_name]["ord"]
    perc = (mtot / grand_total_net * 100) if grand_total_net > 0 else 0
    if mtot > 0 or m_name == "Sito (ProduceShop)":
        msg += f"• **{m_name}:** {format_eur(mtot)} ({perc:.1f}%) - {mord} ordini\n"

if mps:
    msg += "\n🛍 **Dettaglio Marketplaces [Netto]:**\n"
    for name, tot, ord_cnt in mps:
        if tot > 0:
            msg += f"• {name}: {format_eur(tot)} ({ord_cnt} ordini)\n"

msg += "\n🌍 **Spaccato per Nazione [Netto]:**\n"
for naz, tot in nazioni:
    perc = (tot / grand_total_net * 100) if grand_total_net > 0 else 0
    msg += f"• {naz}: {format_eur(tot)} ({perc:.1f}%)\n"

msg += "\n🔥 **Top 10 Prodotti (per fatturato Netto):**\n"
for i, (ref, desc, tot) in enumerate(top_10, 1):
    msg += f"{i}. {ref} - {desc}... ({format_eur(tot)})\n"

print(msg.strip())
