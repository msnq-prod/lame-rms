from __future__ import annotations

import uuid
from typing import Iterable, Sequence

from app.core.config import Settings
from app.monitoring.security import SecurityMonitor

from .audit import AuditTrail
from .jwt import JWTManager, JWTDecodingError
from .mfa import MFAVerifier
from .models import AuditEvent, AuthenticatedUser, TokenPair, TokenPayload
from .passwords import PasswordHasher
from .refresh import RefreshTokenError, RefreshTokenStore


class AuthenticationError(RuntimeError):
    """Raised when authentication fails."""


class AuthorizationError(RuntimeError):
    """Raised when an action is not permitted."""


class MFARequiredError(RuntimeError):
    """Raised when MFA validation is required."""


class InvalidTokenError(RuntimeError):
    """Raised when a token cannot be decoded or validated."""


class AuthService:
    """Aggregate authentication helpers (passwords, tokens, MFA, audit)."""

    def __init__(
        self,
        settings: Settings,
        *,
        jwt_manager: JWTManager | None = None,
        refresh_store: RefreshTokenStore | None = None,
        password_hasher: PasswordHasher | None = None,
        mfa_verifier: MFAVerifier | None = None,
        audit_trail: AuditTrail | None = None,
        security_monitor: SecurityMonitor | None = None,
    ) -> None:
        self._settings = settings
        self._jwt = jwt_manager or JWTManager(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            issuer=settings.jwt_issuer,
        )
        self._refresh_store = refresh_store or RefreshTokenStore()
        self._password_hasher = password_hasher or PasswordHasher()
        self._monitor = security_monitor or SecurityMonitor(settings.security_alert_file)
        self._mfa = mfa_verifier or MFAVerifier(
            interval=settings.mfa_totp_interval_seconds,
            digits=settings.mfa_totp_digits,
        )
        self._audit = audit_trail or AuditTrail(settings.audit_log_file, self._monitor)

    @property
    def refresh_store(self) -> RefreshTokenStore:
        return self._refresh_store

    def hash_password(self, password: str) -> str:
        return self._password_hasher.hash(password)

    def verify_password(self, password: str, hashed: str) -> bool:
        return self._password_hasher.verify(password, hashed)

    def _ensure_mfa(self, user: AuthenticatedUser, mfa_code: str | None, *, required: bool) -> bool:
        if not (required or user.mfa_enrolled):
            return False
        if not user.mfa_secret:
            raise MFARequiredError("User does not have an MFA secret configured")
        if not mfa_code or not self._mfa.verify(user.mfa_secret, mfa_code):
            self._record_security_event(
                "auth.mfa_failure",
                user=user,
                severity="high",
                metadata={"reason": "invalid_code"},
            )
            raise MFARequiredError("Invalid MFA code provided")
        return True

    def _record_security_event(
        self,
        event_type: str,
        *,
        user: AuthenticatedUser | None,
        severity: str = "info",
        metadata: dict | None = None,
    ) -> None:
        self._audit.record(
            AuditEvent(
                event_type=event_type,
                user_id=user.id if user else None,
                actor=user.email if user else None,
                severity=severity,
                metadata=metadata or {},
            )
        )

    def issue_token_pair(
        self,
        user: AuthenticatedUser,
        *,
        scopes: Iterable[str] | None = None,
        session_id: str | None = None,
        mfa_code: str | None = None,
        require_mfa: bool = False,
    ) -> TokenPair:
        """Return an access/refresh token pair for ``user``."""

        scopes_list = sorted(set(scopes or []))
        session = session_id or uuid.uuid4().hex
        mfa_verified = self._ensure_mfa(user, mfa_code, required=require_mfa)
        session_claim = session
        access_jti = uuid.uuid4().hex
        refresh_metadata = self._refresh_store.new_metadata(
            user_id=user.id,
            session=session,
            scopes=scopes_list,
            ttl_seconds=int(self._settings.refresh_token_ttl.total_seconds()),
            mfa=mfa_verified,
        )
        refresh_token = self._jwt.encode(
            {
                "sub": user.id,
                "jti": refresh_metadata.jti,
                "session": session_claim,
                "scope": scopes_list,
                "mfa": mfa_verified,
                "type": "refresh",
            },
            expires_delta=self._settings.refresh_token_ttl,
        )
        self._refresh_store.register(refresh_token, refresh_metadata)
        access_token = self._jwt.encode(
            {
                "sub": user.id,
                "jti": access_jti,
                "session": session_claim,
                "scope": scopes_list,
                "mfa": mfa_verified,
                "type": "access",
            },
            expires_delta=self._settings.access_token_ttl,
        )
        self._record_security_event(
            "auth.session_issued",
            user=user,
            severity="info",
            metadata={"session": session_claim, "scopes": scopes_list},
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(self._settings.access_token_ttl.total_seconds()),
        )

    def refresh_session(
        self,
        refresh_token: str,
        *,
        user: AuthenticatedUser | None = None,
        mfa_code: str | None = None,
    ) -> TokenPair:
        """Issue a new token pair using ``refresh_token``."""

        try:
            payload = self._jwt.decode(refresh_token)
        except JWTDecodingError as exc:  # pragma: no cover - defensive path
            raise InvalidTokenError(str(exc)) from exc
        if payload.type != "refresh":
            raise InvalidTokenError("Token is not a refresh token")
        try:
            metadata = self._refresh_store.validate(refresh_token)
        except RefreshTokenError as exc:
            raise InvalidTokenError(str(exc)) from exc
        if metadata.mfa:
            if user is None:
                raise MFARequiredError("User context with MFA secret required to refresh secured session")
            self._ensure_mfa(user, mfa_code, required=True)
        scopes = payload.scope
        self._refresh_store.revoke(metadata.jti)
        resulting_user = user or AuthenticatedUser(id=payload.sub, email="", roles=[], mfa_enrolled=metadata.mfa)
        pair = self.issue_token_pair(
            resulting_user,
            scopes=scopes,
            session_id=metadata.session,
            mfa_code=mfa_code if metadata.mfa else None,
            require_mfa=metadata.mfa,
        )
        self._record_security_event(
            "auth.session_refreshed",
            user=resulting_user,
            severity="info",
            metadata={"session": metadata.session, "previous": metadata.jti},
        )
        return pair

    def verify_access_token(self, token: str) -> TokenPayload:
        payload = self._jwt.decode(token)
        if payload.type != "access":
            raise InvalidTokenError("Token is not an access token")
        return payload

    def revoke_session(self, session_id: str) -> int:
        revoked = self._refresh_store.revoke_by_session(session_id)
        if revoked:
            self._monitor.record_event(
                event_type="auth.session_revoked",
                severity="medium",
                payload={"session": session_id, "revoked": revoked},
            )
        return revoked

    def enroll_mfa_secret(self, user: AuthenticatedUser) -> str:
        secret = self._mfa.generate_secret()
        self._record_security_event(
            "auth.mfa_enrolled",
            user=user,
            severity="low",
            metadata={"secret": "generated"},
        )
        return secret


__all__ = [
    "AuthService",
    "AuthenticationError",
    "AuthorizationError",
    "MFARequiredError",
    "InvalidTokenError",
]
