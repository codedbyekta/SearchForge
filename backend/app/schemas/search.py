from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    id: str
    title: str
    url: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total: int
    page: int
    limit: int
    latency_ms: float
    cached: bool = False
    mode: Literal["tfidf", "bm25", "hybrid"] = "bm25"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int
