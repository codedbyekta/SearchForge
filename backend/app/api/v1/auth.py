from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthError, authenticate

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = authenticate(db, request.username, request.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    from app.core.security import decode_access_token

    role = decode_access_token(token)["role"]
    return TokenResponse(access_token=token, role=role)
