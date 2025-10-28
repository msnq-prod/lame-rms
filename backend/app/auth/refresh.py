from __future__ import annotations

import hashlib
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .models import RefreshTokenMetadata


class RefreshTokenError(RuntimeError):
    """Raised when a refresh token fails validation."""


@dataclass(slots=True)
class StoredRefreshToken:
    """Internal representation of a refresh token entry."""

    digest: str
    metadata: RefreshTokenMetadata
    revoked: bool = False

    def is_expired(self, current_time: datetime | None = None) -> bool:
        now = current_time or datetime.now(timezone.utc)
        return now >= self.metadata.expires_at


class RefreshTokenStore:
    """In-memory refresh token registry with cryptographic digests."""

    def __init__(self) -> None:
        self._storage: dict[str, StoredRefreshToken] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _digest(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def register(self, token: str, metadata: RefreshTokenMetadata) -> StoredRefreshToken:
        digest = self._digest(token)
        with self._lock:
            self._storage[metadata.jti] = StoredRefreshToken(digest=digest, metadata=metadata)
        return self._storage[metadata.jti]

    def validate(self, token: str, *, expected_session: str | None = None) -> RefreshTokenMetadata:
        digest = self._digest(token)
        with self._lock:
            entry = next((item for item in self._storage.values() if item.digest == digest), None)
            if entry is None:
                raise RefreshTokenError("Refresh token is unknown")
            if entry.revoked:
                raise RefreshTokenError("Refresh token revoked")
            if entry.is_expired():
                raise RefreshTokenError("Refresh token expired")
            if expected_session and entry.metadata.session != expected_session:
                raise RefreshTokenError("Refresh token session mismatch")
            return entry.metadata

    def revoke(self, jti: str) -> None:
        with self._lock:
            if jti in self._storage:
                self._storage[jti].revoked = True

    def revoke_by_session(self, session: str) -> int:
        """Revoke all tokens belonging to a session and return count."""

        revoked = 0
        with self._lock:
            for entry in self._storage.values():
                if entry.metadata.session == session and not entry.revoked:
                    entry.revoked = True
                    revoked += 1
        return revoked

    def prune(self) -> int:
        """Remove expired tokens and return how many entries were deleted."""

        now = datetime.now(timezone.utc)
        to_delete = []
        with self._lock:
            for key, entry in self._storage.items():
                if entry.is_expired(now):
                    to_delete.append(key)
            for key in to_delete:
                del self._storage[key]
        return len(to_delete)

    def new_metadata(
        self,
        user_id: str,
        session: str | None,
        scopes: list[str],
        ttl_seconds: int,
        *,
        mfa: bool,
    ) -> RefreshTokenMetadata:
        jti = uuid.uuid4().hex
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(seconds=ttl_seconds)
        return RefreshTokenMetadata(
            jti=jti,
            session=session or jti,
            user_id=user_id,
            issued_at=issued_at,
            expires_at=expires_at,
            scopes=scopes,
            mfa=mfa,
        )


__all__ = [
    "RefreshTokenStore",
    "StoredRefreshToken",
    "RefreshTokenError",
]
