from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.feature_flags import ensure_feature
from app.schemas.assets import AssetDetails, AssetListResponse
from app.services.assets import AssetsService


router = APIRouter(prefix="/assets", tags=["assets"])
require_assets_feature = ensure_feature("assets_api")


def get_assets_service(db: Session = Depends(get_db)) -> AssetsService:
    return AssetsService.from_session(db)


@router.get(
    "",
    response_model=AssetListResponse,
    summary="List assets with pagination and optional free-text search.",
    operation_id="list_assets",
    dependencies=[Depends(require_assets_feature)],
)
async def list_assets(
    *,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    search: str | None = Query(None, max_length=100, description="Case-insensitive match against tags"),
    service: AssetsService = Depends(get_assets_service),
) -> AssetListResponse:
    return service.list_assets(limit=limit, offset=offset, search=search)


@router.get(
    "/{asset_id}",
    response_model=AssetDetails,
    summary="Retrieve detailed information about a single asset by identifier.",
    operation_id="get_asset",
    dependencies=[Depends(require_assets_feature)],
)
async def get_asset(
    *,
    asset_id: int = Path(..., ge=1, description="Numeric asset identifier"),
    service: AssetsService = Depends(get_assets_service),
) -> AssetDetails:
    result = service.get_asset(asset_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return result


__all__ = ["router"]
