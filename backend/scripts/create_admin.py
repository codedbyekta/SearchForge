"""
Create (or update) an administrator account.

Usage:
    python -m scripts.create_admin --username admin --password changeme
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.models import User, UserRole
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        existing = db.execute(select(User).where(User.username == args.username)).scalar_one_or_none()
        if existing:
            existing.hashed_password = hash_password(args.password)
            existing.role = UserRole.ADMIN
            print(f"Updated existing admin user '{args.username}'.")
        else:
            db.add(User(username=args.username, hashed_password=hash_password(args.password), role=UserRole.ADMIN))
            print(f"Created admin user '{args.username}'.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
