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
