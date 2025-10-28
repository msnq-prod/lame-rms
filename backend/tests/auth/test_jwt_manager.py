from __future__ import annotations

from datetime import timedelta

import pytest

from app.auth.jwt import JWTDecodingError, JWTManager


def test_jwt_manager_roundtrip() -> None:
    manager = JWTManager("secret-key", algorithm="HS256", issuer="adamrms")
    token = manager.encode({"sub": "user-1", "jti": "abc", "type": "access"}, timedelta(minutes=1))
    payload = manager.decode(token)
    assert payload.sub == "user-1"
    assert payload.type == "access"
    assert payload.jti == "abc"


def test_jwt_manager_rejects_modified_token() -> None:
    manager = JWTManager("secret-key", algorithm="HS256")
    token = manager.encode({"sub": "user-1", "jti": "abc", "type": "access"}, timedelta(minutes=1))
    # Tamper with token by flipping a bit
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(JWTDecodingError):
        manager.decode(tampered)
