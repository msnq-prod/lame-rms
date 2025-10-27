from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.generated import Assets


class AssetsRepository:
    """Data-access helpers for the assets domain."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_assets(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> Sequence[Assets]:
        stmt = select(Assets).order_by(Assets.assets_id).limit(limit).offset(offset)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(func.coalesce(Assets.assets_tag, "")).like(pattern)
            )
        return list(self._session.execute(stmt).scalars())

    def count_assets(self, *, search: str | None = None) -> int:
        stmt = select(func.count()).select_from(Assets)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(func.coalesce(Assets.assets_tag, "")).like(pattern)
            )
        return int(self._session.execute(stmt).scalar_one())

    def get_asset(self, asset_id: int) -> Assets | None:
        return self._session.get(Assets, asset_id)


__all__ = ["AssetsRepository"]
