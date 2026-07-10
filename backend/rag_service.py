import os
import sys
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

_vectorstore = None
_llm = None

def load_components():
    """Lazily initialize the vectorstore and LLM once, reuse across requests."""
    global _vectorstore, _llm

    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings
        )

    if _llm is None:
        _llm = ChatGroq(temperature=0.1, model_name="llama-3.3-70b-versatile")

    return _vectorstore, _llm

def analyze_query(query: str, k: int = 10) -> dict:
    """
    Runs the RAG pipeline: retrieve top-k similar reviews, then ask the LLM
    for a PM/SDE-style root cause analysis grounded in those reviews.
    """
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            "Vector DB not found. Run scraper.py then build_vector_db.py first."
        )

    vectorstore, llm = load_components()

    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return {"answer": "No relevant reviews found for this query.", "sources": []}

    context_text = "\n\n".join(
        f"User {d.metadata['user']}: {d.page_content}" for d in docs
    )

    system_prompt = """
    You are a cross-functional expert acting as both a Lead Software Engineer and a Senior Product Manager at Swiggy.
    Your goal is to perform a strict, data-backed Root Cause Analysis (RCA) using ONLY the provided user reviews.

    CRITICAL RULES:
    1. NO HALLUCINATIONS: Do not guess or invent problems. If the reviews lack specific details (e.g., they just say "bad app"), explicitly output: "Error: Insufficient technical or product data in the retrieved reviews to determine a root cause."
    2. QUOTE THE DATA: You must back up every single finding with a short, direct quote from the provided reviews.
    3. DUAL-PERSPECTIVE ANALYSIS: You must structure your final answer into these two distinct sections:
   
   🛠️ Engineering Root Causes & Fixes:
   Focus on technical issues (e.g., API timeouts, memory leaks, database sync issues, location tracking failures, network drops).
   
   📊 Product & Operational Root Causes & Fixes:
   Focus on business logic and user experience (e.g., refund policies, payment UX friction, delivery executive routing, customer support response delays).
   """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Reviews:\n{context}\n\nQuestion: {question}\n\nProvide your structured Dual-Perspective Analysis:")
    ])

    chain = prompt | llm
    response = chain.invoke({"context": context_text, "question": query})

    sources = [
        {"user": d.metadata["user"], "score": d.metadata["score"], "date": d.metadata["date"], "text": d.page_content}
        for d in docs
    ]

    return {"answer": response.content, "sources": sources}

def get_last_updated() -> str:
    if not CHROMA_DIR.exists():
        return "Never"
    mtime = CHROMA_DIR.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

def refresh_data(review_count: int = 1000) -> dict:
    """Re-scrapes Play Store reviews and rebuilds the vector DB."""
    global _vectorstore  # force reload after rebuild

    _vectorstore = None
    try:
        scraper_result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scraper.py")],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=180,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        if scraper_result.returncode != 0:
            return {"success": False, "step": "scraping", "error": scraper_result.stderr[-500:]}

        build_result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "build_vector_db.py")],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        if build_result.returncode != 0:
            return {"success": False, "step": "vector_db_build", "error": build_result.stderr[-500:]}

        # Swap: remove old, rename new into place
        new_dir = PROJECT_ROOT / "chroma_db_new"
        if new_dir.exists():
            old_backup = PROJECT_ROOT / "chroma_db_old"
            if old_backup.exists():
                shutil.rmtree(old_backup, ignore_errors=True)
            if CHROMA_DIR.exists():
                CHROMA_DIR.rename(old_backup)
            new_dir.rename(CHROMA_DIR)
            shutil.rmtree(old_backup, ignore_errors=True)
        return {"success": True, "last_updated": get_last_updated()}

    except subprocess.TimeoutExpired:
        return {"success": False, "step": "timeout", "error": "Refresh took too long and was aborted."}
    except Exception as e:
        return {"success": False, "step": "unknown", "error": str(e)}