from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.auth.models import AuthenticatedUser
from app.auth.service import AuthService, InvalidTokenError, MFARequiredError
from app.core.config import Settings


@pytest.fixture()
def auth_service() -> AuthService:
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        settings = Settings(
            jwt_secret_key="unit-test-secret",
            access_token_expiry_minutes=1,
            refresh_token_expiry_days=1,
            audit_log_path=str(tmp_path / "audit.log"),
            security_alert_log_path=str(tmp_path / "alerts.jsonl"),
            mfa_totp_digits=6,
            mfa_totp_interval_seconds=30,
        )
        service = AuthService(settings)
        yield service


def test_issue_and_refresh_tokens(auth_service: AuthService) -> None:
    user = AuthenticatedUser(id="user-1", email="user@example.com", roles=["viewer"], mfa_enrolled=False)
    pair = auth_service.issue_token_pair(user, scopes=["projects:read"])
    payload = auth_service.verify_access_token(pair.access_token)
    assert payload.sub == "user-1"
    assert "projects:read" in payload.scope
    refreshed = auth_service.refresh_session(pair.refresh_token)
    assert refreshed.access_token != pair.access_token
    with pytest.raises(InvalidTokenError):
        auth_service.refresh_session(pair.refresh_token)


def test_issue_requires_mfa_when_enrolled(auth_service: AuthService) -> None:
    user = AuthenticatedUser(id="user-2", email="user@example.com", roles=["system_admin"], mfa_enrolled=True)
    secret = auth_service.enroll_mfa_secret(user)
    user = user.model_copy(update={"mfa_secret": secret})
    with pytest.raises(MFARequiredError):
        auth_service.issue_token_pair(user)
    code = auth_service._mfa.generate_code(secret)
    pair = auth_service.issue_token_pair(user, mfa_code=code)
    assert pair.access_token


def test_refresh_requires_user_context_when_mfa(auth_service: AuthService) -> None:
    user = AuthenticatedUser(id="user-3", email="user@example.com", roles=["system_admin"], mfa_enrolled=True)
    secret = auth_service.enroll_mfa_secret(user)
    user = user.model_copy(update={"mfa_secret": secret})
    code = auth_service._mfa.generate_code(secret)
    pair = auth_service.issue_token_pair(user, mfa_code=code)
    with pytest.raises(MFARequiredError):
        auth_service.refresh_session(pair.refresh_token)
    new_code = auth_service._mfa.generate_code(secret)
    refreshed = auth_service.refresh_session(pair.refresh_token, user=user, mfa_code=new_code)
    assert refreshed.refresh_token != pair.refresh_token
