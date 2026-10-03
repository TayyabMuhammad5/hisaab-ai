import sqlglot
from sqlglot import exp
from typing import List, Tuple
from . import config

ALLOWED_FUNCTIONS = {"unnest", "generate_series"} # safe table-valued functions

def validate_sql(sql: str, allowed_tables: List[str]) -> Tuple[bool, str, str]:
    """
    Validates a SQL string for DuckDB safety.
    Returns: (is_valid, rewritten_sql, reason)
    """
    try:
        parsed = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as e:
        return False, sql, f"SQL Parse Error: {str(e)}"
        
    if not parsed or len(parsed) == 0:
        return False, sql, "No query found."
        
    if len(parsed) > 1:
        return False, sql, "Multiple statements are not allowed. Provide exactly one SELECT query."
        
    statement = parsed[0]
    
    # 1. Must be a SELECT (or CTE wrapping a SELECT)
    if not isinstance(statement, exp.Select):
        return False, sql, "Only SELECT statements are allowed."
        
    # 2. Find all CTE names so we can allow them as valid tables
    cte_names = set()
    with_expr = statement.find(exp.With)
    if with_expr:
        for expression in with_expr.expressions:
            cte_names.add(expression.alias)
                
    # 3. Check all referenced tables and table-valued functions
    for table in statement.find_all(exp.Table):
        if isinstance(table.this, exp.Func):
            func_name = table.this.sql().split('(')[0].lower().strip()
            if func_name not in ALLOWED_FUNCTIONS:
                return False, sql, f"Function '{func_name}' is not allowed."
            continue
            
        name = table.name
        if name and name not in allowed_tables and name not in cte_names:
            return False, sql, f"Table '{name}' is not allowed or does not exist."
            
    # 4. Check for disallowed commands nested inside (just in case)
    disallowed_types = (
        exp.Drop, exp.Delete, exp.Insert, exp.Update, exp.Create, 
        exp.Alter, exp.Pragma, exp.Command
    )
    if statement.find(*disallowed_types):
        return False, sql, "Disallowed command type found in query."

    # 5. Enforce LIMIT
    existing_limit = statement.args.get("limit")
    if existing_limit:
        try:
            limit_val = int(existing_limit.expression.name)
            if limit_val > config.ROW_CAP:
                statement.set("limit", exp.Limit(expression=exp.Literal.number(config.ROW_CAP)))
        except (ValueError, AttributeError):
            # If complex limit, just override
            statement.set("limit", exp.Limit(expression=exp.Literal.number(config.ROW_CAP)))
    else:
        statement.set("limit", exp.Limit(expression=exp.Literal.number(config.ROW_CAP)))
        
    return True, statement.sql(dialect="duckdb"), "ok"
