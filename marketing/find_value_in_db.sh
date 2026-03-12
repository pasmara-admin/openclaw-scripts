#!/bin/bash
if [ -z "$1" ]; then
  echo "Usage: $0 <numeric_value>"
  exit 1
fi

SEARCH_VAL=$1
MYSQL_KANG="mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro -N -B"

TABLES=$($MYSQL_KANG -e "SHOW TABLES;")
for T in $TABLES; do
    COLS=$($MYSQL_KANG -e "SHOW COLUMNS FROM $T" | grep -iE "price|cost|amount|fob|net|gross" | awk '{print $1}')
    if [ -n "$COLS" ]; then
        for C in $COLS; do
            $MYSQL_KANG -e "SELECT '$T.$C', $C FROM $T WHERE ROUND($C, 2) = $SEARCH_VAL LIMIT 1;" 2>/dev/null
        done
    fi
done
