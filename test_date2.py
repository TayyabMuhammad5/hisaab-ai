import pandas as pd
df = pd.read_excel('data/sample_shop.xlsx', sheet_name='sales')
try:
    parsed = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    print("Parsed count:", parsed.notna().sum())
    print("Type:", parsed.dtype)
except Exception as e:
    print("Exception:", str(e))
