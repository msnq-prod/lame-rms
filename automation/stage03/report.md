# Summary

- `make stage03-verify` rerun on 2025-10-31T12:21:31.917360+00:00 (UTC).
- ETL pytest suite still passes against the generated fixtures and models.
- Alembic migration step remains blocked because the temporary PostgreSQL helper did not expose a connection URI; manual DB setup is required before this check can succeed.

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
| Tooling | warn | asdf=warning, npm=ok, npx=ok, act=warning, k6=warning, schemathesis=warning, bandit=ok, playwright=warning, terraform=warning, helm=warning |
| Pytest (ETL) | pass | backend/tests/etl (see pytest.log) |
| Alembic upgrade | fail | Temporary PostgreSQL did not provide URI (see alembic.log) |
| Row counts | pass | actionsCategories=1/1, actions=2/2 |
| Foreign keys | pass | No foreign key violations |
| run.py coverage | pass | run.py covered_lines=19/19 |

## Coverage

- Coverage: 94.19% (81/86 lines)

## Commands

1. `make stage03` — генерация схемы, моделей, ETL и документации.
2. `make stage03-verify` — pytest, alembic, проверки данных и coverage.
3. `make stage03-report` — вывод актуального отчёта.

## Next Gate

- Run `make stage04` once the FastAPI skeleton is ready to consume the migrated database.
- Extend fixtures with production-like datasets before executing the full migration.
