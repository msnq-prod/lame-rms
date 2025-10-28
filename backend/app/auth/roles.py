from __future__ import annotations

from typing import Dict

from .models import RoleDefinition


DEFAULT_ROLES: tuple[RoleDefinition, ...] = (
    RoleDefinition(
        slug="system_admin",
        name="System Administrator",
        description="Full administrative access to AdamRMS backend, including role and security policy management.",
        permissions=(
            "auth:users:read",
            "auth:users:write",
            "auth:roles:read",
            "auth:roles:write",
            "auth:mfa:reset",
            "audit:events:export",
        ),
        mfa_required=True,
        is_default=False,
    ),
    RoleDefinition(
        slug="project_manager",
        name="Project Manager",
        description="Manage projects and crew assignments with elevated read/write permissions but limited security scope.",
        permissions=(
            "projects:read",
            "projects:write",
            "crew:assign",
            "assets:reserve",
            "auth:users:read",
        ),
        mfa_required=True,
        is_default=True,
    ),
    RoleDefinition(
        slug="auditor",
        name="Security Auditor",
        description="Read-only visibility into audit and security events for compliance reviews.",
        permissions=(
            "audit:events:read",
            "auth:roles:read",
            "auth:users:read",
        ),
        mfa_required=False,
        is_default=False,
    ),
    RoleDefinition(
        slug="viewer",
        name="Operations Viewer",
        description="Baseline read-only access to operational data without security-sensitive permissions.",
        permissions=(
            "projects:read",
            "assets:read",
            "inventory:read",
        ),
        mfa_required=False,
        is_default=True,
    ),
)


def role_lookup() -> Dict[str, RoleDefinition]:
    """Return a mapping of role slug to definition."""

    return {role.slug: role for role in DEFAULT_ROLES}


def permissions_for(role_slug: str) -> tuple[str, ...]:
    """Return permissions associated with a role slug."""

    return tuple(role_lookup().get(role_slug, RoleDefinition(role_slug, role_slug, "", ())).permissions)


def all_permissions() -> set[str]:
    """Return the full set of permissions across default roles."""

    return {permission for role in DEFAULT_ROLES for permission in role.permissions}


__all__ = ["DEFAULT_ROLES", "role_lookup", "permissions_for", "all_permissions"]
