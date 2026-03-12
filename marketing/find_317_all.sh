#!/bin/bash
MYSQL_KANG="mysql -h 34.38.166.212 -u john -p3rmiCyf6d~MZDO41 kanguro -N -B"
TABLES=$($MYSQL_KANG -e "SHOW TABLES;")
for T in $TABLES; do
    COLS=$($MYSQL_KANG -e "SHOW COLUMNS FROM $T" | grep -iE "price|cost|amount|fob|net|gross" | awk '{print $1}')
    if [ -n "$COLS" ]; then
        for C in $COLS; do
            # echo "Checking $T.$C"
            $MYSQL_KANG -e "SELECT '$T.$C', $C FROM $T WHERE ROUND($C, 2) = 31.70 LIMIT 1;" 2>/dev/null
        done
    fi
done
