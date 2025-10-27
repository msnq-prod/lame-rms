# Assets API

Generated from backlog item M5-001.

## Feature flag

`assets_api`

## Endpoints

| Method | Path | Summary | Operation ID |
|---|---|---|---|
| GET | /api/assets | List assets with pagination and optional free-text search. | list_assets |
| GET | /api/assets/{asset_id} | Retrieve detailed information about a single asset by identifier. | get_asset |

## Schemas

- `AssetSummary`
- `AssetDetails`
- `AssetListResponse`
