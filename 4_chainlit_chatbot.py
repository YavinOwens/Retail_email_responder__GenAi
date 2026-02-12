# app.py
<<<<<<< HEAD
"""
Retail Email Responder – Full Data Agent Mode
=============================================

Features:
- Static source toggles
- CSV / XLSX upload
=======

"""
Retail Email Responder – Full Data Agent Mode + Document Context
=============================================
Features:
- Static source toggles
- CSV / XLSX upload (data analysis)
- TXT/PDF/DOCX upload (document context)
>>>>>>> main
- DataFrame memory
- LLM-generated pandas analysis
- Safe execution sandbox
- Result explanation
<<<<<<< HEAD
=======

Compatible with Chainlit < 1.0
>>>>>>> main
"""

import os
import re
import io
import traceback
from pathlib import Path
from typing import Dict, List, Optional
<<<<<<< HEAD

=======
>>>>>>> main
import chainlit as cl
from chainlit.input_widget import Switch
from dotenv import load_dotenv
from ollama import Client
import pandas as pd

<<<<<<< HEAD
# ----------------------------------------------------------------------
# 1️⃣ Environment
# ----------------------------------------------------------------------

load_dotenv()

=======
# Optional document loaders
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ----------------------------------------------------------------------
# 1️⃣ Environment
# ----------------------------------------------------------------------
load_dotenv()
>>>>>>> main
OLLAMA_API_KEY = os.getenv("ollama_api_key")
OLLAMA_URL = os.getenv("ollama_url", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

# ----------------------------------------------------------------------
# 2️⃣ Ollama Client
# ----------------------------------------------------------------------
<<<<<<< HEAD

=======
>>>>>>> main
def create_ollama_client() -> Client:
    if OLLAMA_API_KEY:
        return Client(host=OLLAMA_URL, headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"})
    return Client(host=OLLAMA_URL)

ollama_client = create_ollama_client()

# ----------------------------------------------------------------------
# 3️⃣ Static Sources
# ----------------------------------------------------------------------
<<<<<<< HEAD

BASE_DIR = Path(__file__).parent
SOURCE_DIR = BASE_DIR / "sources"

=======
BASE_DIR = Path(__file__).parent
SOURCE_DIR = BASE_DIR / "sources"
>>>>>>> main
SOURCE_FILES: Dict[str, Path] = {
    "Wikipedia": SOURCE_DIR / "wikipedia.txt",
    "Company Docs": SOURCE_DIR / "company_docs.txt",
    "News Articles": SOURCE_DIR / "news.txt",
}

def read_source(name: str) -> str:
    path = SOURCE_FILES.get(name)
    return path.read_text(encoding="utf-8") if path and path.is_file() else ""

# ----------------------------------------------------------------------
<<<<<<< HEAD
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

=======
# 4️⃣ Document Parsing Utilities
# ----------------------------------------------------------------------
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    if not PDF_AVAILABLE:
        return "[PDF parsing not available. Install PyPDF2]"
    
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
        return "\n".join(text_parts)
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    if not DOCX_AVAILABLE:
        return "[DOCX parsing not available. Install python-docx]"
    
    try:
        doc = DocxDocument(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"[Error reading DOCX: {str(e)}]"

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            return f"[Error reading TXT: {str(e)}]"

def extract_document_text(file_path: str, filename: str) -> Optional[str]:
    """Extract text from various document formats."""
    lower_name = filename.lower()
    
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif lower_name.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif lower_name.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        return None

# ----------------------------------------------------------------------
# 5️⃣ Data Agent Utilities
# ----------------------------------------------------------------------
MAX_PREVIEW_ROWS = 5

def parse_tabular_file(file_path: str, filename: str):
    """Parse CSV or Excel files."""
    if filename.lower().endswith(".csv"):
        return pd.read_csv(file_path)
    elif filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file type")

def generate_analysis_code(question: str, df_summaries: str) -> str:
    """Ask LLM to generate safe pandas code."""
    system_prompt = """
You are a Python data analyst.
>>>>>>> main
Generate ONLY valid pandas code.
Do NOT include explanations.
Do NOT use import statements.
Do NOT access files, OS, network, or system.
Only use the provided dataframes dictionary.
<<<<<<< HEAD

The dataframes are available as:
dataframes["filename"]

Store final answer in variable: result
"""

=======
The dataframes are available as:
    dataframes["filename"]
Store final answer in variable: result
"""
>>>>>>> main
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": df_summaries},
        {"role": "user", "content": question},
    ]
<<<<<<< HEAD

    resp = ollama_client.chat(model=OLLAMA_MODEL, messages=messages)
    return resp["message"]["content"].strip()


def execute_code_safely(code: str, dataframes: Dict[str, pd.DataFrame]):
    """
    Execute generated pandas code in restricted environment.
    """

=======
    resp = ollama_client.chat(model=OLLAMA_MODEL, messages=messages)
    return resp["message"]["content"].strip()

def execute_code_safely(code: str, dataframes: Dict[str, pd.DataFrame]):
    """Execute generated pandas code in restricted environment."""
>>>>>>> main
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
<<<<<<< HEAD

=======
>>>>>>> main
    for pattern in forbidden_patterns:
        if pattern in code:
            raise ValueError(f"Unsafe code detected: {pattern}")

    local_env = {
        "pd": pd,
        "dataframes": dataframes,
    }
<<<<<<< HEAD

    exec(code, {}, local_env)

    if "result" not in local_env:
        raise ValueError("No result variable produced.")

    return local_env["result"]


def summarize_dataframes(dataframes: Dict[str, pd.DataFrame]) -> str:
=======
    exec(code, {}, local_env)
    
    if "result" not in local_env:
        raise ValueError("No result variable produced.")
    
    return local_env["result"]

def summarize_dataframes(dataframes: Dict[str, pd.DataFrame]) -> str:
    """Summarize dataframes for LLM context."""
>>>>>>> main
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
<<<<<<< HEAD
# 5️⃣ Chainlit Lifecycle
# ----------------------------------------------------------------------

@cl.on_chat_start
async def init_settings():
=======
# 6️⃣ File Processing Functions
# ----------------------------------------------------------------------
async def process_uploaded_files(files: List) -> tuple:
    """Process uploaded files and return dataframes and documents."""
    stored_dfs = {}
    stored_docs = {}
    data_files = []
    doc_files = []
    errors = []
    
    for file in files:
        filename = file.name
        file_path = file.path
        
        # Try to parse as tabular data
        if filename.lower().endswith((".csv", ".xlsx", ".xls")):
            try:
                df = parse_tabular_file(file_path, filename)
                stored_dfs[filename] = df
                data_files.append(filename)
            except Exception as e:
                errors.append(f"❌ Error loading {filename}: {str(e)}")
        else:
            # Try to parse as document
            text = extract_document_text(file_path, filename)
            if text:
                stored_docs[filename] = text
                doc_files.append(filename)
            else:
                errors.append(f"⚠️ Unsupported file type: {filename}. Supported: CSV, XLSX, TXT, PDF, DOCX")
    
    return stored_dfs, stored_docs, data_files, doc_files, errors

# ----------------------------------------------------------------------
# 7️⃣ Chainlit Lifecycle
# ----------------------------------------------------------------------
@cl.on_chat_start
async def init_settings():
    """Initialize chat settings and session."""
>>>>>>> main
    settings = await cl.ChatSettings(
        [
            Switch(id="Wikipedia", label="Wikipedia", initial=True),
            Switch(id="CompanyDocs", label="Company Docs", initial=True),
            Switch(id="News", label="News Articles", initial=True),
        ]
    ).send()
<<<<<<< HEAD

=======
    
>>>>>>> main
    cl.user_session.set("active_sources", {
        "Wikipedia": settings["Wikipedia"],
        "Company Docs": settings["CompanyDocs"],
        "News Articles": settings["News"],
    })
<<<<<<< HEAD

    cl.user_session.set("dataframes", {})


@cl.on_settings_update
async def update_settings(settings):
=======
    cl.user_session.set("dataframes", {})
    cl.user_session.set("uploaded_documents", {})
    
    # Welcome message with upload instructions
    welcome = """Welcome! 👋

You can:
1. Ask questions about the knowledge base (toggle sources in settings)
2. Upload files for analysis:
   - **Data files** (CSV, XLSX) → Data analysis mode
   - **Documents** (TXT, PDF, DOCX) → Will be used as context

To upload files, use the command: `/upload`
"""
    await cl.Message(content=welcome).send()

@cl.on_settings_update
async def update_settings(settings):
    """Update active sources when settings change."""
>>>>>>> main
    cl.user_session.set("active_sources", {
        "Wikipedia": settings["Wikipedia"],
        "Company Docs": settings["CompanyDocs"],
        "News Articles": settings["News"],
    })

<<<<<<< HEAD

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

=======
# ----------------------------------------------------------------------
# 8️⃣ Main Message Handler
# ----------------------------------------------------------------------
@cl.on_message
async def main(message: cl.Message):
    """Main message handler."""
    question = message.content.strip()
    
    # Handle upload command
    if question.lower() == "/upload":
        files = await cl.AskFileMessage(
            content="📎 Please upload your files (CSV, XLSX, TXT, PDF, or DOCX):",
            accept=["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                   "application/vnd.ms-excel", "text/plain", "application/pdf", 
                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            max_files=10
        ).send()
        
        if files:
            # Process files
            stored_dfs, stored_docs, data_files, doc_files, errors = await process_uploaded_files(files)
            
            # Update session
            current_dfs = cl.user_session.get("dataframes", {})
            current_docs = cl.user_session.get("uploaded_documents", {})
            current_dfs.update(stored_dfs)
            current_docs.update(stored_docs)
            cl.user_session.set("dataframes", current_dfs)
            cl.user_session.set("uploaded_documents", current_docs)
            
            # Send feedback
            messages = []
            if data_files:
                messages.append(f"📊 {len(data_files)} dataset(s) uploaded: {', '.join(data_files)}")
            if doc_files:
                messages.append(f"📄 {len(doc_files)} document(s) uploaded: {', '.join(doc_files)}")
            if errors:
                messages.extend(errors)
            
            if messages:
                await cl.Message(content="\n".join(messages)).send()
        return
    
    # Get session data
    dataframes = cl.user_session.get("dataframes", {})
    active_sources = cl.user_session.get("active_sources", {})
    uploaded_docs = cl.user_session.get("uploaded_documents", {})
    
>>>>>>> main
    # If we have datasets → Data Agent Mode
    if dataframes:
        try:
            df_summary = summarize_dataframes(dataframes)
<<<<<<< HEAD

            code = generate_analysis_code(question, df_summary)

            result = execute_code_safely(code, dataframes)

=======
            code = generate_analysis_code(question, df_summary)
            result = execute_code_safely(code, dataframes)
            
>>>>>>> main
            explanation_prompt = f"""
The user asked:
{question}

The computed result is:
{result}

Explain the answer clearly and concisely.
Cite dataset names in square brackets.
"""
<<<<<<< HEAD

=======
>>>>>>> main
            explanation = ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": explanation_prompt}],
            )["message"]["content"]
<<<<<<< HEAD

            await cl.Message(content=explanation).send()

=======
            
            await cl.Message(content=explanation).send()
        
>>>>>>> main
        except Exception as e:
            await cl.Message(
                content=f"❗ Data analysis error:\n{str(e)}\n\n{traceback.format_exc()}"
            ).send()
<<<<<<< HEAD

    else:
        # Fallback to normal chat
        context_parts = []

        for name, enabled in active_sources.items():
            if enabled:
                context_parts.append(f"### {name}\n{read_source(name)}")

=======
    
    else:
        # Fallback to normal chat with context
        context_parts = []
        
        # Add static sources
        for name, enabled in active_sources.items():
            if enabled:
                source_text = read_source(name)
                if source_text:
                    context_parts.append(f"### {name}\n{source_text}")
        
        # Add uploaded documents
        for doc_name, doc_text in uploaded_docs.items():
            if doc_text:
                context_parts.append(f"### {doc_name}\n{doc_text}")
        
>>>>>>> main
        system_prompt = """
You are a helpful assistant.
Use only provided context.
Cite sources in square brackets.
"""
<<<<<<< HEAD

=======
        
>>>>>>> main
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": "\n\n".join(context_parts)},
            {"role": "user", "content": question},
        ]
<<<<<<< HEAD

        response = ollama_client.chat(model=OLLAMA_MODEL, messages=messages)

        await cl.Message(content=response["message"]["content"]).send()

# ----------------------------------------------------------------------
# 7️⃣ Run
# ----------------------------------------------------------------------

=======
        
        response = ollama_client.chat(model=OLLAMA_MODEL, messages=messages)
        await cl.Message(content=response["message"]["content"]).send()

# ----------------------------------------------------------------------
# 9️⃣ Run
# ----------------------------------------------------------------------
>>>>>>> main
if __name__ == "__main__":
    cl.run()
