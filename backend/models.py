from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    k: int = Field(default=10, ge=1, le=20)


class SourceReview(BaseModel):
    user: str
    score: int
    date: str
    text: str


class AnalyzeResponse(BaseModel):
    answer: str
    sources: list[SourceReview]

class RefreshResponse(BaseModel):
    success: bool
    step: str | None = None
    error: str | None = None
    last_updated: str | None = None