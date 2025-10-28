# Security Policies for Stage 06

The authentication and authorization stack migrated from the PHP monolith now provides a
consistent set of safeguards. This document summarises the controls introduced during
Stage 06 and maps them to the migration plan checklist.

## Access Tokens
- JSON Web Tokens (JWT) are signed with `HS256` using the configurable secret
  `APP_JWT_SECRET_KEY` (see `backend/app/core/config.py`).
- Access tokens expire after `APP_ACCESS_TOKEN_EXPIRY_MINUTES` (15 minutes by default).
- Refresh tokens are scoped to sessions and stored as SHA-256 digests in memory to
  avoid leaking raw values.
- Token payloads include the session identifier, MFA status, and scopes.

## Multi-factor Authentication (MFA)
- Time-based One-Time Password (TOTP) is implemented in `backend/app/auth/mfa.py` with
  a 30-second window and 6-digit codes.
- The backend enforces MFA whenever a user is enrolled or a role is configured with
  `mfa_required=true`.
- MFA secrets are generated using cryptographically secure random bytes and are only
  returned to the caller during enrollment.

## Role-based Access Control
- Roles are defined in `backend/app/auth/roles.py` and synchronised with the database
  using `automation/stage06/run.sh`.
- The canonical role matrix is rendered to `docs/security/roles.md` for auditability.
- Default roles include `system_admin`, `project_manager`, `auditor`, and `viewer` with
  explicit permission scopes.

## Audit Trail and Monitoring
- Every authentication event is recorded to `backend/var/security_audit.log` via
  `backend/app/auth/audit.py`.
- High severity events automatically emit alerts captured by the security monitor at
  `backend/var/security_alerts.jsonl`.
- The monitoring layer (`backend/app/monitoring/security.py`) exposes structured alerts
  and events for integration with external SIEM tools.

## Security Checklist (Stage 06)
- [x] JWT signing and expiration policies defined.
- [x] Refresh token store hashes token values and enforces revocation.
- [x] MFA flows implemented with TOTP and enforced for high privilege roles.
- [x] Security roles migrated to dedicated tables (`security_roles`, `security_role_permissions`).
- [x] Audit trail persists events and forwards high severity alerts.
- [x] Monitoring integration produces JSONL alerts for external consumers.

