import pandas as pd
df = pd.read_excel('data/sample_shop.xlsx', sheet_name='sales')
print("Dtype of Date:", df['Date'].dtype)
print("Is object?", df['Date'].dtype == object)
