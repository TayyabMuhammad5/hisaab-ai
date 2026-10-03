from datetime import datetime
from typing import List

def build_system_prompt(schema_profile: str) -> List[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    
    system_text = f"""You are an expert DuckDB SQL writer for a small shop's database.
Today's date is {today}.
Output exactly one valid DuckDB SELECT statement.
No explanation, no markdown fences, no conversational text.
ONLY return the raw SQL query.

Here is the schema profile:
{schema_profile}

Few-shot examples:
Q: pichle mahine ki total sale kitni thi? (What was the total sale last month?)
A: SELECT SUM(total) FROM sales WHERE date >= date_trunc('month', current_date - interval '1 month') AND date < date_trunc('month', current_date);

Q: kis customer ka udhaar sab se zyada hai? (Which customer has the most udhaar?)
A: SELECT customer, SUM(amount) FROM udhaar_ledger WHERE type = 'given' GROUP BY customer ORDER BY SUM(amount) DESC LIMIT 1;

Q: top 5 items sold today
A: SELECT item, SUM(quantity) FROM sales WHERE date = current_date GROUP BY item ORDER BY SUM(quantity) DESC LIMIT 5;

Q: list all cash payments
A: SELECT * FROM sales WHERE payment_method = 'cash';
"""
    return [{"role": "system", "content": system_text}]

def build_correction_prompt(original_question: str, bad_sql: str, error_msg: str) -> str:
    return f"""The SQL you generated for the question "{original_question}" failed.
SQL: {bad_sql}
Error: {error_msg}

Please fix it and return a valid single SELECT statement. NO Markdown fences, NO explanations."""
