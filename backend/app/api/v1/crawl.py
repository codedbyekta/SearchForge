from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.url_safety import URLSafetyError
from app.db.models import CrawlJob
from app.db.session import get_db
from app.schemas.crawl import CrawlJobResponse, CrawlRequest
from app.services.crawl_service import start_crawl_job

router = APIRouter(prefix="/api/v1", tags=["crawl"])


@router.post("/crawl", response_model=CrawlJobResponse, status_code=201)
def create_crawl(
    request: CrawlRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    try:
        job = start_crawl_job(db, request.seed_url, request.max_pages, request.max_depth)
    except URLSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return job


@router.get("/crawl/{job_id}", response_model=CrawlJobResponse)
def get_crawl(job_id: str, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    job = db.execute(select(CrawlJob).where(CrawlJob.id == job_id)).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return job
