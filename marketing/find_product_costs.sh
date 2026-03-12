#!/bin/bash
if [ -z "$1" ]; then
  echo "Usage: $0 <product_id>"
  exit 1
fi

PRODUCT_ID=$1
MYSQL_KANG="mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro -N -B"

$MYSQL_KANG -e "
SELECT 'dat_product_price', price FROM dat_product_price WHERE product_id = $PRODUCT_ID;
SELECT 'pch_product_cost', price_fob FROM pch_product_cost WHERE product_id = $PRODUCT_ID;
SELECT 'inv_weighted_average_cost', price, wac_eur FROM inv_weighted_average_cost WHERE product_id = $PRODUCT_ID;
SELECT 'dat_product', volume, unit_weight_g FROM dat_product WHERE id = $PRODUCT_ID;
"
