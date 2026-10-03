# Hisaab AI 🛒 (Demo MVP)

A talk-to-your-data tool for small shop owners in Pakistan. This MVP lets you upload a CSV/Excel file or use sample kiryana store data, and ask questions in English or Roman Urdu to get answers, charts, and SQL queries.

## Tech Stack
- **UI:** Gradio
- **Data Engine:** DuckDB (in-memory, session-scoped)
- **Data Loading:** Pandas (with messy value coercions)
- **Parsing / Validation:** SQLGlot
- **LLM API:** Groq (`openai/gpt-oss-20b`)

## Model and License
This project relies on the **GPT-OSS 20B** model accessed via Groq, which is an open-weight reasoning model.

## Features & Guardrails
- **Read-Only Sandbox**: DuckDB `enable_external_access` is disabled to prevent file reads (e.g. `/etc/passwd`).
- **AST Validation**: Every generated query is parsed using SQLGlot. It strictly enforces exactly one `SELECT` statement and checks that all tables referenced belong to the active user session.
- **Limits**: Missing `LIMIT` clauses are automatically added, and high limits are clamped to a hard cap (1,000 rows).
- **Timeouts**: Long-running queries (like accidental cross joins) are killed in a background thread after a hard timeout.

## Evaluation
Execution accuracy: **18/20 (90%)** on a self-written gold set, evaluated on synthetic data with no overlap with few-shot examples, using Groq (GPT-OSS 20B). 

*Note: One of the failures occurred because the model correctly used a `WHERE customer IN (...)` clause to avoid duplicating rows in a 1-to-many relationship, outsmarting the flawed `JOIN` in the reference query! The actual logical accuracy is arguably 19/20.*

## Limitations
- **Accuracy**: Small open-weight models may occasionally generate incorrect SQL for complex analytical logic.
- **Privacy**: The free-tier Groq endpoint does not offer strict data privacy guarantees (this is a demo).
- **Scale**: File size is capped at 5MB (approx 50,000 rows) so that the free Hugging Face CPU Space remains responsive.

## Setup
1. `pip install -r requirements.txt`
2. Configure environment variables in `.env` (copy `.env.example`).
3. Run the app: `python app.py`
4. Login with `demo` / `demo123`.
