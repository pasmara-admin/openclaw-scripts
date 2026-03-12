import pymysql
import sys
import subprocess

skus_raw = """SGA800SNJY
SGA800SNJB
SGA800SNJR
SGA046ALTN
SGA046ALTV
SGA046ALTB
SGA046ALTG
SGA054CHIA
SGA054CHIG
SGA054CHIM
SGA054CHIN
SGA054CHIB
SGA800NEWN
SGA800NEWB
SGA800AMAN
SGA800AMAA
SGA800AMAB
SGA053LASB
BIS70QUANER
BIS70ROTBIA
SGA800SFRA
SGA054HOLG
SGA800DALS"""

skus = [s.strip() for s in skus_raw.split('\n') if s.strip()]
sku_list_str = ', '.join([f"'{s}'" for s in skus])

ps_data = {}
query_ps = f"""
    SELECT p.reference as sku, sa.quantity, ps.price as base_price, 0 as impact_price, sp.reduction, sp.reduction_type
    FROM ps_product p
    JOIN ps_stock_available sa ON p.id_product = sa.id_product AND sa.id_product_attribute = 0
    JOIN ps_product_shop ps ON p.id_product = ps.id_product AND ps.id_shop = 1
    LEFT JOIN ps_specific_price sp ON p.id_product = sp.id_product AND sp.id_shop IN (0, 1) AND sp.id_product_attribute = 0
    WHERE sa.id_shop = 1 AND p.reference IN ({sku_list_str})
    UNION
    SELECT pa.reference as sku, sa.quantity, ps.price as base_price, pas.price as impact_price, sp.reduction, sp.reduction_type
    FROM ps_product_attribute pa
    JOIN ps_stock_available sa ON pa.id_product = sa.id_product AND pa.id_product_attribute = sa.id_product_attribute
    JOIN ps_product_shop ps ON pa.id_product = ps.id_product AND ps.id_shop = 1
    JOIN ps_product_attribute_shop pas ON pa.id_product_attribute = pas.id_product_attribute AND pas.id_shop = 1
    LEFT JOIN ps_specific_price sp ON pa.id_product = sp.id_product AND sp.id_shop IN (0, 1) AND (sp.id_product_attribute = 0 OR sp.id_product_attribute = pa.id_product_attribute)
    WHERE sa.id_shop = 1 AND pa.reference IN ({sku_list_str})
"""

cmd = ["mysql", "--skip-ssl-verify-server-cert", "-h", "62.84.190.199", "-u", "john", "-ppqARa6aRozi6I", "produceshop", "-B", "-N", "-e", query_ps]
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

if res.returncode == 0:
    for line in res.stdout.strip().split('\n'):
        if not line: continue
        parts = line.split('\t')
        if len(parts) >= 6:
            sku = parts[0]
            base_price = float(parts[2])
            impact_price = float(parts[3])
            reduction_str = parts[4]
            reduction_type = parts[5]
            
            final_price = base_price + impact_price
            if reduction_str and reduction_str != 'NULL':
                reduction = float(reduction_str)
                if reduction_type == 'amount':
                    final_price -= reduction
                elif reduction_type == 'percentage':
                    final_price -= (final_price * reduction)
                    
            # Add 22% VAT for Italy final selling price to customer
            final_price_vat = final_price * 1.22
            ps_data[sku] = final_price_vat

print("Prezzi finali di vendita (IVA INCLUSA):")
for sku in skus:
    price = ps_data.get(sku, 0.0)
    print(f"- {sku}: €{price:.2f}")
