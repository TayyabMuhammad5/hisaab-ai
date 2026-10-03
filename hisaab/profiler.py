import duckdb

def get_db_profile(conn: duckdb.DuckDBPyConnection) -> str:
    tables = conn.execute("SHOW TABLES").fetchall()
    
    profile_lines = []
    
    for (table_name,) in tables:
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        profile_lines.append(f"Table: {table_name} (Rows: {row_count})")
        
        cols_info = conn.execute(f"DESCRIBE {table_name}").fetchall()
        
        for col_info in cols_info:
            col_name = col_info[0]
            col_type = col_info[1]
            
            stats = conn.execute(f"""
                SELECT 
                    COUNT(*) FILTER (WHERE "{col_name}" IS NULL) * 100.0 / COUNT(*) as null_pct,
                    COUNT(DISTINCT "{col_name}") as approx_distinct,
                    MIN("{col_name}") as min_val,
                    MAX("{col_name}") as max_val
                FROM {table_name}
            """).fetchone()
            
            null_pct = stats[0] if stats[0] is not None else 0.0
            distinct = stats[1] if stats[1] is not None else 0
            
            min_max_str = ""
            if any(t in col_type for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'DATE', 'TIMESTAMP']):
                min_max_str = f", Min: {stats[2]}, Max: {stats[3]}"
                
            samples = conn.execute(f"""
                SELECT DISTINCT "{col_name}" 
                FROM {table_name} 
                WHERE "{col_name}" IS NOT NULL 
                LIMIT 5
            """).fetchall()
            sample_vals = [str(s[0]) for s in samples]
            
            profile_lines.append(f"  - {col_name} ({col_type}): Nulls {null_pct:.1f}%, Distinct {distinct}{min_max_str}")
            if sample_vals:
                profile_lines.append(f"    Samples: {', '.join(sample_vals)}")
                
        profile_lines.append("")
        
    return "\n".join(profile_lines)
