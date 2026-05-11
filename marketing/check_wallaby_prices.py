import sys
import subprocess

def get_wallaby_prices(skus):
    # Wallaby credentials
    host = "161.97.132.28"
    user = "john"
    password = "6uxA8iwIsA5e"
    db = "wallaby"
    id_shop = 1  # Italia

    sku_list_str = ", ".join([f"'{s}'" for s in skus])
    
    # 1. Map SKUs to IDs
    # Query main products
    query_main = f"SELECT reference, id_product, 0 as id_product_attribute FROM products WHERE reference IN ({sku_list_str})"
    # Query variants
    query_var = f"SELECT reference, id_product, id_product_attribute FROM product_attributes WHERE reference IN ({sku_list_str})"
    
    query_mapping = f"{query_main} UNION {query_var};"
    
    cmd = ["mysql", "--skip-ssl-verify-server-cert", "-h", host, "-u", user, f"-p{password}", db, "-N", "-B", "-e", query_mapping]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    sku_map = {}
    product_ids = set()
    attribute_ids = set()
    
    if res.stdout.strip():
        for line in res.stdout.strip().split('\n'):
            parts = line.split('\t')
            sku = parts[0]
            pid = parts[1]
            paid = parts[2]
            sku_map[sku] = {"pid": pid, "paid": paid}
            product_ids.add(pid)
            if paid != '0':
                attribute_ids.add(paid)

    if not sku_map:
        return [{"sku": sku, "price": None, "error": "Non trovato"} for sku in skus]

    # 2. Get all base prices and discounts
    pid_list_str = ", ".join(product_ids)
    query_prices = f"SELECT id_product, gross, discount FROM product_prices WHERE id_product IN ({pid_list_str}) AND id_shop = {id_shop};"
    cmd = ["mysql", "--skip-ssl-verify-server-cert", "-h", host, "-u", user, f"-p{password}", db, "-N", "-B", "-e", query_prices]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    base_prices = {}
    if res.stdout.strip():
        for line in res.stdout.strip().split('\n'):
            parts = line.split('\t')
            base_prices[parts[0]] = {"gross": float(parts[1]), "discount": float(parts[2])}

    # 3. Get all impacts
    impacts = {}
    if attribute_ids:
        paid_list_str = ", ".join(attribute_ids)
        query_impacts = f"SELECT id_product_attribute, impact FROM product_attribute_prices WHERE id_product_attribute IN ({paid_list_str});"
        cmd = ["mysql", "--skip-ssl-verify-server-cert", "-h", host, "-u", user, f"-p{password}", db, "-N", "-B", "-e", query_impacts]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.stdout.strip():
            for line in res.stdout.strip().split('\n'):
                parts = line.split('\t')
                impacts[parts[0]] = float(parts[1])

    # 4. Calculate final prices
    results = []
    for sku in skus:
        if sku not in sku_map:
            results.append({"sku": sku, "price": None, "error": "Non trovato"})
            continue
            
        mapping = sku_map[sku]
        pid = mapping["pid"]
        paid = mapping["paid"]
        
        if pid not in base_prices:
            results.append({"sku": sku, "price": None, "error": "Prezzo IT non trovato"})
            continue
            
        base = base_prices[pid]
        gross = base["gross"]
        discount = base["discount"]
        impact = impacts.get(paid, 0.0)
        
        # Final price logic: ((Gross + Impact) - Discount) * 1.22
        final_price_net = (gross + impact) - discount
        final_price_vat = final_price_net * 1.22
        
        results.append({"sku": sku, "price": final_price_vat})

    # Sort by price
    results.sort(key=lambda x: (x['price'] is None, x['price']))
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_wallaby_prices.py SKU1 SKU2 ...")
        sys.exit(1)
        
    skus = [s.strip() for s in sys.argv[1:] if s.strip()]
    prices = get_wallaby_prices(skus)
    
    print(f"{'SKU':<25} | {'Prezzo (IVA Inc.)':<15}")
    print("-" * 43)
    for item in prices:
        if item['price'] is not None:
            print(f"{item['sku']:<25} | €{item['price']:>13.2f}")
        else:
            print(f"{item['sku']:<25} | {item['error']:<15}")
