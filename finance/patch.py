with open('generate_fatturato.py', 'r') as f:
    content = f.read()

import re

# Patch query
new_query = """
query_santorini = \"\"\"
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
\"\"\"
"""
content = re.sub(r'query_santorini = """(.*?)"""', new_query.strip(), content, flags=re.DOTALL)

# Patch processing
old_proc = """days_after = (today - price_change_date).days + 1
# From Jan 1st 2026 to Mar 9th 2026 = 31 (Jan) + 28 (Feb) + 9 (Mar) = 68 days
start_date = datetime.date(2026, 1, 1)
end_before_date = datetime.date(2026, 3, 9)
days_before = (end_before_date - start_date).days + 1

for line in res_santorini.split('\\n'):
    if not line: continue
    r = line.split('\\t')
    if len(r) == 3 and r[0] != 'Altro':
        gruppo = r[0]
        qty_before = float(r[1] if r[1] != 'NULL' else 0)
        qty_after = float(r[2] if r[2] != 'NULL' else 0)
        
        avg_before = qty_before / days_before
        avg_after = qty_after / days_after
        
        diff = 0
        if avg_before > 0:
            diff = ((avg_after - avg_before) / avg_before) * 100
            
        santorini_data.append({
            'name': gruppo,
            'avg_before': avg_before,
            'avg_after': avg_after,
            'diff': diff
        })"""

new_proc = """days_after = (today - price_change_date).days + 1
days_before = 7

for line in res_santorini.split('\\n'):
    if not line: continue
    r = line.split('\\t')
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
        })"""

content = content.replace(old_proc, new_proc)

# Patch message
old_msg = """msg += f"   *(Nota: storico dal 1 Gen, fisiologicamente basso causa stagionalità)*\\n"
    for s in sorted(santorini_data, key=lambda x: x['name']):
        diff_str = f"+{s['diff']:.1f}%" if s['diff'] > 0 else f"{s['diff']:.1f}%"
        msg += f"   • {s['name']}: {s['avg_after']:.1f} pz/gg (vs {s['avg_before']:.1f} prec.) -> {diff_str}\\n"
    msg += "\\n\""""

new_msg = """msg += f"   *(Nota: media ultimi 7gg pre-cambio vs media post-cambio, e confronto oggi vs stesso giorno settimana scorsa)*\\n"
    for s in sorted(santorini_data, key=lambda x: x['name']):
        diff_str = f"+{s['diff']:.1f}%" if s['diff'] > 0 else f"{s['diff']:.1f}%"
        msg += f"   • {s['name']}: {s['avg_after']:.1f} pz/gg (vs {s['avg_before']:.1f} prec.) -> {diff_str} | [Oggi: {s['today']:.0f} pz vs {s['last_week']:.0f} pz mercoledì scorso]\\n"
    msg += "\\n"
"""

content = content.replace(old_msg, new_msg)

with open('generate_fatturato.py', 'w') as f:
    f.write(content)
