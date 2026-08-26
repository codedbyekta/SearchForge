"""
ORM models matching SRS 2.7 Data Requirements.

Document: id, url, canonical_url, title, content, content_hash, word_count,
          status, created_at, updated_at.
CrawlJob: id, seed_url, max_pages, max_depth, status, pages_crawled,
          pages_failed, started_at, completed_at.
CrawlURL: id, crawl_job_id, url, depth, status, http_status, error.
SearchLog (optional MVP+): id, query, result_count, latency_ms, created_at.
User: administrative accounts (JWT auth).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DocumentStatus(str, enum.Enum):
    INDEXED = "indexed"
    FAILED = "failed"
    PENDING = "pending"


class CrawlJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlURLStatus(str, enum.Enum):
    QUEUED = "queued"
    FETCHED = "fetched"
    FAILED = "failed"
    SKIPPED_DUPLICATE = "skipped_duplicate"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("canonical_url", name="uq_document_canonical_url"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    url = Column(String(2048), nullable=False)
    canonical_url = Column(String(2048), nullable=False, index=True)
    title = Column(String(1024), nullable=True)
    content = Column(Text, nullable=False, default="")
    content_hash = Column(String(64), nullable=False, index=True)
    word_count = Column(Integer, nullable=False, default=0)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    seed_url = Column(String(2048), nullable=False)
    max_pages = Column(Integer, nullable=False)
    max_depth = Column(Integer, nullable=False)
    status = Column(Enum(CrawlJobStatus), nullable=False, default=CrawlJobStatus.PENDING)
    pages_crawled = Column(Integer, nullable=False, default=0)
    pages_failed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    urls = relationship("CrawlURL", back_populates="crawl_job", cascade="all, delete-orphan")


class CrawlURL(Base):
    __tablename__ = "crawl_urls"
    __table_args__ = (UniqueConstraint("crawl_job_id", "url", name="uq_crawl_job_url"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    crawl_job_id = Column(UUID(as_uuid=False), ForeignKey("crawl_jobs.id"), nullable=False)
    url = Column(String(2048), nullable=False)
    depth = Column(Integer, nullable=False, default=0)
    status = Column(Enum(CrawlURLStatus), nullable=False, default=CrawlURLStatus.QUEUED)
    http_status = Column(Integer, nullable=True)
    error = Column(String(1024), nullable=True)

    crawl_job = relationship("CrawlJob", back_populates="urls")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    query = Column(String(500), nullable=False)
    result_count = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    username = Column(String(150), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
