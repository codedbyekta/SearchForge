"""
Minimal schema bootstrap for the MVP.

For a real production rollout this would be replaced/complemented by Alembic
migrations, but `create_all` is sufficient to satisfy Phase 1 ("clean
migrations pass") for the portfolio-scale MVP described in the docs.
"""
from app.db.base import Base
from app.db.session import engine

# Import models so they are registered on Base.metadata before create_all.
from app.db import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created.")
