from pathlib import Path
from data.make_sample_data import generate_sample_data
from hisaab.data_loader import load_files_to_duckdb
from hisaab.profiler import get_db_profile

def main():
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    
    print("1. Generating sample data...")
    generate_sample_data(data_dir)
    
    sample_file = data_dir / "sample_shop.xlsx"
    print(f"\n2. Loading data from {sample_file}...")
    conn, mappings, logs = load_files_to_duckdb([sample_file])
    
    print("\nCoercion Logs:")
    for log in logs:
        print(f"  - {log}")
        
    print("\nColumn Mappings:")
    for table, mapping in mappings.items():
        print(f"  [{table}]")
        for orig, clean in mapping.items():
            if orig != clean:
                print(f"    '{orig}' -> '{clean}'")
                
    print("\n3. Generating Profile...")
    profile_text = get_db_profile(conn)
    print("\n--- SCHEMA PROFILE ---\n")
    print(profile_text)
    print("----------------------\n")
    
    token_count = len(profile_text) // 4
    print(f"Approximate Profile Token Count: {token_count} tokens")
    print("\nMilestone 1 Verification Complete.")

if __name__ == "__main__":
    main()
