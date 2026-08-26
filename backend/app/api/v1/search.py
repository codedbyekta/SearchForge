from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import SearchResponse
from app.services import search_service
from app.services.search_service import InvalidQueryError

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="Search query", alias="q"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    mode: str = Query("bm25", pattern="^(tfidf|bm25)$"),
    db: Session = Depends(get_db),
):
    try:
        return search_service.search(db, query=q, page=page, limit=limit, mode=mode)
    except InvalidQueryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
