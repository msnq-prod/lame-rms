# Stage 05 Report

## Summary
- Generated FastAPI assets domain from backlog items M5-001, M5-002, M5-003 и M5-004.
- Feature flag: `assets_api`.
- Documentation: `docs/api/assets.md`.

## Backlog Alignment

| Backlog ID | Scope | Legacy routes |
|---|---|---|
| M5-002 | Barcode workflows parity | `/api/assets/searchAssetsBarcode`, `/api/assets/barcodes/*` |
| M5-003 | Assets CRUD and asset-type parity | `/api/assets/list`, `/api/assets/newAssetType`, `/api/assets/editAsset`, `/api/assets/delete`, `/api/assets/search*`, `/api/assets/substitutions`, `/api/assets/transfer` |
| M5-004 | Assets export parity | `/api/assets/export` |

## Endpoints

| Method | Path | Summary | Operation ID |
|---|---|---|---|
| GET | /api/assets | List assets with pagination and optional free-text search. | list_assets |
| GET | /api/assets/{asset_id} | Retrieve detailed information about a single asset by identifier. | get_asset |

## Performance

Aggregated results from k6:

- Status: fail
- Runner: missing
- p95 latency: n/a
- Success rate: n/a

## Contract

Aggregated results from schemathesis:

- Status: fail
- Runner: missing
- Success rate: 0.00%
- Checks passed: n/a
- Notes: schemathesis runner not available

## Metrics Export

Results captured in `automation/stage05/metrics.json`:

```json
{
  "performance": {
    "status": "fail",
    "message": "k6 runner not available",
    "runner": "missing",
    "exit_code": 1,
    "summary_path": null,
    "log_path": null,
    "p95_latency_ms": null,
    "success_rate": null
  },
  "contract": {
    "status": "fail",
    "message": "schemathesis runner not available",
    "runner": "missing",
    "exit_code": 1,
    "log_path": null,
    "summary_path": "automation/stage05/schemathesis_summary.json",
    "success_rate": 0.0,
    "checks": null
  }
}
```

## Generated At

2025-10-30T14:41:47.209998+00:00
