import pandas as pd

df = pd.DataFrame({'date': ['08/07/2023', '21/01/2023', 'invalid']})
parsed = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
print("notna().sum():", parsed.notna().sum())
print("len(parsed.dropna()):", len(parsed.dropna()))
if parsed.notna().sum() > len(parsed.dropna()) * 0.5 and parsed.notna().sum() > 0:
    print("Condition passed")
else:
    print("Condition failed")
