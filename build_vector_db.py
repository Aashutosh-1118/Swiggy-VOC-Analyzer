import pandas as pd
import os
import shutil
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


def create_vector_db():
    print("🔄 Loading reviews from CSV...")
    if not os.path.exists("swiggy_negative_reviews.csv"):
        print("❌ Error: Run scraper.py first!")
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

    print(f"✅ Loaded {len(documents)} reviews. Building AI folder...")

    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")

    # This part might take a minute to download the model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    print("🚀 SUCCESS! 'chroma_db' folder created.")


if __name__ == "__main__":
    create_vector_db()