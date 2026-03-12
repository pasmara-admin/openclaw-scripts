#!/bin/bash
MYSQL_PS="mysql --skip-ssl-verify-server-cert -h 62.84.190.199 -u john -pqARa6aRozi6I produceshop -N -B"
MYSQL_KANG="mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro -N -B"

echo "--- 1. Stock (PrestaShop) ---"
$MYSQL_PS -e "
SELECT SUM(s.quantity) 
FROM ps_stock_available s 
LEFT JOIN ps_product_attribute pa ON s.id_product = pa.id_product AND s.id_product_attribute = pa.id_product_attribute 
LEFT JOIN ps_product p ON s.id_product = p.id_product
WHERE (pa.reference = 'sa800texe' OR p.reference = 'sa800texe') AND s.id_shop = 1;"

echo "--- 2. Sales since Oct 2025 (Kanguro) ---"
$MYSQL_KANG -e "
SELECT SUM(sor.qty) 
FROM sal_order_row sor 
JOIN sal_order so ON sor.order_id = so.id 
WHERE (sor.reference = 'sa800texe' OR sor.reference = 'SA800TEXE') 
  AND so.date >= '2025-10-01' 
  AND so.state_id NOT IN ('00', '01');"

echo "--- 3. Last IT Price (Kanguro) ---"
$MYSQL_KANG -e "
SELECT sor.price, so.date
FROM sal_order_row sor
JOIN sal_order so ON sor.order_id = so.id
WHERE (sor.reference = 'sa800texe' OR sor.reference = 'SA800TEXE')
  AND so.delivery_country_id = 10
  AND so.state_id NOT IN ('00', '01')
  AND sor.price > 0
ORDER BY so.date DESC, so.time DESC
LIMIT 1;"

echo "--- 4. WAC Original Currency (Kanguro) ---"
$MYSQL_KANG -e "
SELECT w.price, w.currency 
FROM inv_weighted_average_cost w 
JOIN dat_product p ON w.product_id = p.id 
WHERE p.reference = 'SA800TEXE' 
ORDER BY w.purchase_date DESC LIMIT 1;"

