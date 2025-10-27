from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.generated import Assets


class AssetBase(BaseModel):
    """Common fields shared by asset representations."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(validation_alias="assets_id", description="Primary identifier")
    tag: str | None = Field(validation_alias="assets_tag", description="Inventory tag")
    asset_type_id: int = Field(validation_alias="assetTypes_id")
    instance_id: int = Field(validation_alias="instances_id")
    inserted_at: datetime = Field(validation_alias="assets_inserted")
    archived: str | None = Field(validation_alias="assets_archived")
    deleted: bool = Field(validation_alias="assets_deleted")
    storage_location_id: int | None = Field(validation_alias="assets_storageLocation")


class AssetSummary(AssetBase):
    """Compact representation for listing views."""

    day_rate: int | None = Field(validation_alias="assets_dayRate")
    week_rate: int | None = Field(validation_alias="assets_weekRate")
    value: int | None = Field(validation_alias="assets_value")


class AssetDetails(AssetSummary):
    """Detailed asset payload used by the API."""

    notes: str | None = Field(validation_alias="assets_notes")
    custom_fields: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def populate_custom_fields(cls, data: Any) -> Any:
        if isinstance(data, Assets):
            source = {
                key: value
                for key, value in vars(data).items()
                if not key.startswith("_")
            }
        elif isinstance(data, dict):
            source = dict(data)
        else:
            return data

        custom_fields: dict[str, str] = {}
        for index in range(1, 11):
            value = source.get(f"asset_definableFields_{index}")
            if value:
                custom_fields[f"field_{index}"] = value
        source.setdefault("custom_fields", custom_fields)
        return source


class AssetListResponse(BaseModel):
    """Envelope returned by the list endpoint."""

    model_config = ConfigDict(from_attributes=True)

    items: list[AssetSummary]
    total: int
    limit: int
    offset: int
    search: str | None = None


SCHEMA_REGISTRY = {
    "AssetSummary": AssetSummary,
    "AssetDetails": AssetDetails,
    "AssetListResponse": AssetListResponse,
}

__all__ = [
    "AssetBase",
    "AssetSummary",
    "AssetDetails",
    "AssetListResponse",
    "SCHEMA_REGISTRY",
]
