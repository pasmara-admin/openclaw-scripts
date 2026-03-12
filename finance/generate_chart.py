import subprocess
import datetime
import matplotlib.pyplot as plt

def run_query(q):
    cmd = ["mysql", "-h", "34.38.166.212", "-u", "john", "-p3rmiCyf6d~MZDO41", "kanguro", "-sN", "-e", q]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

# Fetch data for channels
query_main = """
SELECT 
    CASE 
        WHEN ot.id = 2 THEN 'Sito (ProduceShop)' 
        WHEN ot.is_internal = b'1' AND ot.id != 2 THEN 'Altri Canali Interni' 
        ELSE 'Marketplaces' 
    END AS macro_canale,
    SUM(o.total) as totale
FROM sal_order o 
JOIN sal_order_type ot ON o.type_id = ot.id 
WHERE o.date = CURDATE() AND o.is_deleted = 0 
GROUP BY macro_canale;
"""
res_main = run_query(query_main)

sito_tot = 0.0
mk_tot = 0.0
altri_tot = 0.0

for line in res_main.split('\n'):
    if not line: continue
    r = line.split('\t')
    if len(r) < 2: continue
    macro, tot = r[0], float(r[1] if r[1] != 'NULL' else 0)
    if macro == 'Sito (ProduceShop)':
        sito_tot += tot
    elif macro == 'Marketplaces':
        mk_tot += tot
    else:
        altri_tot += tot

# Fetch data for countries
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
res_nazioni = run_query(query_nazioni)
nazioni_labels = []
nazioni_sizes = []
for line in res_nazioni.split('\n'):
    if not line: continue
    r = line.split('\t')
    nazioni_labels.append(r[0])
    nazioni_sizes.append(float(r[1] if r[1] != 'NULL' else 0))

# --- PLOTTING ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4)) # Reduced figure size

# Plot 1: Macro Channels
labels_macro = []
sizes_macro = []
colors_macro = []

if sito_tot > 0:
    labels_macro.append('Sito')
    sizes_macro.append(sito_tot)
    colors_macro.append('#3498db')
if mk_tot > 0:
    labels_macro.append('Marketplaces')
    sizes_macro.append(mk_tot)
    colors_macro.append('#ff9999')
if altri_tot > 0:
    labels_macro.append('Altri')
    sizes_macro.append(altri_tot)
    colors_macro.append('#9b59b6')

if sizes_macro:
    ax1.pie(sizes_macro, labels=labels_macro, colors=colors_macro, autopct='%1.1f%%', startangle=90)
ax1.axis('equal')
ax1.set_title('Sito vs MK', pad=10, fontsize=12, fontweight='bold')

# Plot 2: Countries
if len(nazioni_labels) > 5:
    top_labels = nazioni_labels[:5]
    top_sizes = nazioni_sizes[:5]
    top_labels.append('Altri')
    top_sizes.append(sum(nazioni_sizes[5:]))
else:
    top_labels = nazioni_labels
    top_sizes = nazioni_sizes

if top_sizes:
    ax2.pie(top_sizes, labels=top_labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
ax2.axis('equal')
ax2.set_title('Nazioni', pad=10, fontsize=12, fontweight='bold')

plt.tight_layout()
# Reduced dpi and changed format to jpg to make it much lighter
plt.savefig('/tmp/fatturato_charts.jpg', dpi=100, bbox_inches='tight', pil_kwargs={"quality": 85})
