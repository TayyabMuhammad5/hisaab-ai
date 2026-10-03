import os
from pathlib import Path
from hisaab.data_loader import load_files_to_duckdb
from hisaab.profiler import get_db_profile
from hisaab.pipeline import run_pipeline

def main():
    base_dir = Path(__file__).parent
    sample_file = base_dir / "data" / "sample_shop.xlsx"
    
    if not sample_file.exists():
        print("Run verify_m1.py first to generate data.")
        return
        
    print("Loading data...")
    conn, mappings, logs = load_files_to_duckdb([sample_file])
    schema_profile = get_db_profile(conn)
    allowed_tables = list(mappings.keys())
    
    questions = [
        "What was the highest quantity sold in a single transaction?",
        "pichle mahine sab se zyada kaunsa item bika?"
    ]
    
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY is not set. Will attempt Ollama fallback.")
        
    for q in questions:
        print(f"\n--- QUESTION: {q} ---")
        result = run_pipeline(q, conn, schema_profile, allowed_tables)
        print(f"Summary: {result['answer_text']}")
        print(f"SQL: {result['sql']}")
        print(f"Chart: {result['chart']}")
        print(f"Provider: {result['provider_used']}")
        print(f"Attempts: {result['attempts']}")
        print(f"Error: {result['error']}")
        if result['dataframe'] is not None:
            print("\nData:")
            print(result['dataframe'].head())

if __name__ == "__main__":
    main()
