import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("s3cret!")
    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_roundtrip_contains_role():
    token = create_access_token(subject="admin_user", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "admin_user"
    assert payload["role"] == "admin"


def test_jwt_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_access_token("not-a-real-token")
