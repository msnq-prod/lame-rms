#!/usr/bin/env python3
"""Generate database assets for stage 03.

This script extracts the legacy MySQL schema exported by Phinx,
produces a Mermaid ER diagram, generates SQLAlchemy models and
Pydantic schemas, and ensures the ETL scaffolding, tests, and
documentation artefacts are in place.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ROOT / "db" / "schema.php"
DOCS_DATA_DIR = ROOT / "docs" / "data"
MODELS_DIR = ROOT / "backend" / "app" / "models"
SCHEMAS_DIR = ROOT / "backend" / "app" / "schemas"
ETL_DIR = ROOT / "backend" / "app" / "etl"
TESTS_DIR = ROOT / "backend" / "tests" / "etl"
STAGE_DIR = ROOT / "automation" / "stage03"


@dataclass
class ColumnMeta:
    name: str
    data: dict[str, Any]

    @property
    def position(self) -> int:
        try:
            return int(self.data.get("ORDINAL_POSITION", 0))
        except (TypeError, ValueError):
            return 0


def run_php_to_json(schema_path: Path) -> dict[str, Any]:
    command = [
        "php",
        "-r",
        f"echo json_encode(include '{schema_path}');",
    ]
    try:
        raw = subprocess.check_output(command)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to execute php for schema: {exc}") from exc
    return json.loads(raw)


def to_class_name(table_name: str) -> str:
    buffer: list[str] = []
    segment = ""
    for char in table_name:
        if char in {"_", "-"}:
            if segment:
                buffer.append(segment)
                segment = ""
            continue
        if char.isupper() and segment:
            buffer.append(segment)
            segment = char
        else:
            segment += char
    if segment:
        buffer.append(segment)
    return "".join(part.capitalize() for part in buffer)


def map_sqlalchemy_type(column: ColumnMeta) -> tuple[str, set[str]]:
    data_type = column.data.get("DATA_TYPE", "").lower()
    column_type = (column.data.get("COLUMN_TYPE") or "").lower()
    length = column.data.get("CHARACTER_MAXIMUM_LENGTH")
    numeric_precision = column.data.get("NUMERIC_PRECISION")
    numeric_scale = column.data.get("NUMERIC_SCALE")

    imports: set[str] = set()
    type_expr = "Text"

    if data_type == "int":
        type_expr = "Integer"
        imports.add("Integer")
    elif data_type == "bigint":
        type_expr = "BigInteger"
        imports.add("BigInteger")
    elif data_type == "tinyint":
        if column_type.startswith("tinyint(1"):
            type_expr = "Boolean"
            imports.add("Boolean")
        else:
            type_expr = "SmallInteger"
            imports.add("SmallInteger")
    elif data_type == "varchar":
        try:
            if length:
                type_expr = f"String({int(length)})"
            else:
                type_expr = "Text"
        except (TypeError, ValueError):
            type_expr = "Text"
        imports.add("String")
        imports.add("Text")
    elif data_type in {"text", "longtext"}:
        type_expr = "Text"
        imports.add("Text")
    elif data_type == "timestamp":
        type_expr = "DateTime"
        imports.add("DateTime")
    elif data_type == "decimal":
        precision = int(numeric_precision) if numeric_precision else 10
        scale = int(numeric_scale) if numeric_scale else 0
        type_expr = f"Numeric({precision}, {scale})"
        imports.add("Numeric")
    elif data_type in {"float", "double"}:
        type_expr = "Float"
        imports.add("Float")
    elif data_type == "json":
        type_expr = "JSON"
        imports.add("JSON")
    else:
        type_expr = "Text"
        imports.add("Text")

    return type_expr, imports


def map_python_type(column: ColumnMeta) -> tuple[str, set[str]]:
    data_type = column.data.get("DATA_TYPE", "").lower()
    column_type = (column.data.get("COLUMN_TYPE") or "").lower()
    imports: set[str] = set()
    annotation = "str"

    if data_type in {"int", "bigint"}:
        annotation = "int"
    elif data_type == "tinyint":
        annotation = "bool" if column_type.startswith("tinyint(1") else "int"
    elif data_type in {"varchar", "text", "longtext"}:
        annotation = "str"
    elif data_type == "decimal":
        annotation = "Decimal"
        imports.add("Decimal")
    elif data_type in {"float", "double"}:
        annotation = "float"
    elif data_type == "timestamp":
        annotation = "datetime"
        imports.add("datetime")
    elif data_type == "json":
        annotation = "dict[str, Any] | list[Any]"
        imports.update({"Any", "List"})
    else:
        annotation = "str"

    return annotation, imports


def collect_foreign_keys(table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    foreign_keys = table.get("foreign_keys") or {}
    result: dict[str, dict[str, Any]] = {}
    for details in foreign_keys.values():
        column_name = details.get("COLUMN_NAME")
        if not column_name:
            continue
        result[column_name] = details
    return result


def generate_models(tables: dict[str, Any], destination: Path, summary: dict[str, Any]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    generated_file = destination / "generated.py"

    lines: list[str] = [
        "from __future__ import annotations",
        "",
        "from typing import Dict, Type",
        "",
        "from sqlalchemy import Column, ForeignKey",
        "from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, Numeric, String, Text",
        "from sqlalchemy import BigInteger, SmallInteger",
        "",
        "from app.db.base import Base",
        "",
        f"# Auto-generated on {summary['timestamp']} from db/schema.php",
        "",
    ]

    registry_entries: list[str] = []
    all_names: list[str] = []

    for table_name in sorted(tables):
        table = tables[table_name]
        columns = [ColumnMeta(name=col_name, data=col_data) for col_name, col_data in table["columns"].items()]
        columns.sort(key=lambda col: col.position)
        fk_map = collect_foreign_keys(table)
        class_name = to_class_name(table_name)
        all_names.append(class_name)
        lines.append(f"class {class_name}(Base):")
        lines.append(f"    __tablename__ = \"{table_name}\"")
        lines.append("")
        for column in columns:
            type_expr, _ = map_sqlalchemy_type(column)
            args: list[str] = [type_expr]
            fk_details = fk_map.get(column.name)
            if fk_details:
                fk_target = f"{fk_details['REFERENCED_TABLE_NAME']}.{fk_details['REFERENCED_COLUMN_NAME']}"
                fk_args = [f"\"{fk_target}\""]
                delete_rule = fk_details.get("DELETE_RULE")
                update_rule = fk_details.get("UPDATE_RULE")
                if delete_rule and delete_rule not in {"NO ACTION", "RESTRICT"}:
                    fk_args.append(f"ondelete=\"{delete_rule}\"")
                if update_rule and update_rule not in {"NO ACTION", "RESTRICT"}:
                    fk_args.append(f"onupdate=\"{update_rule}\"")
                args.append(f"ForeignKey({', '.join(fk_args)})")
            if column.data.get("COLUMN_KEY") == "PRI":
                args.append("primary_key=True")
            if column.data.get("IS_NULLABLE") == "NO" and column.data.get("COLUMN_KEY") != "PRI":
                args.append("nullable=False")
            if "auto_increment" in (column.data.get("EXTRA") or ""):
                args.append("autoincrement=True")
            column_line = f"    {column.name} = Column({', '.join(args)})"
            lines.append(column_line)
        lines.append("")
        registry_entries.append(f"    \"{table_name}\": {class_name},")

    lines.append("MODEL_REGISTRY: Dict[str, Type[Base]] = {")
    lines.extend(registry_entries)
    lines.append("}")
    lines.append("")
    lines.append("__all__ = [")
    for name in all_names:
        lines.append(f"    \"{name}\",")
    lines.append("    \"MODEL_REGISTRY\",")
    lines.append("]")
    lines.append("")

    generated_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    (destination / "__init__.py").write_text(
        "from __future__ import annotations\n"
        "import importlib\n"
        "from typing import Dict, Type\n"
        "\n"
        "from app.db.base import Base\n"
        "\n"
        "generated = importlib.import_module('.generated', __name__)\n"
        "MODEL_REGISTRY: Dict[str, Type[Base]] = generated.MODEL_REGISTRY\n"
        "__all__ = list(generated.__all__)\n"
        "for name in __all__:\n"
        "    globals()[name] = getattr(generated, name)\n"
        "\n"
        "METADATA = Base.metadata\n",
        encoding="utf-8",
    )


def generate_schemas(tables: dict[str, Any], destination: Path, summary: dict[str, Any]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    generated_file = destination / "generated.py"

    type_imports: set[str] = set()
    needs_datetime = False
    needs_decimal = False

    class_blocks: list[str] = []
    registry_entries: list[str] = []
    all_names: list[str] = []

    for table_name in sorted(tables):
        table = tables[table_name]
        columns = [ColumnMeta(name=col_name, data=col_data) for col_name, col_data in table["columns"].items()]
        columns.sort(key=lambda col: col.position)
        class_name = f"{to_class_name(table_name)}Schema"
        all_names.append(class_name)
        class_lines: list[str] = [f"class {class_name}(BaseModel):"]
        class_lines.append(f"    \"\"\"Schema for table {table_name}.\"\"\"")
        class_lines.append("    model_config = ConfigDict(from_attributes=True)")
        for column in columns:
            annotation, extras = map_python_type(column)
            if "datetime" in extras:
                needs_datetime = True
                extras.discard("datetime")
            if "List" in extras:
                type_imports.add("List")
                extras.discard("List")
            if "Decimal" in extras:
                needs_decimal = True
                extras.discard("Decimal")
            for item in extras:
                type_imports.add(item)
            nullable = column.data.get("IS_NULLABLE") == "YES"
            primary_key = column.data.get("COLUMN_KEY") == "PRI"
            if nullable or primary_key:
                annotation = f"{annotation} | None"
                default = " = None"
            else:
                default = ""
            class_lines.append(f"    {column.name}: {annotation}{default}")
        class_blocks.append("\n".join(class_lines))
        registry_entries.append(f"    \"{table_name}\": {class_name},")

    imports = ["from __future__ import annotations", ""]
    base_imports = ["from typing import Any, Dict, Type"]
    if "List" in type_imports:
        base_imports.append("from typing import List")
    if needs_decimal:
        base_imports.append("from decimal import Decimal")
    if needs_datetime:
        imports.append("from datetime import datetime")
    imports.extend(base_imports)
    imports.append("from pydantic import BaseModel, ConfigDict")
    imports.append("")
    imports.append(f"# Auto-generated on {summary['timestamp']} from db/schema.php")
    imports.append("")

    content = "\n".join(imports + class_blocks)
    content += "\n\nSCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {\n"
    content += "\n".join(registry_entries)
    content += "\n}\n\n__all__ = [\n"
    for name in all_names:
        content += f"    \"{name}\",\n"
    content += "    \"SCHEMA_REGISTRY\",\n]\n"

    generated_file.write_text(content + "\n", encoding="utf-8")

    (destination / "__init__.py").write_text(
        "from __future__ import annotations\n"
        "import importlib\n"
        "from typing import Dict, Type\n"
        "\n"
        "from pydantic import BaseModel\n"
        "\n"
        "generated = importlib.import_module('.generated', __name__)\n"
        "SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = generated.SCHEMA_REGISTRY\n"
        "__all__ = list(generated.__all__)\n"
        "for name in __all__:\n"
        "    globals()[name] = getattr(generated, name)\n",
        encoding="utf-8",
    )


def generate_er_diagram(tables: dict[str, Any], destination: Path, summary: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = ["%% Auto-generated ER diagram", f"%% Generated on {summary['timestamp']}", "erDiagram"]

    for table_name in sorted(tables):
        table = tables[table_name]
        columns = [ColumnMeta(name=col_name, data=col_data) for col_name, col_data in table["columns"].items()]
        columns.sort(key=lambda col: col.position)
        lines.append(f"    {table_name} {{")
        for column in columns:
            col_type = (column.data.get("DATA_TYPE") or "").upper()
            key = column.data.get("COLUMN_KEY") or ""
            flags: list[str] = []
            if key == "PRI":
                flags.append("PK")
            elif key == "UNI":
                flags.append("UQ")
            elif key == "MUL":
                flags.append("FK")
            suffix = f" {' '.join(flags)}" if flags else ""
            lines.append(f"        {col_type} {column.name}{suffix}")
        lines.append("    }")
    relation_lines: set[str] = set()
    for table_name, table in tables.items():
        fk_map = collect_foreign_keys(table)
        for details in fk_map.values():
            target_table = details.get("REFERENCED_TABLE_NAME")
            if not target_table:
                continue
            relation = f"    {table_name} }}o--|| {target_table} : \"{details['COLUMN_NAME']}\""
            relation_lines.add(relation)
    lines.extend(sorted(relation_lines))

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ensure_etl_scaffolding() -> None:
    ETL_DIR.mkdir(parents=True, exist_ok=True)
    files: dict[Path, str] = {
        ETL_DIR / "__init__.py": dedent(
            """
            from __future__ import annotations

            from pathlib import Path
            from typing import Any, Dict

            from sqlalchemy.engine import Engine

            from . import extract, load, transform


            def run_pipeline(source: Path, engine: Engine) -> Dict[str, Any]:
                \"\"\"Run the ETL pipeline and return statistics.\"\"\"
                raw = extract.extract_from_json(source)
                transformed = transform.transform_raw(raw)
                return load.load_into_database(engine, transformed)
            """
        ).strip()
    }

    files[ETL_DIR / "extract.py"] = dedent(
        """
        from __future__ import annotations

        import json
        from pathlib import Path
        from typing import Any, Dict, List


        def extract_from_json(source: Path) -> Dict[str, List[Dict[str, Any]]]:
            \"\"\"Extract data from a JSON dump produced from MySQL.\"\"\"
            with source.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                raise ValueError("Expected top-level object with table arrays")
            result: Dict[str, List[Dict[str, Any]]] = {}
            for table, rows in payload.items():
                if not isinstance(rows, list):
                    raise ValueError(f"Table {table} must contain a list of rows")
                normalised: List[Dict[str, Any]] = []
                for row in rows:
                    if not isinstance(row, dict):
                        raise ValueError(f"Row for {table} must be an object")
                    normalised.append(row)
                result[table] = normalised
            return result
        """
    ).strip()

    files[ETL_DIR / "transform.py"] = dedent(
        """
        from __future__ import annotations

        from typing import Any, Dict, List

        from app.schemas import SCHEMA_REGISTRY


        def transform_raw(raw: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
            \"\"\"Validate and coerce raw rows using the generated Pydantic schemas.\"\"\"
            transformed: Dict[str, List[Dict[str, Any]]] = {}
            for table, rows in raw.items():
                schema = SCHEMA_REGISTRY.get(table)
                if schema is None:
                    continue
                transformed_rows: List[Dict[str, Any]] = []
                for row in rows:
                    model = schema.model_validate(row)
                    transformed_rows.append(model.model_dump(mode="python", exclude_none=True))
                transformed[table] = transformed_rows
            return transformed
        """
    ).strip()

    files[ETL_DIR / "load.py"] = dedent(
        """
        from __future__ import annotations

        from typing import Any, Dict, List

        from sqlalchemy.engine import Engine
        from sqlalchemy.orm import Session

        from app.models import MODEL_REGISTRY
        from sqlalchemy import text


        def load_into_database(engine: Engine, transformed: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
            \"\"\"Load validated rows into the target database.\"\"\"
            stats: Dict[str, Any] = {"tables": {}, "total_rows": 0}
            if engine.dialect.name == "sqlite":
                with engine.begin() as connection:
                    connection.execute(text("PRAGMA foreign_keys=ON"))
            with Session(engine) as session:
                for table, rows in transformed.items():
                    model = MODEL_REGISTRY.get(table)
                    if model is None or not rows:
                        continue
                    for row in rows:
                        session.merge(model(**row))
                    session.flush()
                    stats["tables"][table] = len(rows)
                    stats["total_rows"] += len(rows)
                session.commit()
            return stats
        """
    ).strip()

    files[ETL_DIR / "run.py"] = dedent(
        """
        from __future__ import annotations

        import argparse
        import os
        from pathlib import Path

        from sqlalchemy import create_engine

        from app.db.base import Base
        import app.models  # noqa: F401
        from . import run_pipeline


        def main() -> None:
            parser = argparse.ArgumentParser(description="Run the stage03 ETL pipeline.")
            parser.add_argument("--input", type=Path, default=Path("backend/tests/etl/fixtures/sample_dump.json"), help="Path to JSON dump")
            parser.add_argument("--database-url", dest="database_url", default=os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:"))
            args = parser.parse_args()

            engine = create_engine(args.database_url, future=True)
            Base.metadata.create_all(engine)
            stats = run_pipeline(args.input, engine)
            print(f"Loaded {stats['total_rows']} rows across {len(stats['tables'])} tables")


        if __name__ == "__main__":
            main()
        """
    ).strip()

    for path, content in files.items():
        path.write_text(content + "\n", encoding="utf-8")


def ensure_tests(summary: dict[str, Any]) -> None:
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    fixtures_dir = TESTS_DIR / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    sample_fixture = {
        "actionsCategories": [
            {
                "actionsCategories_id": 1,
                "actionsCategories_name": "Operations",
                "actionsCategories_order": 1,
            }
        ],
        "actions": [
            {
                "actions_id": 1,
                "actions_name": "Check Inventory",
                "actionsCategories_id": 1,
                "actions_dependent": None,
                "actions_incompatible": None,
            },
            {
                "actions_id": 2,
                "actions_name": "Calibrate Lights",
                "actionsCategories_id": 1,
                "actions_dependent": None,
                "actions_incompatible": None,
            },
        ],
    }
    write_json(fixtures_dir / "sample_dump.json", sample_fixture)

    test_file = TESTS_DIR / "test_pipeline.py"
    test_content = dedent(
        """
        from __future__ import annotations

        from pathlib import Path

        from sqlalchemy import create_engine, text

        from app.db.base import Base
        import app.models  # noqa: F401
        from app.etl import run_pipeline

        FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_dump.json"


        def create_sqlite_engine():
            engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
            with engine.begin() as conn:
                conn.execute(text("PRAGMA foreign_keys=ON"))
            return engine


        def test_pipeline_loads_rows():
            engine = create_sqlite_engine()
            Base.metadata.create_all(engine)
            stats = run_pipeline(FIXTURE_PATH, engine)
            assert stats["tables"]["actions"] == 2
            assert stats["tables"]["actionsCategories"] == 1
            with engine.connect() as conn:
                total_actions = conn.execute(text('SELECT COUNT(*) FROM "actions"')).scalar_one()
                total_categories = conn.execute(text('SELECT COUNT(*) FROM "actionsCategories"')).scalar_one()
            assert total_actions == 2
            assert total_categories == 1
        """
    ).strip()
    test_file.write_text(test_content + "\n", encoding="utf-8")


def update_docs(summary: dict[str, Any]) -> None:
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    migration_doc = DOCS_DATA_DIR / "migration_plan.md"
    content = dedent(
        f"""
        # План миграции данных (Stage 03)

        ## Итоги извлечения
        - Схема извлечена из `db/schema.php` {summary['timestamp']}.
        - Найдено таблиц: {summary['table_count']}.
        - Всего столбцов: {summary['column_count']}.
        - Внешние ключи: {summary['foreign_key_count']}.

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
        """
    ).strip()
    migration_doc.write_text(content + "\n", encoding="utf-8")


def write_initial_report(summary: dict[str, Any]) -> None:
    report_path = STAGE_DIR / "report.md"
    content = dedent(
        f"""
        # Summary

        - Schema extracted on {summary['timestamp']} containing {summary['table_count']} tables and {summary['column_count']} columns.
        - Generated SQLAlchemy models and Pydantic schemas for all legacy tables.
        - ETL scaffolding ready under `backend/app/etl/` with CLI entrypoint.

        ## Artifacts

        - [ER diagram](../../docs/data/er_diagram.mmd)
        - [Schema snapshot](schema.json)
        - [SQLAlchemy models](../../backend/app/models/generated.py)
        - [Pydantic schemas](../../backend/app/schemas/generated.py)
        - [ETL pipeline](../../backend/app/etl/)

        ## Checks

        | Check | Result | Details |
        | --- | --- | --- |
        | Pytest (ETL) | ⏳ | Pending `make stage03-verify` |
        | Alembic migrations | ⏳ | Pending `make stage03-verify` |
        | Coverage | ⏳ | Pending `make stage03-verify` |

        ## Next Gate

        - Run `make stage03-verify` to execute automated tests and database checks.
        - Review updated documentation in `docs/data/migration_plan.md`.
        """
    ).strip()
    report_path.write_text(content + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate migration assets for stage03")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--schema-json", type=Path, default=STAGE_DIR / "schema.json")
    parser.add_argument("--er-diagram", type=Path, default=DOCS_DATA_DIR / "er_diagram.mmd")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.schema.exists():
        raise SystemExit(
            f"Schema file {args.schema} does not exist. "
            "Run vendor/bin/phinx schema:dump or provide --schema."
        )
    schema_data = run_php_to_json(args.schema.resolve())
    tables = schema_data.get("tables", {})
    column_count = sum(len(table.get("columns", {})) for table in tables.values())
    foreign_key_count = sum(len((table.get("foreign_keys") or {})) for table in tables.values())
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "table_count": len(tables),
        "column_count": column_count,
        "foreign_key_count": foreign_key_count,
    }
    write_json(args.schema_json, schema_data)
    generate_models(tables, MODELS_DIR, summary)
    generate_schemas(tables, SCHEMAS_DIR, summary)
    generate_er_diagram(tables, args.er_diagram, summary)
    ensure_etl_scaffolding()
    ensure_tests(summary)
    update_docs(summary)
    write_initial_report(summary)
    write_json(STAGE_DIR / "summary.json", summary)


if __name__ == "__main__":
    main()
