import os
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# chroma_db lives at the project root, one level above backend/
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

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
    for a PM-style root cause analysis grounded in those reviews.
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Senior Product Manager at Swiggy. Analyze the "
                    "following reviews and provide a root cause and a solution."),
        ("human", "Reviews:\n{context}\n\nQuestion: {question}")
    ])

    chain = prompt | llm
    response = chain.invoke({"context": context_text, "question": query})

    sources = [
        {"user": d.metadata["user"], "score": d.metadata["score"], "date": d.metadata["date"], "text": d.page_content}
        for d in docs
    ]

    return {"answer": response.content, "sources": sources}






import time
from datetime import datetime

def get_last_updated() -> str:
    if not CHROMA_DIR.exists():
        return "Never"
    mtime = CHROMA_DIR.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
import subprocess
import sys


PROJECT_ROOT = Path(__file__).parent.parent

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
            if CHROMA_DIR.exists():
                shutil.rmtree(CHROMA_DIR, ignore_errors=True)
            new_dir.rename(CHROMA_DIR)
        return {"success": True, "last_updated": get_last_updated()}

    except subprocess.TimeoutExpired:
        return {"success": False, "step": "timeout", "error": "Refresh took too long and was aborted."}
    except Exception as e:
        return {"success": False, "step": "unknown", "error": str(e)}