from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stats import StatsResponse
from app.services.stats_service import get_stats

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    # Guest access is "Limited" per SRS 2.5; MVP exposes the same aggregate
    # counts to everyone since no sensitive data is included in them.
    return get_stats(db)
