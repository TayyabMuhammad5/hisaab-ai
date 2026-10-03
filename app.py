import os
import gradio as gr
from pathlib import Path
import plotly.express as px
import pandas as pd
from hisaab import config
from hisaab.data_loader import load_files_to_duckdb
from hisaab.profiler import get_db_profile
from hisaab.pipeline import run_pipeline
from data.make_sample_data import generate_sample_data

data_dir = Path(__file__).parent / "data"
sample_file = data_dir / "sample_shop.xlsx"
if not sample_file.exists():
    generate_sample_data(data_dir)

SESSION_DB = {}

def get_session(request: gr.Request):
    return SESSION_DB.get(request.session_hash)

def init_session(file_paths: list, request: gr.Request):
    if request.session_hash in SESSION_DB:
        try:
            SESSION_DB[request.session_hash]["conn"].close()
        except:
            pass
    
    conn, maps, logs = load_files_to_duckdb(file_paths)
    schema = get_db_profile(conn)
    allowed_tables = list(maps.keys())
    
    SESSION_DB[request.session_hash] = {
        "conn": conn,
        "schema": schema,
        "allowed_tables": allowed_tables
    }
    
    preview_md = "### Schema\n```\n" + schema + "\n```"
    return preview_md, "Dataset loaded successfully!"

def load_uploaded_file(file_objs, request: gr.Request):
    if not file_objs:
        return "No files uploaded.", "Please upload a file."
    try:
        paths = [Path(f.name) for f in file_objs]
        return init_session(paths, request)
    except Exception as e:
        return f"Error loading file: {str(e)}", "Upload failed."

def load_sample_data(request: gr.Request):
    try:
        return init_session([sample_file], request)
    except Exception as e:
        return f"Error loading sample data: {str(e)}", "Sample load failed."

def ask_question(question: str, request: gr.Request):
    session = get_session(request)
    if not session:
        return "Please upload a dataset or load the sample data first.", None, None, "", "Status: No dataset loaded."
        
    if not question.strip():
        return "Please ask a question.", None, None, "", "Status: Waiting for question."
        
    try:
        result = run_pipeline(
            question, 
            session["conn"], 
            session["schema"], 
            session["allowed_tables"]
        )
        
        err = result.get("error")
        if err and "Max retries exceeded" not in err:
            return result["answer_text"], None, None, "", f"Status: Error - {err}"
            
        ans_text = result["answer_text"]
        sql_text = f"```sql\n{result['sql']}\n```" if result['sql'] else ""
        df = result["dataframe"]
        chart_type = result["chart"]
        
        plot = None
        if df is not None and not df.empty:
            cols = df.columns
            types = df.dtypes
            date_cols = [c for c in cols if pd.api.types.is_datetime64_any_dtype(types[c]) or 'date' in c.lower()]
            num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(types[c]) and not c.endswith('_id')]
            cat_cols = [c for c in cols if c not in date_cols and c not in num_cols and not c.endswith('_id')]
            
            if chart_type == "line" and date_cols and num_cols:
                plot = px.line(df, x=date_cols[0], y=num_cols[0], title=f"{num_cols[0]} over {date_cols[0]}")
            elif chart_type == "bar" and cat_cols and num_cols:
                df_top = df.nlargest(10, num_cols[0])
                plot = px.bar(df_top, x=cat_cols[0], y=num_cols[0], title=f"Top 10 {cat_cols[0]} by {num_cols[0]}")
        
        if df is None:
            df = pd.DataFrame()
            
        status = f"Answered by {result['provider_used']} in {result['attempts']} attempt(s), {result['latency_ms']/1000:.1f} s"
        return ans_text, plot, df, sql_text, status
        
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}", None, None, "", "Status: Error"

def example_click(text):
    return text

with gr.Blocks(title="Hisaab AI (MVP)") as demo:
    gr.Markdown("# Hisaab AI 🛒 (Demo)")
    gr.Markdown("Talk to your shop data in English or Roman Urdu.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Load Data")
            file_upload = gr.File(label="Upload CSV or Excel (Max 5MB)", file_count="multiple")
            sample_btn = gr.Button("Use sample shop data", variant="primary")
            
            status_text = gr.Textbox(label="Status", interactive=False)
            schema_out = gr.Markdown("Schema will appear here...")
            
            with gr.Accordion("About & Limitations", open=False):
                gr.Markdown("""
                **Tech Stack:** DuckDB, Gradio, Plotly, Pandas, SQLGlot
                **LLM:** Groq API (GPT-OSS 20B)
                **Note:** 
                - Free-tier rate limits apply.
                - Max 1000 rows returned per query for safety.
                - Queries run in a sandboxed, read-only DuckDB session.
                - Small open-weight models may occasionally misinterpret complex logic.
                """)
                
        with gr.Column(scale=2):
            gr.Markdown("### 2. Ask a Question")
            q_input = gr.Textbox(label="Your Question", placeholder="e.g. pichle mahine sab se zyada kaunsa item bika?")
            
            gr.Markdown("**Example Questions:**")
            with gr.Row():
                ex1 = gr.Button("kis customer ka udhaar sab se zyada hai?")
                ex2 = gr.Button("pichle mahine ki total sale kitni thi?")
            with gr.Row():
                ex3 = gr.Button("What are the top 5 items sold?")
                ex4 = gr.Button("Show a trend of total sales over time")
                
            ask_btn = gr.Button("Ask", variant="primary")
            
            gr.Markdown("### Answer")
            answer_out = gr.Markdown()
            chart_out = gr.Plot()
            table_out = gr.Dataframe()
            
            with gr.Accordion("View SQL Query", open=False):
                sql_out = gr.Markdown()
                
            query_status = gr.Markdown("*Status: Waiting for question*")

    file_upload.upload(load_uploaded_file, inputs=[file_upload], outputs=[schema_out, status_text])
    sample_btn.click(load_sample_data, inputs=[], outputs=[schema_out, status_text])
    
    ex1.click(example_click, inputs=[ex1], outputs=[q_input])
    ex2.click(example_click, inputs=[ex2], outputs=[q_input])
    ex3.click(example_click, inputs=[ex3], outputs=[q_input])
    ex4.click(example_click, inputs=[ex4], outputs=[q_input])
    
    ask_btn.click(
        ask_question,
        inputs=[q_input],
        outputs=[answer_out, chart_out, table_out, sql_out, query_status]
    )
    q_input.submit(
        ask_question,
        inputs=[q_input],
        outputs=[answer_out, chart_out, table_out, sql_out, query_status]
    )

from fastapi import FastAPI
app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    demo.launch(auth=(config.DEMO_USER, config.DEMO_PASS), server_name="0.0.0.0")
