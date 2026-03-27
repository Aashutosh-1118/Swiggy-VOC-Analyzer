#  Swiggy VoC Analyzer: AI-Powered Product Strategy Engine

### 📌 Project Overview
The **Swiggy Voice of Customer (VoC) Analyzer** is a sophisticated **RAG (Retrieval-Augmented Generation)** application designed to transform raw consumer complaints into actionable product insights. 

By scraping thousands of 1-star reviews from the Google Play Store, the engine uses a **Vector Database (ChromaDB)** and **Llama 3.3 (via Groq)** to identify root causes of user friction and suggest high-impact features for the Swiggy product roadmap.

---

### 🚀 How It Works (The Architecture)

The system follows a standard RAG pipeline to ensure accuracy and reduce AI hallucinations:

1.  **Data Extraction:** A custom scraper pulls real-time, negative reviews from the Swiggy Play Store page.
2.  **Vectorization:** Raw text is converted into high-dimensional mathematical vectors using the `all-MiniLM-L6-v2` HuggingFace model.
3.  **Semantic Storage:** These vectors are stored in **ChromaDB**, allowing the system to search by "meaning" rather than just keywords (e.g., searching for "money" will find reviews about "refunds").
4.  **Contextual Intelligence:** When a user asks a question, the top 10 most relevant reviews are retrieved and sent to **Llama 3.3-70B** to generate a Senior PM-level analysis.

---

### 🛠️ Tech Stack
* **Language:** Python 3.10
* **Orchestration:** LangChain
* **Vector Database:** ChromaDB
* **LLM:** Llama 3.3-70B (Groq Cloud API)
* **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
* **Frontend:** Streamlit
* **Data Source:** `google-play-scraper`

---

### 🚦 Running the Project (The Pipeline)

To build and launch the engine, run the scripts in this specific order:

1. **Scrape Data:**
   `python scraper.py`
   *Extracts the latest 1-star reviews from the Google Play Store into a local CSV.*

2. **Build the AI Model:**
   `python build_vector_db.py`
   *Converts raw text into mathematical vectors and stores them in the `chroma_db` folder.*

3. **Launch Dashboard:**
   `streamlit run app.py`
   *Starts the interactive web interface for real-time Product Management analysis.*

---

### 📊 Key Features

* **Semantic Search:** Uses vector embeddings to find relevant complaints based on context and meaning, rather than simple keyword matching.
* **PM-Level Analysis:** Automatically generates structured **Root Cause Analysis** and **Actionable Product Plans** for every query.
* **Username Integration:** Tracks and displays the specific user associated with each review for authentic data tracking.
* **Evidence Transparency:** Includes a dedicated "Source Reviews" panel to show the exact raw data used by the AI to reach its conclusions.
* **High-Speed Inference:** Powered by **Groq’s LPU** (Language Processing Unit) for near-instant response generation using Llama 3.3.