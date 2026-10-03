import pytest
import duckdb
from hisaab.validator import validate_sql
from hisaab.executor import execute_query
from hisaab import config
import time

def test_valid_select():
    sql = "SELECT item, SUM(quantity) FROM sales GROUP BY item"
    is_valid, rewritten, reason = validate_sql(sql, ["sales", "udhaar"])
    assert is_valid
    assert "LIMIT 1000" in rewritten
    
def test_cte_support():
    sql = "WITH top_sales AS (SELECT * FROM sales LIMIT 5) SELECT * FROM top_sales"
    is_valid, rewritten, reason = validate_sql(sql, ["sales"])
    assert is_valid
    
def test_reject_multiple_statements():
    sql = "SELECT 1; DROP TABLE sales;"
    is_valid, rewritten, reason = validate_sql(sql, ["sales"])
    assert not is_valid
    assert "Multiple statements" in reason
    
def test_reject_drop():
    sql = "DROP TABLE sales"
    is_valid, rewritten, reason = validate_sql(sql, ["sales"])
    assert not is_valid
    assert "Only SELECT" in reason
    
def test_reject_file_read():
    sql = "SELECT * FROM read_csv('/etc/passwd')"
    is_valid, rewritten, reason = validate_sql(sql, ["sales"])
    assert not is_valid
    assert "Function 'read_csv' is not allowed" in reason

def test_reject_unknown_table():
    sql = "SELECT * FROM users"
    is_valid, rewritten, reason = validate_sql(sql, ["sales"])
    assert not is_valid
    assert "not allowed or does not exist" in reason

def test_enforce_limit():
    sql = "SELECT * FROM sales LIMIT 5000"
    is_valid, rewritten, reason = validate_sql(sql, ["sales"])
    assert is_valid
    assert "LIMIT 1000" in rewritten
    
def test_executor_timeout():
    # Setup test DB
    conn = duckdb.connect()
    
    # Generate large data series that will take a long time to cross join
    conn.execute("CREATE TABLE big AS SELECT * FROM generate_series(1, 5000)")
    
    # An intentionally slow query (cross join)
    slow_sql = "SELECT COUNT(*) FROM big b1, big b2, big b3"
    
    # Temporarily set timeout low for the test
    original_timeout = config.QUERY_TIMEOUT_S
    config.QUERY_TIMEOUT_S = 0.5
    
    df, latency, error = execute_query(conn, slow_sql)
    
    config.QUERY_TIMEOUT_S = original_timeout
    
    assert error is not None
    assert "Query timed out" in error
    assert latency >= 500
