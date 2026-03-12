import sys

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
prices = {}

try:
    with open('/tmp/ps_prices_vat.tsv', 'r') as f:
        next(f)
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                sku = parts[0]
                base_price = float(parts[1])
                impact_price = float(parts[2])
                reduction_str = parts[3]
                reduction_type = parts[4]
                
                final_price = base_price + impact_price
                if reduction_str and reduction_str != 'NULL':
                    reduction = float(reduction_str)
                    if reduction_type == 'amount':
                        final_price -= reduction
                    elif reduction_type == 'percentage':
                        final_price -= (final_price * reduction)
                        
                final_price_vat = final_price * 1.22
                prices[sku] = final_price_vat
except Exception as e:
    print(e)

for sku in skus:
    if sku in prices:
        print(f"- {sku}: €{prices[sku]:.2f}")
    else:
        print(f"- {sku}: Non trovato")
