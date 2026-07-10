import pandas as pd
import os
import shutil
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


def create_vector_db():
    print("[INFO] Loading reviews from CSV...")
    if not os.path.exists("swiggy_negative_reviews.csv"):
        print("[ERROR] Run scraper.py first!")
        return

    df = pd.read_csv("swiggy_negative_reviews.csv")

    documents = []
    for _, row in df.iterrows():
        doc = Document(
            page_content=str(row['content']),
            metadata={
                "user": str(row['userName']),
                "score": int(row['score']),
                "date": str(row['at'])
            }
        )
        documents.append(doc)

    print(f"[INFO] Loaded {len(documents)} reviews. Building vector store...")

     # Build into a fresh temp folder instead of overwriting the live one
    temp_dir = "./chroma_db_new"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=temp_dir
    )

    print("[SUCCESS] New vector store built at chroma_db_new")


if __name__ == "__main__":
    create_vector_db()