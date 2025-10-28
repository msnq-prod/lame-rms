from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SecurityRole(Base):
    """Role definition stored in the database."""

    __tablename__ = "security_roles"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    permissions: Mapped[list["SecurityRolePermission"]] = relationship(
        "SecurityRolePermission",
        cascade="all, delete-orphan",
        back_populates="role",
        lazy="joined",
    )
    assignments: Mapped[list["SecurityRoleAssignment"]] = relationship(
        "SecurityRoleAssignment",
        cascade="all, delete-orphan",
        back_populates="role",
        lazy="selectin",
    )


class SecurityRolePermission(Base):
    """Permission tied to a role."""

    __tablename__ = "security_role_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_slug: Mapped[str] = mapped_column(
        String(64), ForeignKey("security_roles.slug", ondelete="CASCADE"), nullable=False
    )
    permission: Mapped[str] = mapped_column(String(128), nullable=False)

    role: Mapped[SecurityRole] = relationship("SecurityRole", back_populates="permissions")


class SecurityRoleAssignment(Base):
    """Assignment connecting a user with a role."""

    __tablename__ = "security_role_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_slug: Mapped[str] = mapped_column(
        String(64), ForeignKey("security_roles.slug", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.users_userid", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    assigned_by: Mapped[int | None] = mapped_column(ForeignKey("users.users_userid"), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    role: Mapped[SecurityRole] = relationship("SecurityRole", back_populates="assignments")


class TokenPayload(BaseModel):
    """Decoded JWT payload shared across token types."""

    sub: str
    jti: str
    exp: datetime
    iat: datetime
    nbf: datetime
    scope: list[str] = Field(default_factory=list)
    session: str | None = None
    mfa: bool = False
    type: str = "access"


class TokenPair(BaseModel):
    """Pair of access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenMetadata(BaseModel):
    """Metadata persisted alongside refresh tokens."""

    jti: str
    session: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    scopes: list[str] = Field(default_factory=list)
    mfa: bool = False


class AuditEvent(BaseModel):
    """Structured audit event stored on disk and optionally forwarded."""

    event_type: str
    user_id: str | None = None
    actor: str | None = None
    severity: str = Field(default="info", pattern=r"^(info|low|medium|high|critical)$")
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthenticatedUser(BaseModel):
    """Lightweight authenticated user representation."""

    id: str
    email: str
    roles: list[str] = Field(default_factory=list)
    mfa_enrolled: bool = False
    mfa_secret: str | None = None

    @property
    def primary_role(self) -> str | None:
        return self.roles[0] if self.roles else None


@dataclass(slots=True)
class RoleDefinition:
    """Definition used to bootstrap security roles."""

    slug: str
    name: str
    description: str
    permissions: Sequence[str]
    mfa_required: bool = False
    is_default: bool = False

    def to_assignment_payload(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "mfa_required": self.mfa_required,
            "is_default": self.is_default,
        }


__all__ = [
    "SecurityRole",
    "SecurityRolePermission",
    "SecurityRoleAssignment",
    "TokenPayload",
    "TokenPair",
    "RefreshTokenMetadata",
    "AuditEvent",
    "AuthenticatedUser",
    "RoleDefinition",
]
