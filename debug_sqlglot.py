import sqlglot
from sqlglot import exp

sql1 = "WITH top_sales AS (SELECT * FROM sales LIMIT 5) SELECT * FROM top_sales"
parsed1 = sqlglot.parse_one(sql1, read="duckdb")

with_expr = parsed1.find(exp.With)
if with_expr:
    for cte in with_expr.expressions:
        print(f"CTE Name: {cte.alias}")

sql2 = "SELECT * FROM read_csv('/etc/passwd')"
parsed2 = sqlglot.parse_one(sql2, read="duckdb")
for table in parsed2.find_all(exp.Table):
    print(f"Table name: {table.name}")
    print(f"Is this a Func? {isinstance(table.this, exp.Func)}")
    if isinstance(table.this, exp.Func):
        print(f"Func name: {table.this.__class__.__name__.lower()}")

