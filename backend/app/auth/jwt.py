from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

import jwt

from .models import TokenPayload


class JWTEncodingError(RuntimeError):
    """Raised when JWT encoding fails."""


class JWTDecodingError(RuntimeError):
    """Raised when JWT decoding fails."""


class JWTManager:
    """Utility class for issuing and verifying JSON Web Tokens."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        issuer: str | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._issuer = issuer

    def _base_claims(self, expires_delta: timedelta) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        exp = now + expires_delta
        claims: dict[str, Any] = {
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        if self._issuer:
            claims["iss"] = self._issuer
        return claims

    def encode(self, payload: Mapping[str, Any], expires_delta: timedelta) -> str:
        """Encode ``payload`` into a JWT string."""

        claims = {**self._base_claims(expires_delta), **payload}
        try:
            return jwt.encode(claims, self._secret_key, algorithm=self._algorithm)
        except Exception as exc:  # pragma: no cover - unexpected
            raise JWTEncodingError(str(exc)) from exc

    def decode(self, token: str, audience: Sequence[str] | None = None) -> TokenPayload:
        """Decode ``token`` and validate registered claims."""

        options = {
            "require": ["exp", "iat", "nbf", "sub", "jti", "type"],
            # Always verify critical registered claims and the token signature, even if
            # PyJWT's global configuration was altered elsewhere in the process.
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
        }
        decode_kwargs: dict[str, Any] = {
            "algorithms": [self._algorithm],
            "options": options,
            "issuer": self._issuer,
            "key": self._secret_key,
        }
        if audience:
            decode_kwargs["audience"] = list(audience)
        else:
            options["verify_aud"] = False
        try:
            decoded = jwt.decode(token, **decode_kwargs)
        except Exception as exc:  # pragma: no cover - unexpected
            raise JWTDecodingError(str(exc)) from exc

        # Normalise scope claim to list
        scope_value = decoded.get("scope", [])
        if isinstance(scope_value, str):
            scopes = [scope_value]
        else:
            scopes = list(scope_value)

        return TokenPayload(
            sub=str(decoded.get("sub")),
            jti=str(decoded.get("jti")),
            exp=datetime.fromtimestamp(int(decoded["exp"]), tz=timezone.utc),
            iat=datetime.fromtimestamp(int(decoded["iat"]), tz=timezone.utc),
            nbf=datetime.fromtimestamp(int(decoded["nbf"]), tz=timezone.utc),
            scope=scopes,
            session=str(decoded.get("session")) if decoded.get("session") else None,
            mfa=bool(decoded.get("mfa", False)),
            type=str(decoded.get("type", "access")),
        )


__all__ = ["JWTManager", "JWTEncodingError", "JWTDecodingError"]
