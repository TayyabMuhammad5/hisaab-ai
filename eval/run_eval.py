import os
import sys
import json
import duckdb
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from hisaab.data_loader import load_files_to_duckdb
from hisaab.profiler import get_db_profile
from hisaab.pipeline import run_pipeline

def norm(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
        elif pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype(float).round(2)
        else:
            df[c] = df[c].astype(str).str.strip()
    return df

def same(expected, got):
    if expected is None or expected.empty:
        return got is None or got.empty
    if got is None or got.empty:
        return False
        
    e, g = norm(expected), norm(got)
    if len(e) != len(g):
        return False
    got_cols = [sorted(g[c].tolist()) for c in g.columns]
    return all(sorted(e[c].tolist()) in got_cols for c in e.columns)

def main():
    base_dir = Path(__file__).parent.parent
    sample_file = base_dir / "data" / "sample_shop.xlsx"
    gold_file = Path(__file__).parent / "gold_questions.json"
    
    if not sample_file.exists():
        print("Please run verify_m1.py to generate sample data.")
        return
        
    with open(gold_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    conn, maps, logs = load_files_to_duckdb([sample_file])
    schema_profile = get_db_profile(conn)
    allowed_tables = list(maps.keys())
    
    passed = 0
    total = len(questions)
    
    for i, item in enumerate(questions, 1):
        q = item["question"]
        ref_sql = item["reference_sql"]
        
        try:
            ref_df = conn.execute(ref_sql).df()
        except Exception as e:
            print(f"[{i}/{total}] SKIP: Reference SQL failed: {e}")
            continue
            
        if ref_df.empty:
            print(f"[{i}/{total}] SKIP: Reference query returned empty result, fix the gold query.")
            continue
            
        result = run_pipeline(q, conn, schema_profile, allowed_tables)
        
        if result["error"]:
            print(f"[{i}/{total}] FAIL: Error - {result['error']}")
            continue
            
        model_df = result["dataframe"]
        
        if same(ref_df, model_df):
            print(f"[{i}/{total}] PASS")
            passed += 1
        else:
            print(f"[{i}/{total}] FAIL: Results differ")
            print(f"  Question: {q}")
            print(f"  Model SQL: {result['sql']}")
            print(f"  Reference SQL: {ref_sql}")
            print(f"  Expected Row Count: {len(ref_df)}")
            print(f"  Got Row Count: {len(model_df) if model_df is not None else 0}")
            print(f"  Expected:\n{norm(ref_df).head(2).to_dict() if not ref_df.empty else 'Empty'}")
            print(f"  Got:\n{norm(model_df).head(2).to_dict() if model_df is not None and not model_df.empty else 'Empty'}")
            
    print(f"\nFinal Score: {passed}/{total}")

if __name__ == "__main__":
    main()
