import pandas as pd
import sys

try:
    df = pd.read_excel('/root/.openclaw/media/inbound/Monitoraggio_Container---febc7e3b-5230-4ed3-bae4-623290376ef1.xlsx')
    print("Columns:", df.columns.tolist())
    print("\nHead:\n", df.head(10).to_string())
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
