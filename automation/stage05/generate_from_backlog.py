"""Generate FastAPI domain artefacts for stage 05 from the migration backlog."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO_ROOT / "docs" / "backlog" / "migration_backlog.yaml"
SUMMARY_PATH = REPO_ROOT / "automation" / "stage05" / "summary.json"


def load_backlog() -> list[dict[str, Any]]:
    """Return backlog entries defined in the YAML source."""

    raw = yaml.safe_load(BACKLOG_PATH.read_text(encoding="utf-8"))
    items = raw.get("items", []) if isinstance(raw, dict) else []
    return [item for item in items if isinstance(item, dict)]


def write_file(path: Path, content: str) -> bool:
    """Write *content* to *path* if changed. Return True when updated."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = content if content.endswith("\n") else content + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == encoded:
        return False
    path.write_text(encoded, encoding="utf-8")
    return True


def generate_feature_flags(feature_flag: str) -> None:
    target = REPO_ROOT / "backend" / "app" / "feature_flags.py"
    content_template = dedent(
        '''
        from __future__ import annotations

        from functools import lru_cache
        from typing import Any

        from fastapi import HTTPException, status
        from pydantic import BaseModel, ConfigDict

        from app.core.config import get_settings


        class FeatureFlagState(BaseModel):
            """Declarative configuration for backend feature flags."""

            model_config = ConfigDict(extra="allow")

            __FEATURE_FLAG__: bool = True

            def is_enabled(self, flag: str) -> bool:
                return bool(getattr(self, flag, False))


        DEFAULT_FLAGS = FeatureFlagState()


        @lru_cache(maxsize=1)
        def get_feature_flags() -> FeatureFlagState:
            """Return cached feature flag configuration merged with overrides."""

            settings = get_settings()
            overrides: dict[str, Any] = {}
            raw_overrides = getattr(settings, "feature_flags", {})
            if isinstance(raw_overrides, dict):
                overrides = raw_overrides
            merged = {**DEFAULT_FLAGS.model_dump(), **overrides}
            return FeatureFlagState(**merged)


        def is_enabled(flag: str) -> bool:
            """Return True when *flag* is enabled."""

            return get_feature_flags().is_enabled(flag)


        def ensure_feature(flag: str):
            """FastAPI dependency ensuring that *flag* is enabled."""

            def dependency() -> None:
                if not is_enabled(flag):
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Feature '{flag}' is temporarily unavailable.",
                    )

            return dependency


        __all__ = [
            "FeatureFlagState",
            "DEFAULT_FLAGS",
            "get_feature_flags",
            "is_enabled",
            "ensure_feature",
        ]
        '''
    ).strip()
    content = content_template.replace("__FEATURE_FLAG__", feature_flag)
    write_file(target, content)


def generate_schemas() -> None:
    target = REPO_ROOT / "backend" / "app" / "schemas" / "assets.py"
    content = dedent(
        '''
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
        '''
    ).strip()
    write_file(target, content)


def generate_repository() -> None:
    target = REPO_ROOT / "backend" / "app" / "repositories" / "assets.py"
    content = dedent(
        '''
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
        '''
    ).strip()
    write_file(target, content)


def generate_service() -> None:
    target = REPO_ROOT / "backend" / "app" / "services" / "assets.py"
    content = dedent(
        '''
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
        '''
    ).strip()
    write_file(target, content)


def generate_router(feature_flag: str, endpoints: list[dict[str, Any]]) -> None:
    target = REPO_ROOT / "backend" / "app" / "api" / "routes" / "assets.py"
    list_endpoint = next((item for item in endpoints if item.get("operation_id") == "list_assets"), {})
    detail_endpoint = next((item for item in endpoints if item.get("operation_id") == "get_asset"), {})
    list_summary = list_endpoint.get("summary", "List assets")
    detail_summary = detail_endpoint.get("summary", "Retrieve asset")
    content = dedent(
        f'''
        from __future__ import annotations

        from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
        from sqlalchemy.orm import Session

        from app.db.session import get_db
        from app.feature_flags import ensure_feature
        from app.schemas.assets import AssetDetails, AssetListResponse
        from app.services.assets import AssetsService


        router = APIRouter(prefix="/assets", tags=["assets"])
        require_assets_feature = ensure_feature("{feature_flag}")


        def get_assets_service(db: Session = Depends(get_db)) -> AssetsService:
            return AssetsService.from_session(db)


        @router.get(
            "",
            response_model=AssetListResponse,
            summary="{list_summary}",
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
            "/{{asset_id}}",
            response_model=AssetDetails,
            summary="{detail_summary}",
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
        '''
    ).strip()
    write_file(target, content)


def update_router_registry() -> None:
    target = REPO_ROOT / "backend" / "app" / "api" / "routes" / "__init__.py"
    content = dedent(
        '''
        from fastapi import APIRouter

        from app.api.routes import assets, health

        api_router = APIRouter()
        api_router.include_router(health.router)
        api_router.include_router(assets.router)

        __all__ = ["api_router"]
        '''
    ).strip()
    write_file(target, content)


def update_service_registry() -> None:
    target = REPO_ROOT / "backend" / "app" / "services" / "__init__.py"
    content = dedent(
        '''
        """Service layer entry point for reusable business logic."""

        from app.services.assets import AssetsService
        from app.services.health import get_health_status

        __all__ = ["AssetsService", "get_health_status"]
        '''
    ).strip()
    write_file(target, content)


def update_repository_registry() -> None:
    target = REPO_ROOT / "backend" / "app" / "repositories" / "__init__.py"
    content = dedent(
        '''
        """Repository layer for database access abstractions."""

        from app.repositories.assets import AssetsRepository

        __all__ = ["AssetsRepository"]
        '''
    ).strip()
    write_file(target, content)


def update_schema_registry() -> None:
    target = REPO_ROOT / "backend" / "app" / "schemas" / "__init__.py"
    content = dedent(
        """
        from __future__ import annotations

        from typing import Dict, Type

        from pydantic import BaseModel

        from . import assets as _assets
        from . import generated as _generated

        SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
            **_generated.SCHEMA_REGISTRY,
            **_assets.SCHEMA_REGISTRY,
        }

        __all__ = list(dict.fromkeys(list(_generated.__all__) + list(_assets.__all__)))

        for name in _generated.__all__:
            globals()[name] = getattr(_generated, name)

        for name in _assets.__all__:
            globals()[name] = getattr(_assets, name)
        """
    ).strip()
    write_file(target, content)


def generate_docs(backlog_item: dict[str, Any]) -> None:
    documentation = backlog_item.get("fastapi", {}).get("documentation", "docs/api/assets.md")
    doc_path = REPO_ROOT / documentation
    endpoints = backlog_item.get("fastapi", {}).get("endpoints", [])
    lines = ["# Assets API", "", f"Generated from backlog item {backlog_item.get('id')}.", ""]
    lines.append("## Feature flag")
    lines.append("")
    lines.append(f"`{backlog_item.get('fastapi', {}).get('feature_flag', 'assets_api')}`")
    lines.append("")
    lines.append("## Endpoints")
    lines.append("")
    lines.append("| Method | Path | Summary | Operation ID |")
    lines.append("|---|---|---|---|")
    for endpoint in endpoints:
        lines.append(
            f"| {endpoint.get('method')} | /api{endpoint.get('path')} | {endpoint.get('summary')} | {endpoint.get('operation_id')} |"
        )
    lines.append("")
    lines.append("## Schemas")
    lines.append("")
    schemas = backlog_item.get("schemas", {}).get("models", [])
    responses = backlog_item.get("schemas", {}).get("responses", [])
    for name in schemas + responses:
        lines.append(f"- `{name}`")
    write_file(doc_path, "\n".join(lines))


def generate_tests() -> None:
    package_dir = REPO_ROOT / "backend" / "tests" / "integration"
    init_path = package_dir / "__init__.py"
    write_file(init_path, '"""Integration tests for FastAPI stage 05 domain."""')

    conftest_content = dedent(
        """
        from __future__ import annotations

        import os
        from datetime import datetime, timezone
        from pathlib import Path
        from typing import Generator

        import pytest
        from fastapi.testclient import TestClient

        TEST_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "integration_stage05.db"
        os.environ.setdefault("APP_DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
        TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        from app.main import app
        from app.db.base import Base
        from app.db.session import SessionLocal, engine
        from app.models.generated import (
            AssetCategories,
            AssetCategoriesGroups,
            AssetTypes,
            Assets,
            Instances,
            Manufacturers,
        )


        @pytest.fixture(scope="module", autouse=True)
        def prepare_database() -> Generator[None, None, None]:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            with SessionLocal() as session:
                instance = Instances(
                    instances_name="Integration Instance",
                    instances_deleted=False,
                    instances_plan="pro",
                    instances_address=None,
                    instances_phone=None,
                    instances_email=None,
                    instances_website=None,
                    instances_weekStartDates=None,
                    instances_logo=None,
                    instances_emailHeader=None,
                    instances_termsAndPayment=None,
                    instances_storageLimit=100000,
                    instances_config_linkedDefaultDiscount=0.0,
                    instances_config_currency="GBP",
                    instances_cableColours=None,
                    instances_publicConfig=None,
                )
                session.add(instance)
                session.flush()

                group = AssetCategoriesGroups(
                    assetCategoriesGroups_name="Lighting",
                    assetCategoriesGroups_fontAwesome=None,
                    assetCategoriesGroups_order=1,
                )
                session.add(group)
                session.flush()

                category = AssetCategories(
                    assetCategories_name="LED",
                    assetCategories_fontAwesome=None,
                    assetCategories_rank=1,
                    assetCategoriesGroups_id=group.assetCategoriesGroups_id,
                    instances_id=instance.instances_id,
                    assetCategories_deleted=False,
                )
                session.add(category)
                session.flush()

                manufacturer = Manufacturers(
                    manufacturers_name="Test Manufacturer",
                    instances_id=instance.instances_id,
                    manufacturers_internalAdamRMSNote=None,
                    manufacturers_website=None,
                    manufacturers_notes=None,
                )
                session.add(manufacturer)
                session.flush()

                asset_type = AssetTypes(
                    assetTypes_name="LED Panel",
                    assetCategories_id=category.assetCategories_id,
                    manufacturers_id=manufacturer.manufacturers_id,
                    instances_id=instance.instances_id,
                    assetTypes_description="Soft light panel",
                    assetTypes_productLink=None,
                    assetTypes_definableFields=None,
                    assetTypes_mass=None,
                    assetTypes_inserted=datetime.now(timezone.utc),
                    assetTypes_dayRate=2500,
                    assetTypes_weekRate=10000,
                    assetTypes_value=35000,
                )
                session.add(asset_type)
                session.flush()

                assets = [
                    Assets(
                        assets_tag="AST-0001",
                        assetTypes_id=asset_type.assetTypes_id,
                        assets_notes="Primary kit",
                        instances_id=instance.instances_id,
                        asset_definableFields_1="Serial-001",
                        assets_inserted=datetime.now(timezone.utc),
                        assets_dayRate=2000,
                        assets_linkedTo=None,
                        assets_weekRate=8000,
                        assets_value=20000,
                        assets_mass=None,
                        assets_deleted=False,
                        assets_endDate=None,
                        assets_archived=None,
                        assets_assetGroups=None,
                        assets_storageLocation=None,
                        assets_showPublic=True,
                    ),
                    Assets(
                        assets_tag="AST-0002",
                        assetTypes_id=asset_type.assetTypes_id,
                        assets_notes="Backup kit",
                        instances_id=instance.instances_id,
                        assets_inserted=datetime.now(timezone.utc),
                        assets_dayRate=1500,
                        assets_linkedTo=None,
                        assets_weekRate=6000,
                        assets_value=15000,
                        assets_mass=None,
                        assets_deleted=False,
                        assets_endDate=None,
                        assets_archived=None,
                        assets_assetGroups=None,
                        assets_storageLocation=None,
                        assets_showPublic=True,
                    ),
                ]
                session.add_all(assets)
                session.commit()
            yield
            Base.metadata.drop_all(bind=engine)


        @pytest.fixture(scope="module")
        def client() -> Generator[TestClient, None, None]:
            with TestClient(app) as test_client:
                yield test_client
        """
    ).strip()
    write_file(package_dir / "conftest.py", conftest_content)

    test_content = dedent(
        """
        from __future__ import annotations

        from fastapi.testclient import TestClient


        def test_list_assets_returns_items(client: TestClient) -> None:
            response = client.get("/api/assets")
            assert response.status_code == 200
            payload = response.json()
            assert payload["total"] >= 2
            assert len(payload["items"]) <= payload["limit"]
            assert any(item["tag"] == "AST-0001" for item in payload["items"])


        def test_search_assets_filters_results(client: TestClient) -> None:
            response = client.get("/api/assets", params={"search": "0002"})
            assert response.status_code == 200
            payload = response.json()
            assert payload["total"] == 1
            assert payload["items"][0]["tag"] == "AST-0002"


        def test_get_asset_detail(client: TestClient) -> None:
            listing = client.get("/api/assets").json()
            asset_id = listing["items"][0]["id"]
            detail = client.get(f"/api/assets/{asset_id}")
            assert detail.status_code == 200
            body = detail.json()
            assert body["id"] == asset_id
            assert "custom_fields" in body


        def test_get_asset_not_found_returns_404(client: TestClient) -> None:
            response = client.get("/api/assets/999999")
            assert response.status_code == 404
        """
    ).strip()
    write_file(package_dir / "test_assets.py", test_content)


def generate_loadtest() -> None:
    target = REPO_ROOT / "backend" / "loadtests" / "main.js"
    content = dedent(
        """
        import http from 'k6/http';
        import { check, sleep } from 'k6';

        export const options = {
          vus: 5,
          duration: '30s',
          thresholds: {
            http_req_duration: ['p(95)<800'],
            http_req_failed: ['rate<0.01'],
          },
        };

        const BASE_URL = `${__ENV.API_BASE_URL || 'http://127.0.0.1:8000/api'}`;

        export default function () {
          const listResponse = http.get(`${BASE_URL}/assets`);
          check(listResponse, {
            'list status is 200': (r) => r.status === 200,
          });

          try {
            const data = listResponse.json();
            if (data.items && data.items.length > 0) {
              const assetId = data.items[0].id;
              const detail = http.get(`${BASE_URL}/assets/${assetId}`);
              check(detail, {
                'detail status is 200': (r) => r.status === 200,
              });
            }
          } catch (err) {
            // Ignore JSON parsing issues during load to keep the scenario resilient.
          }

          sleep(1);
        }
        """
    ).strip()
    write_file(target, content)


def compose_summary(backlog_item: dict[str, Any]) -> None:
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backlog_item": {
            "id": backlog_item.get("id"),
            "title": backlog_item.get("title"),
            "domain": backlog_item.get("domain"),
        },
        "feature_flag": backlog_item.get("fastapi", {}).get("feature_flag"),
        "documentation": backlog_item.get("fastapi", {}).get("documentation"),
        "endpoints": backlog_item.get("fastapi", {}).get("endpoints", []),
        "schemas": backlog_item.get("schemas", {}),
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    backlog = load_backlog()
    stage_items = [item for item in backlog if item.get("stage") == 5]
    if not stage_items:
        raise SystemExit("No stage 05 backlog entries found")

    # Current iteration only migrates the assets domain
    assets_item = next((item for item in stage_items if item.get("domain") == "assets"), None)
    if assets_item is None:
        raise SystemExit("Stage 05 backlog missing assets domain specification")

    feature_flag = assets_item.get("fastapi", {}).get("feature_flag", "assets_api")
    endpoints = assets_item.get("fastapi", {}).get("endpoints", [])

    generate_feature_flags(feature_flag)
    generate_schemas()
    generate_repository()
    generate_service()
    generate_router(feature_flag, endpoints)
    update_router_registry()
    update_service_registry()
    update_repository_registry()
    update_schema_registry()
    generate_docs(assets_item)
    generate_tests()
    generate_loadtest()
    compose_summary(assets_item)


if __name__ == "__main__":
    main()
