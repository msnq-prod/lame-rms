# План миграции AdamRMS с PHP-монолита на стек FastAPI + React + PostgreSQL

Документ перестроен под **полностью автоматизированный** подход: каждый этап оформлен как кодируемая задача для Codex5, которая
создаёт скрипты, пайплайны и проверки. Моя роль сводится к запуску готовых команд (`make stageXX`) и мониторингу итоговых отчётов.

## Каркас автоматизации, который Codex5 должен подготовить на этапе 0

Перед стартом этапов 1–12 Codex5 выполняет установочный шаг ("этап 0") и создаёт инфраструктуру самообслуживания:

1. Каталог `automation/` со структурой:
   - `stageXX/` — подпапка на каждый этап (01–12).
   - `stageXX/run.sh` — единая точка входа, вызывающая нужные `make`/`python`/`npm` команды.
   - `stageXX/self_check.sh` — сценарий самопроверки (линтеры, тесты, smoke, diff-валидация).
   - `stageXX/report.md` — итоговый отчёт (заполняется автоматически скриптом).
2. Расширение `Makefile` универсальными целями:
   - `make stageXX` → запускает `automation/stageXX/run.sh`.
   - `make stageXX-verify` → запускает `automation/stageXX/self_check.sh`.
   - `make stageXX-report` → выводит итоговый отчёт.
3. Обновление CI (GitHub Actions): workflow `codex5-migration.yml`, который по `workflow_dispatch`
   принимает параметр `stage` и последовательно выполняет `make stage${stage}` и `make stage${stage}-verify`.
4. Общий README раздел «Как запускать миграцию»: ссылка на таблицу этапов и команды.
5. Шаблон `automation/templates/report.md` с блоками: *Summary*, *Artifacts*, *Checks*, *Next Gate*.
6. Bootstrap-скрипт `automation/bin/ensure_tools.sh`, который сначала проверяет системные зависимости (`asdf`, `npm`/`npx`), затем ищет ключевые утилиты (`act`, `k6`, Playwright, Terraform, Helm, `bandit`, `schemathesis` и др.):
   - при наличии `asdf` использует плагины и версии из `.tool-versions`,
   - без `asdf` скачивает готовые релизы `act`, `k6`, `terraform`, `helm` в `automation/bin/tools/`,
   - для Python-инструментов пробует `pipx`, затем `python -m pip --user`,
   - для Playwright полагается на `npx playwright` и сохраняет статус установки браузеров,
   - по итогам пишет сводку в `status.json`, оставляя `warning`, если автоматическая подготовка невозможна.
7. Контракт статуса `automation/status.schema.json`, задающий структуру `status.json` и список обязательных ключей
   (`state`, `checks`, `artifacts`, `last_run`, `warnings`, `notes`, `extra`).

**Критерий готовности этапа 0** — все команды `make stageXX` для ещё не реализованных этапов завершаются сообщением
«Stage XX not implemented», CI workflow успешно прогоняет заглушечный шаг, README содержит обновлённую секцию.

---

## Таблица управления этапами

| № | Название | Команда запуска | Основной отчёт | Статусный файл |
|---|----------|-----------------|----------------|----------------|
| 01 | Подготовка репозитория и базовой инфраструктуры | `make stage01` | `automation/stage01/report.md` | `automation/stage01/status.json` |
| 02 | Инвентаризация монолита | `make stage02` | `automation/stage02/report.md` | `automation/stage02/status.json` |
| 03 | Анализ данных и миграция MySQL → PostgreSQL | `make stage03` | `automation/stage03/report.md` | `automation/stage03/status.json` |
| 04 | Каркас FastAPI | `make stage04` | `automation/stage04/report.md` | `automation/stage04/status.json` |
| 05 | Перенос доменной логики и API | `make stage05` | `automation/stage05/report.md` | `automation/stage05/status.json` |
| 06 | Аутентификация, авторизация и аудит | `make stage06` | `automation/stage06/report.md` | `automation/stage06/status.json` |
| 07 | Интеграции и фоновые задачи | `make stage07` | `automation/stage07/report.md` | `automation/stage07/status.json` |
| 08 | React + TypeScript SPA | `make stage08` | `automation/stage08/report.md` | `automation/stage08/status.json` |
| 09 | Клиентская авторизация и работа с API | `make stage09` | `automation/stage09/report.md` | `automation/stage09/status.json` |
| 10 | Тестирование и качество | `make stage10` | `automation/stage10/report.md` | `automation/stage10/status.json` |
| 11 | Инфраструктура и окружения | `make stage11` | `automation/stage11/report.md` | `automation/stage11/status.json` |
| 12 | Параллельная эксплуатация и вывод PHP | `make stage12` | `automation/stage12/report.md` | `automation/stage12/status.json` |

> В каждой подпапке создаётся `status.json`, валидируемый по общей схеме `automation/status.schema.json`.

---

## Формат описания этапа

Для каждого этапа ниже заданы четыре блока:

1. **Автоматизированная задача для Codex5** — какие файлы/скрипты должен сгенерировать агент.
2. **Самопроверка Codex5** — что должно выполняться внутри `self_check.sh` и каких метрик ожидать.
3. **Артефакты и отчётность** — что попадает в `report.md` и куда сохраняются материалы.
4. **Команда оператора (я)** — единственный шаг, который требуется запустить вручную.

---

## Этап 1. Подготовка репозитория и базовой инфраструктуры разработки

**Автоматизированная задача для Codex5**
- Заполнить `automation/stage01/run.sh`, который:
  1. Генерирует сценарий `automation/stage01/prepare_legacy.sh` с инструкциями по переносу монолита в `legacy/`.
  2. Генерирует каталоги `backend/`, `frontend/`, `infrastructure/`, `docs/` и `.gitkeep`.
  3. Обновляет `.gitignore`, `Makefile`, `README.md`, `.env.example` (backend/frontend), `scripts/bootstrap_dev.sh`.
  4. Создаёт CI заглушки (`.github/workflows/backend.yml`, `frontend.yml`).
  5. Настраивает pre-commit (`.pre-commit-config.yaml`).
  6. Инициализирует документацию в `docs/` и чек-лист `docs/checklists/stage01.md`.
- Скрипт обязан быть идемпотентным: при повторном запуске не ломать существующие файлы, а обновлять их.

**Самопроверка Codex5 (`automation/stage01/self_check.sh`)**
- Первый шаг — `STATUS_FILE=automation/stage01/status.json automation/bin/ensure_tools.sh`, который подготавливает окружение (проверяет `asdf`/`npm`, скачивает бинарники в `automation/bin/tools/`, обновляет `PATH` на обёртки). Если инструмент недоступен и не может быть установлен автоматически, скрипт фиксирует `warning`, а самопроверка аккуратно пропускает соответствующий шаг без падения.
- Проверяет структуру каталогов и наличие ключевых файлов (через `test`/`find`).
- При наличии маркера (`--apply` флаг запуска или файл-подтверждение) убеждается, что перенос в `legacy/` выполнен.
- Запускает `pre-commit run --all-files` и `make bootstrap-dev` из `scripts/bootstrap_dev.sh`.
- Сверяет, что `docs/checklists/stage01.md` отмечен полностью (встроенный YAML/Markdown парсер).
- Валидирует CI workflows через `act --dryrun` (или предоставляет заглушку, если `act` недоступен, но фиксирует предупреждение).
- Обновляет `automation/stage01/status.json` в соответствии со схемой `automation/status.schema.json`, складывая агрегированные
  результаты проверок в `extra.checks_summary`.

**Артефакты и отчётность**
- `automation/stage01/report.md` содержит: список созданных файлов, результаты `pre-commit`, вывод `act`.
- Дополнительные артефакты: чек-лист, README-обновления, скрипт запуска окружения.

**Команда оператора**
- `make stage01`, затем после ревью вручную запустить `automation/stage01/prepare_legacy.sh`, после чего `make stage01-verify && make stage01-report`.

---

## Этап 2. Инвентаризация функциональности PHP-монолита

**Автоматизированная задача для Codex5**
- `automation/stage02/run.sh`:
  1. Парсит `src/` и `legacy/` для построения каталога файлов (JSON/CSV).
  2. Генерирует `docs/inventory/` с таблицами (Markdown + CSV) и диаграммами (mermaid/plantuml).
  3. Создаёт backlog в `docs/backlog/migration_backlog.yaml` с оценками, зависимостями, рисками.
  4. Сохраняет отчёты по метрикам и cron-задачам в `docs/inventory/metrics.md` и `docs/inventory/cron.md`.
  5. Формирует экспорт API (OpenAPI или Postman) в `docs/inventory/api/`.

**Самопроверка Codex5 (`automation/stage02/self_check.sh`)**
- Запускает `STATUS_FILE=automation/stage02/status.json automation/bin/ensure_tools.sh` и обрабатывает отсутствие инструментов как `warning` с graceful skip конкретных проверок.
- Убеждается, что количество файлов в отчёте соответствует фактическому (`find legacy -type f`).
- Валидирует YAML backlog (через `yamllint`) и JSON/CSV схемы.
- Проверяет наличие диаграмм (существование файлов `.mmd`/`.puml`).
- Сверяет, что ключевые риски помечены severity (`critical|high|medium|low`).
- Обновляет `automation/stage02/status.json` по контракту `automation/status.schema.json`, сохраняя сводку ключевых
  изменений в `extra.diff_summary`.

**Артефакты и отчётность**
- `automation/stage02/report.md`: таблица рисков, ссылки на диаграммы, экспорт API, backlog.

**Команда оператора**
- `make stage02 && make stage02-verify && make stage02-report`.

---

## Этап 3. Анализ данных и миграция MySQL → PostgreSQL

**Автоматизированная задача для Codex5**
- `automation/stage03/run.sh`:
  1. Извлекает схему из Phinx и MySQL, генерирует ER-диаграмму (`docs/data/er_diagram.mmd`).
  2. Создаёт SQLAlchemy-модели и Pydantic-схемы в `backend/app/models/` и `backend/app/schemas/`.
  3. Настраивает Alembic (`backend/alembic.ini`, `backend/alembic/versions/`).
  4. Формирует ETL в `backend/app/etl/` с пайплайном `python -m app.etl.run`.
  5. Создаёт тесты (`backend/tests/etl/`) и фикстуры данных.
  6. Обновляет документацию `docs/data/migration_plan.md` и план отката.

**Самопроверка Codex5**
- Выполняет `STATUS_FILE=automation/stage03/status.json automation/bin/ensure_tools.sh` и переводит отсутствующие зависимости в `warning`, корректно пропуская соответствующие проверки.
- `pytest backend/tests/etl -q`.
- `alembic upgrade head` против временной БД (использовать docker-compose service `postgres-test`; при отсутствии Docker задействовать `automation/bin/run_pg_tmp.py`, выполнить миграцию по возвращённому URI и завершить временный экземпляр).
- Логи запуска миграции сохраняются в `automation/stage03/alembic.log`.
- Проверка foreign keys и сравнение количества строк до/после ETL.
- Генерация отчёта покрытия тестов для ETL.
- Обновляет `automation/stage03/status.json` на базе схемы `automation/status.schema.json`, добавляя показатели покрытия
  и статистику ETL в `extra.coverage` и `extra.etl_stats`.

**Артефакты и отчётность**
- `automation/stage03/report.md`: результаты тестов, покрытие, ссылки на ER-диаграмму.

**Команда оператора**
- `make stage03 && make stage03-verify && make stage03-report`.

---

## Этап 4. Развитие каркаса FastAPI

**Автоматизированная задача для Codex5**
- Создать структуру модулей (`core/`, `api/routes/`, `services/`, `repositories/`, `auth/`, `integrations/`).
- Настроить конфигурацию (Pydantic Settings), логирование (structlog), middleware, обработчики ошибок.
- Подготовить `backend/pyproject.toml`, `requirements.txt`, `pre-commit` хуки.
- Добавить OpenAPI генерацию и базовые тесты (`backend/tests/api/test_health.py`).
- Скрипт `run.sh` разворачивает каркас, выполняет миграции, запускает линтеры.

**Самопроверка Codex5**
- Перед запуском линтеров вызывает `STATUS_FILE=automation/stage04/status.json automation/bin/ensure_tools.sh` и, если инструмент недоступен, фиксирует `warning` и пропускает конкретный шаг.
- `ruff check backend`, `mypy backend`, `pytest backend/tests/api -q`.
- Проверка, что OpenAPI сгенерирован (`backend/openapi.json`).
- Smoke запуск `uvicorn app.main:app --dry-run` (или `--app-dir`).
- Обновляет `automation/stage04/status.json` по схеме `automation/status.schema.json`, фиксируя сведения об OpenAPI и smoke-проверке в `extra.api_snapshot` и `extra.smoke`.

**Артефакты и отчётность**
- `automation/stage04/report.md`: вывод линтеров/тестов, список эндпоинтов.

**Команда оператора**
- `make stage04 && make stage04-verify && make stage04-report`.

---

## Этап 5. Перенос доменной логики и API

**Автоматизированная задача для Codex5**
- Реализовать сервисный слой, репозитории, Pydantic-схемы и маршруты FastAPI согласно backlog.
- Настроить feature flags (например, `backend/app/feature_flags.py` + конфиг).
- Подготовить нагрузочные профили (`backend/loadtests/`) и интеграционные тесты (`backend/tests/integration/`).
- Скрипт `run.sh` переносит выбранные домены (assets, projects, finance и т.д.) на основании YAML backlog.

**Самопроверка Codex5**
- Запускает `STATUS_FILE=automation/stage05/status.json automation/bin/ensure_tools.sh` и переводит недоступные инструменты (`k6`, `schemathesis` и т.д.) в `warning`, аккуратно пропуская их проверки.
- `pytest backend/tests/integration -q` + генерация Allure/HTML отчёта.
- Нагрузочный тест (`k6 run backend/loadtests/main.js`) с метриками в `automation/stage05/metrics.json`.
- Сравнение контрактов (`schemathesis` или `pytest --schemathesis`) против legacy OpenAPI.
- Обновляет `automation/stage05/status.json` по схеме `automation/status.schema.json`, помещая результаты нагрузочных тестов и контрактного сравнения в `extra.performance` и `extra.contract_diff`.

**Артефакты и отчётность**
- Отчёт с перечислением перенесённых эндпоинтов, ссылками на документацию, результатами нагрузочных тестов.

**Команда оператора**
- `make stage05 && make stage05-verify && make stage05-report`.

**Критерий готовности этапа 5** — закрыты backlog-элементы `M5-001`, `M5-002`, `M5-003` и `M5-004`,
обеспечивающие паритет по критичным маршрутам:

- `/api/assets/searchAssetsBarcode` и весь набор `/api/assets/barcodes/*` для сканеров;
- `/api/assets/list`, `/api/assets/newAssetType`, `/api/assets/editAsset`, `/api/assets/delete`, `/api/assets/transfer` для CRUD-операций;
- `/api/assets/export` для выгрузки в CSV и синхронизации с внешними системами.

---

## Этап 6. Аутентификация, авторизация и аудит

**Автоматизированная задача для Codex5**
- Реализовать модуль `backend/app/auth/` (JWT, refresh, MFA, audit trail).
- Обновить фронтенд SDK/типизацию (`frontend/src/shared/api/auth.ts`).
- Настроить мониторинг событий безопасности (`backend/app/monitoring/security.py`).
- Скрипт `run.sh` запускает миграции, применяет конфиги ролей, обновляет документацию безопасности.

**Самопроверка Codex5**
- Перед тестами вызывает `STATUS_FILE=automation/stage06/status.json automation/bin/ensure_tools.sh`, недостающие зависимости (Playwright, bandit и др.) отражает как `warning` и пропускает соответствующие проверки.
- Юнит-тесты на auth-флоу, e2e сценарии в Playwright (`frontend/tests/auth.spec.ts`).
- Static анализ (`bandit`, `npm run lint`).
- Проверка алертов (эмуляция события, убедиться, что alert записан в лог/метрику).
- Обновляет `automation/stage06/status.json` в формате `automation/status.schema.json`, сохраняя найденные замечания и состояние алертов в `extra.security_findings` и `extra.alerts`.

**Артефакты и отчётность**
- Отчёт с тестами, чек-листом политик безопасности, ссылками на мониторинг.

**Команда оператора**
- `make stage06 && make stage06-verify && make stage06-report`.

---

## Этап 7. Интеграции и фоновые задачи

**Автоматизированная задача для Codex5**
- Перенести адаптеры внешних сервисов в `backend/app/integrations/`.
- Настроить очередь задач (Celery/Redis) и `worker` сервис в docker-compose.
- Создать cron/beat расписания, реализовать fallback логику.
- Обновить фронтенд для отображения прогресса асинхронных операций.

**Самопроверка Codex5**
- Перед запуском интеграционных тестов выполняет `STATUS_FILE=automation/stage07/status.json automation/bin/ensure_tools.sh`, а недостающие утилиты фиксирует как `warning` с graceful skip.
- Контрактные тесты адаптеров (`pytest backend/tests/integrations`).
- Запуск воркера и тестового задания с проверкой отчёта (`celery -A app.worker inspect ping`).
- Проверка мониторинга (Prometheus exporter, графики).
- Обновляет `automation/stage07/status.json` согласно `automation/status.schema.json`, добавляя показатели очереди и мониторинга в `extra.queue_health` и `extra.monitoring`.
- В `automation/stage07/status.json` фиксирует правило: `state=completed` допустим только при успешном `celery inspect ping`; при любом другом результате очередь помечается как `needs_attention` с расшифровкой в `extra.queue_health`.
- Для локальной отладки описывает, как поднять memory fallback вручную: `APP_CELERY_BROKER_URL=memory:// APP_CELERY_RESULT_BACKEND=cache+memory:// APP_QUEUE_FALLBACK_ENABLED=true PYTHONPATH=backend backend/.venv/bin/python -m celery -A app.worker worker --loglevel=info --concurrency=1 --pool=solo` и последующий `PYTHONPATH=backend backend/.venv/bin/python -m celery -A app.worker inspect ping`.

**Артефакты и отчётность**
- `automation/stage07/report.md`: список интеграций, статус очереди, мониторинг.

**Команда оператора**
- `make stage07 && make stage07-verify && make stage07-report`.

---

## Этап 8. Реализация React + TypeScript SPA

**Автоматизированная задача для Codex5**
- Инициализировать фронтенд (Vite/Next) в `frontend/`, настроить архитектуру модулей.
- Настроить ESLint/Prettier/Stylelint/Husky, Storybook.
- Реализовать базовые страницы, дизайн-систему, загрузку файлов, локализацию.
- Генерировать типы из OpenAPI (`npm run openapi`), обновлять клиент.

**Самопроверка Codex5**
- Перед фронтенд-проверками запускает `STATUS_FILE=automation/stage08/status.json automation/bin/ensure_tools.sh` и, если зависимость отсутствует (Storybook, Playwright, Lighthouse), оформляет `warning` и пропускает шаг.
- `npm run lint`, `npm run test`, `npm run storybook:check`.
- Визуальная регрессия (Chromatic/Playwright) с сохранением скриншотов в `automation/stage08/screenshots/`.
- Lighthouse audit (`npm run lighthouse -- --output-path automation/stage08/lighthouse.json`).
- Обновляет `automation/stage08/status.json` по `automation/status.schema.json`, добавляя результаты визуальной регрессии и Lighthouse в `extra.visual_tests` и `extra.lighthouse`.

**Артефакты и отчётность**
- Отчёт со списком страниц, компонентов, ссылками на Storybook, результатами Lighthouse.

**Команда оператора**
- `make stage08 && make stage08-verify && make stage08-report`.

---

## Этап 9. Клиентская авторизация и работа с API

**Автоматизированная задача для Codex5**
- Реализовать клиентские фичи авторизации, управление ролями, обработку ошибок и offline-режим.
- Настроить аудит UI, метрики Web Vitals, сбор UX-данных.
- Обновить e2e тесты для критичных сценариев (`frontend/tests/e2e/`).

**Самопроверка Codex5**
- Использует `STATUS_FILE=automation/stage09/status.json automation/bin/ensure_tools.sh` перед запуском e2e и метрик; отсутствующие зависимости помечаются `warning`, а проверки пропускаются без фейла.
- `npm run test:e2e` (Playwright), `npm run web-vitals` (с сохранением в `automation/stage09/metrics.json`).
- Проверка feature flags переключением окружения (`npm run toggle-flags -- --target legacy`/`new`).
- Генерация accessibility отчёта (axe/pa11y) → `automation/stage09/a11y.html`.
- Обновляет `automation/stage09/status.json` согласно `automation/status.schema.json`, фиксируя UX-метрики и отчёт по доступности в `extra.ux_metrics` и `extra.accessibility`.

**Артефакты и отчётность**
- Отчёт с результатами e2e, UX-метрик, accessibility, списком фичефлагов.

**Команда оператора**
- `make stage09 && make stage09-verify && make stage09-report`.

---

## Этап 10. Тестирование и качество

**Автоматизированная задача для Codex5**
- Сформировать тестовую пирамиду и настроить интеграцию в CI/CD.
- Добавить статический анализ, покрытие, визуальную регрессию, SAST/DAST, проверки зависимостей.
- Настроить генерацию QA-дашбордов (например, выводом в `automation/stage10/dashboard.json`).

**Самопроверка Codex5**
- Перед запуском QA-команд выполняет `STATUS_FILE=automation/stage10/status.json automation/bin/ensure_tools.sh`, переводя недоступные утилиты (`act`, SAST и др.) в `warning` и пропуская проверки без падения.
- Запуск всех тестов (`make test`, `make lint`), сбор coverage отчётов.
- Валидация конфигураций CI через `act`/`ci-sim`.
- Проверка, что отчёты загружаются в артефакты (например, имитация upload).
- Обновляет `automation/stage10/status.json` по схеме `automation/status.schema.json`, добавляя агрегированные QA-метрики в `extra.qa_dashboard`.

**Артефакты и отчётность**
- Отчёт о качестве, ссылки на покрытия, чек-лист приёмки.

**Команда оператора**
- `make stage10 && make stage10-verify && make stage10-report`.

---

## Этап 11. Инфраструктура и окружения

**Автоматизированная задача для Codex5**
- Сгенерировать Dockerfile'ы, docker-compose, Terraform/Helm шаблоны.
- Настроить CI/CD pipeline: сборка контейнеров, миграции, деплой, smoke-тесты.
- Добавить мониторинг, резервное копирование, планы DR.

**Самопроверка Codex5**
- Делает `STATUS_FILE=automation/stage11/status.json automation/bin/ensure_tools.sh` перед инфраструктурными проверками; отсутствие Terraform/Helm/Docker фиксируется `warning` с graceful skip соответствующих шагов.
- Локальный прогон `docker-compose up` в режиме CI (можно headless).
- Проверка Terraform/Helm (`terraform validate`, `helm lint`).
- Имитация деплоя (dry-run) и запуск smoke-тестов.
- Обновляет `automation/stage11/status.json` по контракту `automation/status.schema.json`, сохраняя результаты инфраструктурных проверок в `extra.deployment_checks`.

**Артефакты и отчётность**
- Репозиторий инфраструктуры, dashboards, планы DR/backup.

**Команда оператора**
- `make stage11 && make stage11-verify && make stage11-report`.

---

## Этап 12. Параллельная эксплуатация и вывод PHP

**Автоматизированная задача для Codex5**
- Сформировать стратегию переключения трафика (reverse proxy, feature flags, shadow traffic).
- Настроить синхронизацию данных и мониторинг параллельной эксплуатации.
- Создать финальный чек-лист вывода legacy и автоматизированный smoke-тест после отключения.
- Подготовить коммуникационные шаблоны для пользователей и службы поддержки.

**Самопроверка Codex5**
- Перед эмуляцией переключения вызывает `STATUS_FILE=automation/stage12/status.json automation/bin/ensure_tools.sh`, отсутствие зависимостей отмечает `warning` и пропускает шаги без аварийного завершения.
- Эмуляция переключения (`make blue-green-simulate`), проверка latency/ошибок.
- Smoke-тесты новых сервисов после отключения legacy.
- Валидация полного чек-листа (все пункты `done=true`).
- Обновляет `automation/stage12/status.json` по схеме `automation/status.schema.json`, размещая отчёт по переключению и финальные метрики в `extra.cutover_report`.

**Артефакты и отчётность**
- Отчёт о переключении, финальный чек-лист, результаты smoke-тестов.

**Команда оператора**
- `make stage12 && make stage12-verify && make stage12-report`.

---

## Завершение и контроль

- После каждого успешного этапа Codex5 автоматически коммитит изменения в ветку `migration/stageXX` и формирует Pull Request.
- CI-пайплайн запускается автоматически через `workflow_dispatch` и сохраняет отчёты как артефакты.
- Если `self_check.sh` завершился с ошибкой, статус в `status.json` (валидируется по `automation/status.schema.json`) выставляется в `failed` и PR помечается лейблом `needs-attention`.
- По завершении всех этапов запускается финальный сценарий `automation/finalize.sh`, который собирает агрегированный отчёт,
  архивирует все артефакты и валидирует каждый `status.json` по общей схеме.

Таким образом, весь план представляет собой последовательность полностью автоматизированных шагов. Мне достаточно выполнять
команду `make stageXX` по мере готовности, контролировать отчёты и при необходимости инициировать повторный запуск.
