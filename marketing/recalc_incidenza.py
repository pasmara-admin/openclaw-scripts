import csv

data = []
with open('/root/.openclaw/workspace-marketing/top_100_roas_analysis.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sku = row['SKU']
        rev = float(row['Revenue'])
        spend = float(row['Spend'])
        if spend > 0 and rev > 0:
            incidenza = spend / rev
            data.append({'sku': sku, 'rev': rev, 'spend': spend, 'incidenza': incidenza})

data.sort(key=lambda x: x['incidenza'])

with open('/root/.openclaw/workspace-marketing/top_100_incidenza_analysis.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['SKU', 'Fatturato', 'Spesa', 'Incidenza'])
    writer.writeheader()
    for r in data:
        writer.writerow({'SKU': r['sku'], 'Fatturato': r['rev'], 'Spesa': r['spend'], 'Incidenza': r['incidenza']})

print("Top 10 SKUs per Incidenza (più bassa è migliore):")
for i, r in enumerate(data[:10]):
    print(f"{i+1}. {r['sku']} - Fatturato: €{r['rev']:.2f} | Spesa: €{r['spend']:.2f} | Incidenza: {r['incidenza']*100:.2f}%")
