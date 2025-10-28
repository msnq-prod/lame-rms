from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .models import SecurityRole, SecurityRolePermission
from .roles import DEFAULT_ROLES, RoleDefinition


@contextmanager
def session_scope(engine: Engine):
    session = Session(engine, future=True)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_role(session: Session, definition: RoleDefinition) -> SecurityRole:
    role = session.get(SecurityRole, definition.slug)
    if role is None:
        role = SecurityRole(
            slug=definition.slug,
            name=definition.name,
            description=definition.description,
            is_default=definition.is_default,
            mfa_required=definition.mfa_required,
        )
        session.add(role)
        session.flush()
    else:
        role.name = definition.name
        role.description = definition.description
        role.is_default = definition.is_default
        role.mfa_required = definition.mfa_required

    existing_permissions = {perm.permission for perm in role.permissions}
    desired_permissions = set(definition.permissions)
    for perm in list(role.permissions):
        if perm.permission not in desired_permissions:
            session.delete(perm)
    for permission in desired_permissions - existing_permissions:
        role.permissions.append(SecurityRolePermission(permission=permission))
    return role


def sync_roles(database_url: str, definitions: Iterable[RoleDefinition] = DEFAULT_ROLES) -> list[dict[str, str]]:
    engine = create_engine(database_url, future=True)
    database_path = engine.url.database
    if database_path:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, str]] = []
    with session_scope(engine) as session:
        for definition in definitions:
            role = ensure_role(session, definition)
            summaries.append(
                {
                    "slug": role.slug,
                    "name": role.name,
                    "description": role.description,
                    "permissions": ", ".join(sorted({perm.permission for perm in role.permissions})),
                    "mfa_required": "yes" if role.mfa_required else "no",
                    "is_default": "yes" if role.is_default else "no",
                }
            )
    return summaries


def render_roles_markdown(output: Path, summaries: list[dict[str, str]]) -> None:
    lines = [
        "# Role Matrix",
        "",
        "| Slug | Name | Default | MFA Required | Permissions |",
        "|---|---|---|---|---|",
    ]
    for item in sorted(summaries, key=lambda row: row["slug"]):
        lines.append(
            f"| {item['slug']} | {item['name']} | {item['is_default']} | {item['mfa_required']} | {item['permissions']} |"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["sync_roles", "render_roles_markdown", "ensure_role"]
