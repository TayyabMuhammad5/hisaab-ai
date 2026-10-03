import os
import time
from groq import Groq
from typing import List, Tuple
from . import config

def strip_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        newline_idx = text.find("\n")
        if newline_idx != -1:
            text = text[newline_idx+1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()

def generate_sql(messages: List[dict]) -> Tuple[str, str, float]:
    """Returns (sql, provider, latency_ms)"""
    start_time = time.time()
    
    groq_api_key = os.environ.get("GROQ_API_KEY")
    groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
    
    try:
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not set.")
            
        client = Groq(api_key=groq_api_key, timeout=config.GROQ_TIMEOUT_S)
        
        response = client.chat.completions.create(
            model=groq_model,
            messages=messages,
            temperature=0.0,
            max_tokens=500
        )
        raw_text = response.choices[0].message.content
        provider = f"Groq ({groq_model})"
        
    except Exception as e:
        raise RuntimeError(f"Groq API failed: {e}")
            
    latency_ms = (time.time() - start_time) * 1000
    sql = strip_markdown(raw_text)
    
    return sql, provider, latency_ms
