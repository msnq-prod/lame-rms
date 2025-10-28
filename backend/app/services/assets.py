from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.assets import AssetsRepository
from app.schemas.assets import AssetDetails, AssetListResponse, AssetSummary


@dataclass
class AssetsService:
    """Business logic orchestrator for assets endpoints."""

    repository: AssetsRepository

    @classmethod
    def from_session(cls, session: Session) -> "AssetsService":
        return cls(repository=AssetsRepository(session))

    def list_assets(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> AssetListResponse:
        records = self.repository.list_assets(limit=limit, offset=offset, search=search)
        total = self.repository.count_assets(search=search)
        payload = [AssetSummary.model_validate(record) for record in records]
        return AssetListResponse(items=payload, total=total, limit=limit, offset=offset, search=search)

    def get_asset(self, asset_id: int) -> Optional[AssetDetails]:
        record = self.repository.get_asset(asset_id)
        if record is None:
            return None
        return AssetDetails.model_validate(record)


__all__ = ["AssetsService"]
