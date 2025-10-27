# План миграции данных (Stage 03)

## Итоги извлечения
- Схема извлечена из `db/schema.php` 2025-10-27T00:11:45.758380+00:00.
- Найдено таблиц: 51.
- Всего столбцов: 469.
- Внешние ключи: 80.

## Артефакты
- [ER-диаграмма](er_diagram.mmd)
- SQLAlchemy-модели: `backend/app/models/generated.py`
- Pydantic-схемы: `backend/app/schemas/generated.py`
- ETL-пайплайн: `backend/app/etl/`

## ETL пайплайн
1. **Extract** — читает JSON-дамп MySQL (`extract.py`).
2. **Transform** — валидирует строки через Pydantic (`transform.py`).
3. **Load** — выполняет `session.merge` для загрузки в PostgreSQL (`load.py`).

## Следующие шаги
- Дополнить дамп данными из боевой MySQL.
- Запускать `python -m app.etl.run --input <dump.json> --database-url <postgres url>`.
- Сопоставить типы ENUM/SET с PostgreSQL-эквивалентами.
