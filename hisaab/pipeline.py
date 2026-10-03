import duckdb
from typing import Dict, Any, List
from . import config
from .prompt import build_system_prompt, build_correction_prompt
from .llm import generate_sql
from .validator import validate_sql
from .executor import execute_query
from .answer import pick_chart_and_summary

def run_pipeline(question: str, conn: duckdb.DuckDBPyConnection, schema_profile: str, allowed_tables: List[str]) -> Dict[str, Any]:
    messages = build_system_prompt(schema_profile)
    messages.append({"role": "user", "content": question})
    
    attempts = 0
    total_latency = 0
    provider_used = None
    
    while attempts <= config.MAX_RETRIES:
        attempts += 1
        try:
            sql, provider, latency = generate_sql(messages)
            total_latency += latency
            provider_used = provider
            
            is_valid, rewritten_sql, reason = validate_sql(sql, allowed_tables)
            if not is_valid:
                print(f"Validation failed on attempt {attempts}: {reason} (SQL: {sql})")
                correction = build_correction_prompt(question, sql, reason)
                messages.append({"role": "assistant", "content": sql})
                messages.append({"role": "user", "content": correction})
                continue
                
            df, exec_latency, exec_error = execute_query(conn, rewritten_sql)
            total_latency += exec_latency
            
            if exec_error:
                print(f"Execution failed on attempt {attempts}: {exec_error} (SQL: {rewritten_sql})")
                correction = build_correction_prompt(question, rewritten_sql, exec_error)
                messages.append({"role": "assistant", "content": rewritten_sql})
                messages.append({"role": "user", "content": correction})
                continue
                
            # Success
            chart_type, summary = pick_chart_and_summary(df)
            return {
                "answer_text": summary,
                "sql": rewritten_sql,
                "dataframe": df,
                "chart": chart_type,
                "provider_used": provider_used,
                "attempts": attempts,
                "latency_ms": total_latency,
                "error": None
            }
            
        except Exception as e:
            return {
                "answer_text": "I encountered an error trying to process your request.",
                "sql": None,
                "dataframe": None,
                "chart": None,
                "provider_used": provider_used,
                "attempts": attempts,
                "latency_ms": total_latency,
                "error": str(e)
            }
            
    # Max retries exceeded
    return {
        "answer_text": "I couldn't answer this reliably. Can you rephrase or name the columns you mean?",
        "sql": None,
        "dataframe": None,
        "chart": None,
        "provider_used": provider_used,
        "attempts": attempts,
        "latency_ms": total_latency,
        "error": "Max retries exceeded."
    }
