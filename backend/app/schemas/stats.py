from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatsResponse(BaseModel):
    document_count: int
    indexed_terms: int
    crawled_urls: int
    failed_urls: int
    last_indexing_time: Optional[datetime] = None
