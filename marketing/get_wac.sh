#!/bin/bash
MYSQL_KANG="mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro -N -B"

echo "WAC da inv_weighted_average_cost:"
$MYSQL_KANG -e "
    SELECT w.price, w.currency, w.wac_eur 
    FROM inv_weighted_average_cost w 
    JOIN dat_product p ON w.product_id = p.id 
    WHERE p.reference IN ('SA800TEXE', 'sa800texe', 'SA800TEX') 
    ORDER BY w.purchase_date DESC LIMIT 5;"

echo "WAC da pch_order_row:"
$MYSQL_KANG -e "
    SELECT r.price_fob, o.currency_iso_code, p.reference
    FROM pch_order_row r 
    JOIN pch_order o ON r.order_id = o.id 
    JOIN dat_product p ON r.product_id = p.id 
    WHERE p.reference IN ('SA800TEXE', 'sa800texe', 'SA800TEX') 
    ORDER BY o.date DESC LIMIT 5;"

echo "WAC da pch_price_list_detail:"
$MYSQL_KANG -e "
    SELECT d.net_price, c.iso_code, p.reference
    FROM pch_price_list_detail d 
    JOIN pch_price_list l ON d.list_id = l.id 
    JOIN dat_currency c ON l.currency_id = c.id 
    JOIN dat_product p ON d.product_id = p.id 
    WHERE p.reference IN ('SA800TEXE', 'sa800texe', 'SA800TEX') 
    ORDER BY d.date DESC LIMIT 5;"
