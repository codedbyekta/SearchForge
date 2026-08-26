from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.cache.redis_client import cache_clear_prefix
from app.db.session import get_db
from app.services.indexing_service import rebuild_index_from_documents

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/index/rebuild")
def rebuild_index(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    count = rebuild_index_from_documents(db)
    cache_clear_prefix("search:")
    return {"status": "ok", "documents_indexed": count}


@router.post("/cache/clear")
def clear_cache(_admin=Depends(require_admin)):
    deleted = cache_clear_prefix("search:")
    return {"status": "ok", "keys_cleared": deleted}
