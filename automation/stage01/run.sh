#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

log() {
  printf '[stage01] %s\n' "$1"
}

ensure_dir() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    log "Creating directory ${dir#$REPO_ROOT/}"
    mkdir -p "$dir"
  fi
}

add_gitignore_block() {
  local file="$1"
 local block="$(cat <<'GIT'
# Legacy application
legacy/vendor/
legacy/storage/
legacy/.env
legacy/.env.*
!legacy/.env.example

# Backend virtual environments
backend/.venv/
backend/.pytest_cache/
backend/.mypy_cache/
backend/.ruff_cache/
backend/__pycache__/
backend/htmlcov/
backend/.coverage

# Frontend artifacts
frontend/node_modules/
frontend/build/
frontend/dist/
frontend/.next/
frontend/.cache/

# Infrastructure tooling
infrastructure/.terraform/
*.tfstate
*.tfstate.backup

# Automation artifacts
automation/*/artifacts/
GIT
)"
  block="$(printf '%s' "$block" | sed 's/\\n$//')"
  python3 - "$file" "$block" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
block = sys.argv[2]
text = ""
if path.exists():
    text = path.read_text()

normalized = block.strip()
block_lines = [line for line in normalized.splitlines()]
block_set = {line for line in block_lines if line.strip()}

if text:
    existing_lines = text.splitlines()
    filtered = [line for line in existing_lines if line not in block_set]
else:
    filtered = []

if filtered and filtered[-1].strip() == "":
    filtered = filtered[:-1]

filtered_text = "\n".join(filtered).rstrip()
if filtered_text:
    filtered_text += "\n\n" + normalized + "\n"
else:
    filtered_text = normalized + "\n"

path.write_text(filtered_text)
PY
}

update_makefile() {
  local file="$REPO_ROOT/Makefile"
  python3 - "$file" <<'PY'
from pathlib import Path

path = Path(__import__("sys").argv[1])
text = path.read_text()

if "bootstrap-dev" not in text:
    insertion = "\n.PHONY: bootstrap-dev\nbootstrap-dev:\n\t./scripts/bootstrap_dev.sh\n"
    text = text.rstrip() + insertion + "\n"
else:
    lines = text.splitlines()
    marker = ".PHONY: bootstrap-dev"
    if marker not in lines:
        lines.append(marker)
    target = "bootstrap-dev:\n\t./scripts/bootstrap_dev.sh"
    if not any(line.startswith("bootstrap-dev:") for line in lines):
        lines.extend(target.splitlines())
    text = "\n".join(lines) + "\n"
path.write_text(text)
PY
}

rename_readme() {
  if [[ -f "$REPO_ROOT/Readme.md" && ! -f "$REPO_ROOT/README.md" ]]; then
    log "Renaming Readme.md -> README.md"
    mv "$REPO_ROOT/Readme.md" "$REPO_ROOT/README.md"
  fi
}

update_readme() {
  local file="$REPO_ROOT/README.md"
  if [[ ! -f "$file" ]]; then
    log "Seeding README.md"
    cat <<'MARK' >"$file"
# AdamRMS Migration

See docs/migration_plan.md for migration details.
MARK
  fi
  python3 - "$file" <<'PY'
from pathlib import Path
import re

path = Path(__import__("sys").argv[1])
text = path.read_text()

layout_section = "## Repository layout (migration)"
layout_block = "\n".join([
    layout_section,
    "",
    "- `legacy/` — исходный PHP-монолит (после запуска automation/stage01/prepare_legacy.sh)",
    "- `backend/` — новое серверное приложение на Python/FastAPI",
    "- `frontend/` — клиентское приложение на React/TypeScript",
    "- `infrastructure/` — инфраструктурные манифесты и IaC",
    "- `docs/` — документация по миграции и технические материалы",
    "- `automation/` — сценарии этапов миграции",
])

if layout_section not in text:
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + layout_block + "\n"
else:
    pattern = re.compile(r"## Repository layout \(migration\)(?:\n.*?)(?=\n## |\Z)", re.S)
    text = pattern.sub(layout_block + "\n", text)

commands_section = "## Stage 01 quickstart"
commands_block = "\n".join([
    commands_section,
    "",
    "1. Выполните `make stage01`, чтобы подготовить структуру репозитория.",
    "2. Просмотрите и при необходимости отредактируйте `automation/stage01/prepare_legacy.sh`.",
    "3. Запустите скрипт переноса `automation/stage01/prepare_legacy.sh` (после ревью).",
    "4. Выполните `make stage01-verify` и `make stage01-report` для самопроверки и отчёта.",
])

if commands_section not in text:
    text += "\n" + commands_block + "\n"
else:
    pattern = re.compile(r"## Stage 01 quickstart(?:\n.*?)(?=\n## |\Z)", re.S)
    text = pattern.sub(commands_block + "\n", text)

path.write_text(text)
PY
}

update_env_examples() {
  local root_file="$REPO_ROOT/.env.example"
  cat <<'ENV' >"$root_file"
# Global settings
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=app
DATABASE_URL=postgresql+psycopg://app:app@db:5432/app

# Backend service
BACKEND_PORT=8000
BACKEND_HOST=127.0.0.1
BACKEND_LOG_LEVEL=info

# Frontend service
FRONTEND_PORT=3000
FRONTEND_API_URL=http://localhost:8000/api

# Legacy compatibility
LEGACY_BASE_URL=http://localhost:8080
ENV

  cat <<'BENV' >"$REPO_ROOT/backend/.env.example"
# Backend specific overrides
BACKEND_PORT=8000
BACKEND_WORKERS=4
DATABASE_URL=${DATABASE_URL:-postgresql+psycopg://app:app@db:5432/app}
BENV

  cat <<'FENV' >"$REPO_ROOT/frontend/.env.example"
# Frontend specific overrides
FRONTEND_PORT=3000
VITE_API_URL=${FRONTEND_API_URL:-http://localhost:8000/api}
FENV
}

create_gitkeep() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    local file="$dir/.gitkeep"
    if [[ ! -f "$file" ]]; then
      log "Adding ${file#$REPO_ROOT/}"
      touch "$file"
    fi
  fi
}

write_prepare_legacy() {
  local file="$REPO_ROOT/automation/stage01/prepare_legacy.sh"
  cat <<'LEG' >"$file"
#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
LEGACY_DIR="$REPO_ROOT/legacy"

mkdir -p "$LEGACY_DIR"

MARKER="$LEGACY_DIR/.migration_applied"

PHP_PATHS=(
  "src"
  "db"
  "composer.json"
  "composer.lock"
  "phinx.php"
  "migrate.sh"
  "php-fpm.conf"
  "Dockerfile"
  "docker-compose.yml"
  "app.json"
)

move_path() {
  local rel="$1"
  local src="$REPO_ROOT/$rel"
  local dest="$LEGACY_DIR/$rel"
  if [[ -e "$dest" ]]; then
    printf '✔ %s already in legacy\n' "$rel"
    return
  fi
  if [[ -e "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    printf '→ Moving %s to legacy/\n' "$rel"
    mv "$src" "$dest"
  else
    printf '⚠ %s not found in repository root\n' "$rel"
  fi
}

for item in "${PHP_PATHS[@]}"; do
  move_path "$item"
done

touch "$MARKER"
printf 'Legacy migration marker written to %s\n' "$MARKER"
LEG
  chmod +x "$file"
}

ensure_scripts() {
  local file="$REPO_ROOT/scripts/bootstrap_dev.sh"
  cat <<'BOOT' >"$file"
#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

copy_if_missing() {
  local source="$1"
  local target="$2"
  if [[ -f "$source" && ! -f "$target" ]]; then
    printf '[bootstrap-dev] Copying %s -> %s\n' "${source#$REPO_ROOT/}" "${target#$REPO_ROOT/}"
    cp "$source" "$target"
  fi
}

copy_if_missing "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
copy_if_missing "$REPO_ROOT/backend/.env.example" "$REPO_ROOT/backend/.env"
copy_if_missing "$REPO_ROOT/frontend/.env.example" "$REPO_ROOT/frontend/.env"

if command -v python3 >/dev/null 2>&1; then
  VENV_DIR="$REPO_ROOT/backend/.venv"
  if [[ ! -d "$VENV_DIR" ]]; then
    printf '[bootstrap-dev] Creating backend virtualenv at %s\n' "${VENV_DIR#$REPO_ROOT/}"
    python3 -m venv "$VENV_DIR"
  else
    printf '[bootstrap-dev] Backend virtualenv already exists\n'
  fi
else
  printf '[bootstrap-dev] python3 not found, skipping virtualenv creation\n'
fi

printf '[bootstrap-dev] Done\n'
BOOT
  chmod +x "$file"
}

create_workflows() {
  local backend_workflow="$REPO_ROOT/.github/workflows/backend.yml"
  cat <<'BWF' >"$backend_workflow"
name: Backend CI

on:
  push:
    paths:
      - 'backend/**'
      - '.github/workflows/backend.yml'
  pull_request:
    paths:
      - 'backend/**'
      - '.github/workflows/backend.yml'
  workflow_dispatch:

jobs:
  lint:
    name: Run backend checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install tooling
        run: |
          python -m pip install --upgrade pip
          pip install pre-commit
      - name: Backend static checks
        run: |
          pre-commit run --all-files --show-diff-on-failure --hook-stage manual
BWF

  local frontend_workflow="$REPO_ROOT/.github/workflows/frontend.yml"
  cat <<'FWF' >"$frontend_workflow"
name: Frontend CI

on:
  push:
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend.yml'
  pull_request:
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend.yml'
  workflow_dispatch:

jobs:
  lint:
    name: Run frontend checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          if [ -f frontend/package.json ]; then
            cd frontend && npm install
          else
            echo 'No frontend package.json found, skipping install'
          fi
      - name: Lint placeholder
        run: echo 'Frontend lint placeholder'
FWF
}

write_pre_commit() {
  local file="$REPO_ROOT/.pre-commit-config.yaml"
  cat <<'PCFG' >"$file"
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
      - id: ruff
        args: ["--fix"]
        additional_dependencies: []
        files: "^(backend/|automation/).*\\.py$"
      - id: ruff-format
        files: "^(backend/|automation/).*\\.py$"
PCFG
}

write_checklist() {
  local file="$REPO_ROOT/docs/checklists/stage01.md"
  cat <<'CHECK' >"$file"
---
stage: "01"
title: "Подготовка репозитория и базовой инфраструктуры разработки"
items:
  - id: directories
    description: "Созданы каталоги backend/, frontend/, infrastructure/, legacy/ с .gitkeep"
    done: true
  - id: gitignore
    description: "Обновлён .gitignore для новой структуры"
    done: true
  - id: env
    description: "Обновлены файлы окружения и bootstrap-скрипт"
    done: true
  - id: ci
    description: "Добавлены заготовки GitHub Actions для backend и frontend"
    done: true
  - id: precommit
    description: "Настроена конфигурация pre-commit"
    done: true
  - id: documentation
    description: "README и чек-лист обновлены"
    done: true
---

# Stage 01 Checklist

- [x] Каталоги и заглушки подготовлены
- [x] Настроен .gitignore и файлы окружения
- [x] Добавлены CI workflows и pre-commit
- [x] Обновлена документация и чек-лист
CHECK
}

write_created_files_manifest() {
  local file="$REPO_ROOT/automation/stage01/created_files.txt"
  cat <<'LIST' >"$file"
automation/stage01/prepare_legacy.sh
backend/.env.example
backend/.gitkeep
frontend/.env.example
frontend/.gitkeep
infrastructure/.gitkeep
legacy/.gitkeep
scripts/bootstrap_dev.sh
.github/workflows/backend.yml
.github/workflows/frontend.yml
.pre-commit-config.yaml
docs/checklists/stage01.md
LIST
}

update_report_skeleton() {
  local file="$REPO_ROOT/automation/stage01/report.md"
  cat <<'RPT' >"$file"
# Summary

- Stage 01 scaffolding executed via `automation/stage01/run.sh`.
- Use `make stage01-verify` to populate the sections below with live command output.

# Artifacts

- `automation/stage01/created_files.txt`
- `docs/checklists/stage01.md`

# Checks

- Placeholder: self-check will capture `pre-commit run --all-files` output.
- Placeholder: self-check will capture `act --dryrun` output.

# Next Gate

- Review `automation/stage01/prepare_legacy.sh` and execute it to move the PHP monolith into `legacy/`.
- Run `make stage01-verify` followed by `make stage01-report`.
RPT
}

main() {
  log "Preparing repository structure for Stage 01"
  rename_readme

  ensure_dir "$REPO_ROOT/backend"
  ensure_dir "$REPO_ROOT/frontend"
  ensure_dir "$REPO_ROOT/infrastructure"
  ensure_dir "$REPO_ROOT/docs"
  ensure_dir "$REPO_ROOT/docs/checklists"
  ensure_dir "$REPO_ROOT/legacy"
  ensure_dir "$REPO_ROOT/scripts"

  create_gitkeep "$REPO_ROOT/backend"
  create_gitkeep "$REPO_ROOT/frontend"
  create_gitkeep "$REPO_ROOT/infrastructure"
  create_gitkeep "$REPO_ROOT/legacy"

  add_gitignore_block "$REPO_ROOT/.gitignore"
  update_makefile
  update_readme
  update_env_examples
  ensure_scripts
  create_workflows
  write_pre_commit
  write_checklist
  write_prepare_legacy
  write_created_files_manifest
  update_report_skeleton

  log "Stage 01 run script completed"
}

main "$@"
