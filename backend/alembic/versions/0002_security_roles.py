"""Create security role tables."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_security_roles"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "security_roles",
        sa.Column("slug", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("mfa_required", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "security_role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "role_slug",
            sa.String(length=64),
            sa.ForeignKey("security_roles.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("permission", sa.String(length=128), nullable=False),
    )
    op.create_index(
        "ix_security_role_permissions_role_slug_permission",
        "security_role_permissions",
        ["role_slug", "permission"],
        unique=True,
    )
    op.create_table(
        "security_role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "role_slug",
            sa.String(length=64),
            sa.ForeignKey("security_roles.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.users_userid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.users_userid"), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_security_role_assignments_role_user",
        "security_role_assignments",
        ["role_slug", "user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_security_role_assignments_role_user", table_name="security_role_assignments")
    op.drop_table("security_role_assignments")
    op.drop_index("ix_security_role_permissions_role_slug_permission", table_name="security_role_permissions")
    op.drop_table("security_role_permissions")
    op.drop_table("security_roles")
