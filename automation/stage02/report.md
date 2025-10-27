# Summary

- Inventory generated on 2025-10-27T05:43:46.287385+00:00 covering 505 files across legacy, src.
- Detected 207 API endpoints and 0 cron candidates.
- Migration backlog initialised with actionable items and risk ratings.

## Risk Register
| ID | Title | Severity | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| M2-001 | Stabilise API documentation | high | Incorrect endpoint catalogue may block client migrations. | Review generated OpenAPI with engineering leads and add automated smoke tests. |
| M2-002 | Template parity audit | medium | Missing templates degrade UX during migration. | Prioritise high-traffic templates and create acceptance criteria. |
| M2-003 | Cron job remediation plan | critical | Unmigrated cron jobs can halt invoicing and notifications. | Document ownership, add monitoring, and schedule reimplementation on FastAPI workers. |
| M2-004 | Metrics coverage | low | Lack of metrics limits visibility into migration progress. | Integrate reports into CI dashboards and revisit quarterly. |

# Artifacts

- [File inventory (JSON)](../../docs/inventory/files.json)
- [File inventory (CSV)](../../docs/inventory/files.csv)
- [Metrics report](../../docs/inventory/metrics.md)
- [Cron assessment](../../docs/inventory/cron.md)
- [Structure diagram](../../docs/inventory/structure.mmd)
- [API surface diagram](../../docs/inventory/api_surface.mmd)
- [OpenAPI export](../../docs/inventory/api/openapi.json)
- [API endpoints CSV](../../docs/inventory/api/endpoints.csv)
- [API summary](../../docs/inventory/api/summary.md)
- [Migration backlog](../../docs/backlog/migration_backlog.yaml)

# Checks

| Check | Result | Details |
| --- | --- | --- |
| File coverage | ✅ | 505 files inventoried |
| API extraction | ✅ | 207 endpoints exported |
| Cron detection | ✅ | 0 candidates reviewed |

# Next Gate

- Run `make stage02-verify` to validate the generated artefacts.
- Review `docs/backlog/migration_backlog.yaml` with the migration steering group.
- Prioritise remediation items before starting development migration work.
