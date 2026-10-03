import pandas as pd

def pick_chart_and_summary(df: pd.DataFrame) -> tuple[str, str]:
    if df is None or df.empty:
        return "table", "No data found for this query."
        
    chart_type = "table"
    cols = df.columns
    types = df.dtypes
    
    date_cols = [c for c in cols if pd.api.types.is_datetime64_any_dtype(types[c]) or 'date' in c.lower()]
    num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(types[c]) and not c.endswith('_id')]
    cat_cols = [c for c in cols if c not in date_cols and c not in num_cols and not c.endswith('_id')]
    
    if len(df) == 1 and len(cols) == 1 and len(num_cols) == 1:
        chart_type = "big_number"
        val = df.iloc[0, 0]
        summary = f"The result is {val:,.2f}" if isinstance(val, float) else f"The result is {val}"
        return chart_type, summary
        
    if date_cols and num_cols:
        chart_type = "line"
    elif cat_cols and num_cols:
        chart_type = "bar"
        
    if chart_type == "line":
        summary = f"Showing a trend of {num_cols[0]} over {date_cols[0]}."
    elif chart_type == "bar":
        summary = f"Showing {num_cols[0]} grouped by {cat_cols[0]} (Top 10)."
    else:
        summary = f"Found {len(df)} rows of data."
        
    return chart_type, summary
