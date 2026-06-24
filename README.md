# Swiggy VoC Analyzer: AI-Powered Product Strategy Engine

## 📌 Project Overview

The **Swiggy Voice of Customer (VoC) Analyzer** is a RAG (Retrieval-Augmented Generation) application that transforms raw consumer complaints into actionable product insights.

It scrapes 1-star reviews from the Google Play Store, stores them in a vector database (ChromaDB), and uses Llama 3.3 (via Groq) to identify root causes of user friction and suggest high-impact product fixes — grounded in real, cited review evidence rather than generic guesses.

The project is built as a **decoupled API + frontend system**, not a single script: a FastAPI backend handles retrieval, analysis, authentication, and data refresh; a Streamlit frontend provides the interactive UI and talks to the backend over HTTP.

---

## 🏗️ Architecture

```
metric-rootcause-analyzer/
├── backend/
│   ├── main.py          # FastAPI app — routes, error handling
│   ├── auth.py          # API key authentication
│   ├── models.py        # Pydantic request/response schemas
│   └── rag_service.py   # RAG pipeline + data-refresh logic
├── frontend/
│   └── app.py            # Streamlit UI — calls the backend over HTTP
├── scraper.py             # Scrapes 1-star reviews from Google Play Store
├── build_vector_db.py     # Builds the ChromaDB vector store from scraped reviews
├── requirements.txt
└── .env                   # API keys (not committed — see Setup)
```

**Why this structure:** separating the RAG logic into a standalone API means the frontend is just a thin client. The same backend could serve a different frontend, a CLI tool, or another service without any code duplication.

---

## 🚀 How It Works

1. **Data Extraction** — `scraper.py` pulls the latest 1-star reviews from the Swiggy Play Store page via `google-play-scraper`.
2. **Vectorization** — Review text is embedded into vectors using HuggingFace's `all-MiniLM-L6-v2` model.
3. **Semantic Storage** — Vectors are stored in **ChromaDB**, enabling search by meaning rather than exact keywords (e.g., a search for "money" surfaces reviews about refunds).
4. **Retrieval + Analysis** — On query, the top-k most relevant reviews are retrieved and passed to **Llama 3.3-70B** (via Groq), which generates a structured root-cause analysis grounded in those specific reviews. LangChain orchestrates this pipeline — chaining the retriever, prompt template, and LLM call together.
5. **Data Refresh** — Since Play Store reviews go stale, the system supports re-scraping and rebuilding the vector store on demand via an authenticated API endpoint, without taking the running service down.

---

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Backend API | FastAPI |
| Frontend | Streamlit |
| Orchestration | LangChain (chains together retriever, prompt template, and LLM call) |
| Vector Database | ChromaDB |
| LLM | Llama 3.3-70B (Groq Cloud API) |
| Embeddings | HuggingFace (`all-MiniLM-L6-v2`) |
| Data Source | `google-play-scraper` |
| Auth | API key (header-based) |

---

## ⚙️ Setup

### 1. Clone and install dependencies
```bash
git clone <your-repo-url>
cd metric-rootcause-analyzer
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file in the project root:
```
GROQ_API_KEY=your-groq-api-key
API_KEY=choose-any-secret-string
API_URL=http://localhost:8000
```
- `GROQ_API_KEY` — from [console.groq.com](https://console.groq.com)
- `API_KEY` — a secret you choose yourself, used to authenticate requests to your own backend
- `API_URL` — where the backend is running (`http://localhost:8000` for local dev)

### 3. Build the initial dataset
```bash
python scraper.py
python build_vector_db.py
```

### 4. Run the backend
```bash
uvicorn backend.main:app --reload
```
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### 5. Run the frontend (in a separate terminal)
```bash
streamlit run frontend/app.py
```
Visit `http://localhost:8501`.

---

## 📡 API Endpoints

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| GET | `/health` | No | Health check for uptime monitoring |
| POST | `/analyze` | Yes | Runs RAG analysis on a query, returns answer + source reviews |
| GET | `/last-updated` | No | Returns when the vector store was last rebuilt |
| POST | `/refresh` | Yes | Re-scrapes reviews and rebuilds the vector store |

Authenticated requests require an `x-api-key` header matching your `.env`'s `API_KEY`.


---

## 📊 Key Features

- **Semantic Search** — Finds relevant complaints by meaning, not exact keyword match.
- **PM-Level Analysis** — Generates structured root-cause analysis and actionable recommendations per query, with sources cited.
- **Evidence Transparency** — Every analysis links back to the specific reviews (with username, rating, and date) it was grounded in.
- **On-Demand Data Refresh** — A single authenticated endpoint re-scrapes and rebuilds the dataset without downtime, using a build-new-then-swap strategy to avoid file-lock issues during rebuild.
- **Resilient Failure Handling** — Scraping failures, missing vector stores, and timeout conditions all return clean, descriptive errors instead of crashing.

---

## ⚠️ Known Limitations

- The dataset reflects a **rolling window of the latest ~1000 1-star reviews**, not real-time updates — refreshing shifts the window forward but doesn't guarantee every review is brand-new.
- Designed for a single-user / demo context; the vector store is shared in-memory, not isolated per concurrent user.
- No automated test suite yet (planned).

---

