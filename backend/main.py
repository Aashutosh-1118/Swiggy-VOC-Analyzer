from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends

from .models import AnalyzeRequest, AnalyzeResponse
from .rag_service import analyze_query
from .auth import verify_api_key

app = FastAPI(title="Swiggy VoC Analyzer API")


@app.get("/health")
def health():
    """Unauthenticated — used for uptime checks / deployment health probes."""
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, authorized: bool = Depends(verify_api_key)):
    try:
        return analyze_query(payload.query, payload.k)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    


from .rag_service import refresh_data, get_last_updated
from .models import RefreshResponse

@app.get("/last-updated")
def last_updated():
    return {"last_updated": get_last_updated()}

@app.post("/refresh", response_model=RefreshResponse)
def refresh(authorized: bool = Depends(verify_api_key)):
    return refresh_data()