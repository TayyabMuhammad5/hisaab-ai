import duckdb
import pandas as pd
import threading
import time
from typing import Tuple, Optional
from . import config

def execute_query(conn: duckdb.DuckDBPyConnection, sql: str) -> Tuple[Optional[pd.DataFrame], float, Optional[str]]:
    """
    Executes a query safely with a timeout.
    Returns: (dataframe, latency_ms, error_message)
    """
    # Lockdown DuckDB connection (idempotent, harmless if already set)
    try:
        conn.execute("SET enable_external_access=false")
        conn.execute("SET lock_configuration=true")
    except duckdb.Error:
        pass # Might already be locked

    result_df = None
    exec_error = None
    
    def worker():
        nonlocal result_df, exec_error
        try:
            result_df = conn.execute(sql).df()
        except Exception as e:
            exec_error = str(e)
            
    start_time = time.time()
    thread = threading.Thread(target=worker)
    thread.start()
    
    thread.join(config.QUERY_TIMEOUT_S)
    
    if thread.is_alive():
        # Interrupt the connection to stop the runaway query
        conn.interrupt()
        thread.join() # Wait for it to actually die
        exec_error = f"Query timed out after {config.QUERY_TIMEOUT_S} seconds."
        
    latency_ms = (time.time() - start_time) * 1000
    
    return result_df, latency_ms, exec_error
