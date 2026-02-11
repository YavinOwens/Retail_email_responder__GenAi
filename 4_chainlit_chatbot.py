# app.py
"""
Retail Email Responder – Full Data Agent Mode
=============================================

Features:
- Static source toggles
- CSV / XLSX upload
- DataFrame memory
- LLM-generated pandas analysis
- Safe execution sandbox
- Result explanation
"""

import os
import re
import io
import traceback
from pathlib import Path
from typing import Dict, List, Optional

import chainlit as cl
from chainlit.input_widget import Switch
from dotenv import load_dotenv
from ollama import Client
import pandas as pd

# ----------------------------------------------------------------------
# 1️⃣ Environment
# ----------------------------------------------------------------------

load_dotenv()

OLLAMA_API_KEY = os.getenv("ollama_api_key")
OLLAMA_URL = os.getenv("ollama_url", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

# ----------------------------------------------------------------------
# 2️⃣ Ollama Client
# ----------------------------------------------------------------------

def create_ollama_client() -> Client:
    if OLLAMA_API_KEY:
        return Client(host=OLLAMA_URL, headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"})
    return Client(host=OLLAMA_URL)

ollama_client = create_ollama_client()

# ----------------------------------------------------------------------
# 3️⃣ Static Sources
# ----------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
SOURCE_DIR = BASE_DIR / "sources"

SOURCE_FILES: Dict[str, Path] = {
    "Wikipedia": SOURCE_DIR / "wikipedia.txt",
    "Company Docs": SOURCE_DIR / "company_docs.txt",
    "News Articles": SOURCE_DIR / "news.txt",
}

def read_source(name: str) -> str:
    path = SOURCE_FILES.get(name)
    return path.read_text(encoding="utf-8") if path and path.is_file() else ""

# ----------------------------------------------------------------------
# 4️⃣ Data Agent Utilities
# ----------------------------------------------------------------------

MAX_PREVIEW_ROWS = 5


def parse_tabular_file(file_bytes: bytes, filename: str):
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    elif filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file type")


def generate_analysis_code(question: str, df_summaries: str) -> str:
    """
    Ask LLM to generate safe pandas code.
    """
    system_prompt = """
You are a Python data analyst.

Generate ONLY valid pandas code.
Do NOT include explanations.
Do NOT use import statements.
Do NOT access files, OS, network, or system.
Only use the provided dataframes dictionary.

The dataframes are available as:
dataframes["filename"]

Store final answer in variable: result
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": df_summaries},
        {"role": "user", "content": question},
    ]

    resp = ollama_client.chat(model=OLLAMA_MODEL, messages=messages)
    return resp["message"]["content"].strip()


def execute_code_safely(code: str, dataframes: Dict[str, pd.DataFrame]):
    """
    Execute generated pandas code in restricted environment.
    """

    forbidden_patterns = [
        "import",
        "open(",
        "exec(",
        "eval(",
        "__",
        "os.",
        "sys.",
        "subprocess",
        "socket",
    ]

    for pattern in forbidden_patterns:
        if pattern in code:
            raise ValueError(f"Unsafe code detected: {pattern}")

    local_env = {
        "pd": pd,
        "dataframes": dataframes,
    }

    exec(code, {}, local_env)

    if "result" not in local_env:
        raise ValueError("No result variable produced.")

    return local_env["result"]


def summarize_dataframes(dataframes: Dict[str, pd.DataFrame]) -> str:
    parts = []
    for name, df in dataframes.items():
        parts.append(
            f"""
Dataset: {name}
Shape: {df.shape}
Columns: {list(df.columns)}
Preview:
{df.head(MAX_PREVIEW_ROWS).to_markdown(index=False)}
"""
        )
    return "\n\n".join(parts)

# ----------------------------------------------------------------------
# 5️⃣ Chainlit Lifecycle
# ----------------------------------------------------------------------

@cl.on_chat_start
async def init_settings():
    settings = await cl.ChatSettings(
        [
            Switch(id="Wikipedia", label="Wikipedia", initial=True),
            Switch(id="CompanyDocs", label="Company Docs", initial=True),
            Switch(id="News", label="News Articles", initial=True),
        ]
    ).send()

    cl.user_session.set("active_sources", {
        "Wikipedia": settings["Wikipedia"],
        "Company Docs": settings["CompanyDocs"],
        "News Articles": settings["News"],
    })

    cl.user_session.set("dataframes", {})


@cl.on_settings_update
async def update_settings(settings):
    cl.user_session.set("active_sources", {
        "Wikipedia": settings["Wikipedia"],
        "Company Docs": settings["CompanyDocs"],
        "News Articles": settings["News"],
    })


@cl.on_file_upload
async def on_file_upload(files: List[cl.File]):
    stored_dfs = cl.user_session.get("dataframes", {})

    for file in files:
        content = await file.read()
        df = parse_tabular_file(content, file.name)
        stored_dfs[file.name] = df

    cl.user_session.set("dataframes", stored_dfs)

    await cl.Message(
        content=f"✅ {len(files)} dataset(s) uploaded and ready for analysis."
    ).send()

# ----------------------------------------------------------------------
# 6️⃣ Main Message Handler
# ----------------------------------------------------------------------

@cl.on_message
async def main(message: cl.Message):

    question = message.content.strip()
    dataframes = cl.user_session.get("dataframes", {})
    active_sources = cl.user_session.get("active_sources", {})

    # If we have datasets → Data Agent Mode
    if dataframes:
        try:
            df_summary = summarize_dataframes(dataframes)

            code = generate_analysis_code(question, df_summary)

            result = execute_code_safely(code, dataframes)

            explanation_prompt = f"""
The user asked:
{question}

The computed result is:
{result}

Explain the answer clearly and concisely.
Cite dataset names in square brackets.
"""

            explanation = ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": explanation_prompt}],
            )["message"]["content"]

            await cl.Message(content=explanation).send()

        except Exception as e:
            await cl.Message(
                content=f"❗ Data analysis error:\n{str(e)}\n\n{traceback.format_exc()}"
            ).send()

    else:
        # Fallback to normal chat
        context_parts = []

        for name, enabled in active_sources.items():
            if enabled:
                context_parts.append(f"### {name}\n{read_source(name)}")

        system_prompt = """
You are a helpful assistant.
Use only provided context.
Cite sources in square brackets.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "\n\n".join(context_parts)},
            {"role": "user", "content": question},
        ]

        response = ollama_client.chat(model=OLLAMA_MODEL, messages=messages)

        await cl.Message(content=response["message"]["content"]).send()

# ----------------------------------------------------------------------
# 7️⃣ Run
# ----------------------------------------------------------------------

if __name__ == "__main__":
    cl.run()
