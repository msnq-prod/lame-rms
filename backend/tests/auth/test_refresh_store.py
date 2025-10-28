from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.auth.models import RefreshTokenMetadata
from app.auth.refresh import RefreshTokenError, RefreshTokenStore


def make_metadata(**kwargs) -> RefreshTokenMetadata:
    base = {
        "jti": "token-1",
        "session": "session-1",
        "user_id": "user-1",
        "issued_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "scopes": ["scope:a"],
        "mfa": False,
    }
    base.update(kwargs)
    return RefreshTokenMetadata(**base)


def test_register_and_validate_refresh_token() -> None:
    store = RefreshTokenStore()
    metadata = make_metadata()
    store.register("secret-token", metadata)
    validated = store.validate("secret-token")
    assert validated.jti == metadata.jti
    assert validated.session == metadata.session


def test_validate_unknown_token_raises() -> None:
    store = RefreshTokenStore()
    with pytest.raises(RefreshTokenError):
        store.validate("missing")


def test_expired_token_is_rejected() -> None:
    store = RefreshTokenStore()
    metadata = make_metadata(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    store.register("secret-token", metadata)
    with pytest.raises(RefreshTokenError):
        store.validate("secret-token")


def test_revoke_session_revokes_all_tokens() -> None:
    store = RefreshTokenStore()
    metadata1 = make_metadata(jti="token-1", session="session-1")
    metadata2 = make_metadata(jti="token-2", session="session-1")
    metadata3 = make_metadata(jti="token-3", session="session-2")
    store.register("token-a", metadata1)
    store.register("token-b", metadata2)
    store.register("token-c", metadata3)
    revoked = store.revoke_by_session("session-1")
    assert revoked == 2
    with pytest.raises(RefreshTokenError):
        store.validate("token-a")
    with pytest.raises(RefreshTokenError):
        store.validate("token-b")
    # Third session unaffected
    assert store.validate("token-c").session == "session-2"
