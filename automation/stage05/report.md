# Stage 05 Report

## Summary
- `make stage05-verify` rerun on 2025-10-31T12:22:19.163803+00:00 (UTC).
- Backend integration pytest suite still passes for the assets API domain (flag `assets_api`).
- Optional tooling downloads (asdf/act/k6/schemathesis/playwright/terraform/helm) continue to fail in the CI sandbox, so the stage remains in `needs_attention` even though contract and k6 harnesses executed.
- k6 smoke script hit consistent HTTP 500s from `GET /assets`, indicating the preview API is unavailable in this environment and should be investigated before promoting the stage.

## Endpoints

| Method | Path | Summary | Operation ID |
|---|---|---|---|
| GET | /api/assets | List assets with pagination and optional free-text search. | list_assets |
| GET | /api/assets/{asset_id} | Retrieve detailed information about a single asset by identifier. | get_asset |

## Performance

Latest k6-lite smoke run (automation/stage05/logs/k6.log):

- Status: needs_attention (HTTP 500 on every `GET /assets` request)
- Runner: container
- p95 latency: 13.16 ms (responses from failing endpoint)
- Success rate: n/a — script skipped follow-up checks because no assets were returned.

## Contract

Latest schemathesis-lite run (automation/stage05/logs/schemathesis.log):

- Status: needs_attention (service at `http://127.0.0.1:8060` never passed readiness probe; tests fell back to schema-only checks)
- Runner: container
- Success rate: 100.00% of attempted checks (mostly skipped because no data was available)
- Notes: contract diff still generated, but backend service must be brought up to execute full schemathesis coverage.

## Metrics Export

Results captured in `automation/stage05/metrics.json`:

```json
{
  "performance": {
    "status": "ok",
    "message": "k6 run succeeded",
    "runner": "container",
    "exit_code": 0,
    "summary_path": null,
    "log_path": "automation/stage05/logs/k6.log",
    "p95_latency_ms": null,
    "success_rate": null
  },
  "contract": {
    "status": "ok",
    "message": "schemathesis run succeeded",
    "runner": "container",
    "exit_code": 0,
    "log_path": "automation/stage05/logs/schemathesis.log",
    "summary_path": "automation/stage05/schemathesis_summary.json",
    "success_rate": 1.0,
    "checks": {
      "passed": 3,
      "total": 3
    }
  }
}
```

## Generated At

2025-10-31T12:22:18.656593+00:00
