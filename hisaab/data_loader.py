import pandas as pd
import duckdb
import re
import warnings
from pathlib import Path
from typing import Dict, List, Tuple
from . import config



def clean_column_name(col: str) -> str:
    col = str(col).strip().lower()
    col = re.sub(r'[^a-z0-9]+', '_', col)
    return col.strip('_')

def clean_dataframe(df: pd.DataFrame, table_name: str) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
    logs = []
    
    # Map original to clean column names
    orig_cols = list(df.columns)
    clean_cols = [clean_column_name(c) for c in orig_cols]
    
    # Deduplicate clean columns
    seen = {}
    for i, c in enumerate(clean_cols):
        if c in seen:
            seen[c] += 1
            clean_cols[i] = f"{c}_{seen[c]}"
        else:
            seen[c] = 0
            if c == "":
                clean_cols[i] = f"col_{i}"
                seen[f"col_{i}"] = 0
                
    col_mapping = dict(zip(orig_cols, clean_cols))
    df.columns = clean_cols
    
    for col in clean_cols:
        # Keep ID columns as string
        if col.endswith('_id') or col == 'id':
            df[col] = df[col].astype(str)
            continue
            
        # Try cleaning Rs prefixes and converting to numeric
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            sample_strs = df[col].dropna().astype(str)
            if sample_strs.str.contains(r'^[^\d]*rs\.?\s*[\d,]+', case=False, regex=True).any():
                cleaned_series = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df[col] = pd.to_numeric(cleaned_series, errors='coerce')
                num_cleaned = sample_strs.str.contains(r'^[^\d]*rs\.?\s*[\d,]+', case=False, regex=True).sum()
                logs.append(f"[{table_name}] Stripped 'Rs ' and converted {num_cleaned} values in '{col}' to numeric.")
                continue

            # Try datetime with dayfirst
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                try:
                    parsed = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                    if parsed.notna().sum() > len(df[col].dropna()) * 0.5 and parsed.notna().sum() > 0:
                         df[col] = parsed
                         logs.append(f"[{table_name}] Parsed '{col}' as datetime (day-first).")
                except Exception:
                    pass
                
    return df, col_mapping, logs

def load_files_to_duckdb(file_paths: List[Path]) -> Tuple[duckdb.DuckDBPyConnection, Dict[str, Dict[str, str]], List[str]]:
    conn = duckdb.connect(database=':memory:')
    all_logs = []
    all_mappings = {}
    
    for file_path in file_paths:
        if file_path.stat().st_size > config.MAX_FILE_MB * 1024 * 1024:
            raise ValueError(f"File {file_path.name} exceeds maximum size of {config.MAX_FILE_MB}MB.")
            
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                if len(df) > config.MAX_ROWS:
                    raise ValueError(f"Sheet {sheet_name} in {file_path.name} exceeds max rows of {config.MAX_ROWS}.")
                table_name = clean_column_name(sheet_name)
                if not table_name:
                    table_name = "table"
                df, mapping, logs = clean_dataframe(df, table_name)
                conn.register(table_name, df)
                all_mappings[table_name] = mapping
                all_logs.extend(logs)
                
        elif file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
            if len(df) > config.MAX_ROWS:
                raise ValueError(f"File {file_path.name} exceeds max rows of {config.MAX_ROWS}.")
            table_name = clean_column_name(file_path.stem)
            df, mapping, logs = clean_dataframe(df, table_name)
            conn.register(table_name, df)
            all_mappings[table_name] = mapping
            all_logs.extend(logs)
        else:
            raise ValueError(f"Unsupported file format {file_path.name}. Please upload .csv or .xlsx")
            
    return conn, all_mappings, all_logs
