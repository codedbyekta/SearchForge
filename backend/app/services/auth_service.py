from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.models import User


class AuthError(ValueError):
    pass


def authenticate(db: Session, username: str, password: str) -> str:
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid username or password")
    return create_access_token(subject=user.username, role=user.role.value)
