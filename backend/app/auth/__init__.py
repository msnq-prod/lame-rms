"""Authentication, authorization, and audit utilities."""

from .audit import AuditTrail
from .jwt import JWTManager, JWTDecodingError, JWTEncodingError
from .mfa import MFADevice, MFAVerifier
from .models import (
    AuditEvent,
    AuthenticatedUser,
    RefreshTokenMetadata,
    RoleDefinition,
    SecurityRole,
    SecurityRoleAssignment,
    SecurityRolePermission,
    TokenPair,
    TokenPayload,
)
from .passwords import PasswordHasher
from .refresh import RefreshTokenError, RefreshTokenStore
from .roles import DEFAULT_ROLES, all_permissions, permissions_for, role_lookup
from .service import (
    AuthService,
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    MFARequiredError,
)

__all__ = [
    "AuditTrail",
    "AuditEvent",
    "AuthenticatedUser",
    "AuthService",
    "AuthenticationError",
    "AuthorizationError",
    "InvalidTokenError",
    "MFARequiredError",
    "JWTManager",
    "JWTEncodingError",
    "JWTDecodingError",
    "MFAVerifier",
    "MFADevice",
    "PasswordHasher",
    "RefreshTokenStore",
    "RefreshTokenError",
    "RefreshTokenMetadata",
    "TokenPair",
    "TokenPayload",
    "SecurityRole",
    "SecurityRoleAssignment",
    "SecurityRolePermission",
    "RoleDefinition",
    "DEFAULT_ROLES",
    "role_lookup",
    "permissions_for",
    "all_permissions",
]
