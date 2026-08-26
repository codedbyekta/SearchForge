from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CrawlRequest(BaseModel):
    seed_url: str = Field(..., description="Valid HTTP/HTTPS URL to crawl")
    max_pages: int = Field(default=50, ge=1, le=500)
    max_depth: int = Field(default=2, ge=0, le=5)

    @field_validator("seed_url")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("seed_url must not be empty")
        return v.strip()


class CrawlJobResponse(BaseModel):
    id: str
    seed_url: str
    max_pages: int
    max_depth: int
    status: str
    pages_crawled: int
    pages_failed: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
