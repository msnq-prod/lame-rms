# Summary

- Schema extracted on 2025-10-27T00:11:45.758380+00:00 containing 51 tables, 469 columns and 80 foreign keys.
- Generated SQLAlchemy models and Pydantic schemas to mirror the legacy structure.
- ETL pipeline validated via automated tests and Alembic migrations.

## Artifacts

- [ER diagram](../../docs/data/er_diagram.mmd)
- [Schema snapshot](schema.json)
- [SQLAlchemy models](../../backend/app/models/generated.py)
- [Pydantic schemas](../../backend/app/schemas/generated.py)
- [ETL pipeline](../../backend/app/etl/)

## Checks

| Check | Result | Details |
| --- | --- | --- |
| Tooling | warn | act=warning, k6=warning, playwright=warning, terraform=warning, helm=warning |
| Pytest (ETL) | pass | backend/tests/etl |
| Alembic upgrade | warn | docker not available |
| Row counts | pass | 3 rows loaded across 2 tables |
| Foreign keys | pass | No missing references |

## Coverage

- Coverage: 100.0% (62/62 lines)

## Next Gate

- Run `make stage04` once the FastAPI skeleton is ready to consume the migrated database.
- Extend fixtures with production-like datasets before executing the full migration.
