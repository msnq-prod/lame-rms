# Summary

- Schema extracted on 2025-10-27T06:21:38.656851+00:00 containing 51 tables, 469 columns and 80 foreign keys.
- Generated SQLAlchemy models and Pydantic schemas to mirror the legacy structure.
- ETL pipeline validated via automated tests and Alembic migrations.

## Artifacts

- [ER diagram](../../docs/data/er_diagram.mmd)
- [Schema snapshot](schema.json)
- [SQLAlchemy models](../../backend/app/models/generated.py)
- [Pydantic schemas](../../backend/app/schemas/generated.py)
- [ETL pipeline](../../backend/app/etl/)

## Key Files

- backend/app/models/generated.py
- backend/app/schemas/generated.py
- backend/app/etl/ (extract.py, transform.py, load.py, run.py)
- backend/tests/etl/test_pipeline.py
- docs/data/migration_plan.md
- automation/stage03/run.sh
- automation/stage03/self_check.sh

## Checks

| Check | Result | Details |
| --- | --- | --- |
| Tooling | warn | act=warning, k6=warning, playwright=warning, terraform=warning, helm=warning |
| Pytest (ETL) | pass | backend/tests/etl (see pytest.log) |
| Alembic upgrade | warn | docker not available |
| Row counts | pass | actionsCategories=1/1, actions=2/2 |
| Foreign keys | pass | No foreign key violations |

## Coverage

- Coverage: 72.09% (62/86 lines)

## Commands

1. `make stage03` — генерация схемы, моделей, ETL и документации.
2. `make stage03-verify` — pytest, alembic, проверки данных и coverage.
3. `make stage03-report` — вывод актуального отчёта.

## Next Gate

- Run `make stage04` once the FastAPI skeleton is ready to consume the migrated database.
- Extend fixtures with production-like datasets before executing the full migration.
