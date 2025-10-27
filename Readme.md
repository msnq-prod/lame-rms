# AdamRMS

![GitHub release (latest by date)](https://img.shields.io/github/v/release/adam-rms/adam-rms)
![GitHub repo size](https://img.shields.io/github/repo-size/adam-rms/adam-rms)
![GitHub issues](https://img.shields.io/github/issues/adam-rms/adam-rms)
![GitHub closed issues](https://img.shields.io/github/issues-closed/adam-rms/adam-rms)
![GitHub pull requests](https://img.shields.io/github/issues-pr/adam-rms/adam-rms)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/adam-rms/adam-rms)
![GitHub](https://img.shields.io/github/license/adam-rms/adam-rms)
![GitHub stars](https://img.shields.io/github/stars/adam-rms/adam-rms)
![GitHub contributors](https://img.shields.io/github/contributors/adam-rms/adam-rms)
![GitHub](https://img.shields.io/github/release/adam-rms/adam-rms/all)

AdamRMS is an advanced Rental Management System for Theatre, AV & Broadcast, written in PHP with the Twig Templating engine, and deployed using a pre-built docker container.

It is available as a hosted solution or to be self-hosted as a docker container.

Check out who is using AdamRMS: [stats](https://telemetry.bithell.studio/projects/adam-rms).

## Docker Images

A maintained docker image is provided - hosted on GitHub Packages as [adam-rms/adam-rms](https://github.com/orgs/adam-rms/packages?repo_name=adam-rms). Due to Docker Hub's pricing changes, the Docker Hub images are no longer maintained, but were identical to the GitHub Packages images which are still available to use.

When self-hosting, please pay attention to the license terms of the software you are using. AdamRMS is licenced under AGPLv3, which means changes you make to the source code must be kept open source.

## Getting Started with contributing to this repo

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?ref=main&repo=217888995)

Thanks for your interest in developing and improving AdamRMS!
Contributions are very welcome - please see [the website](https://adam-rms.com/contributing) for a guide and for more info about this repo.

This repo has a configured devcontainer for use with GitHub Codespaces or VSCode. If you have a GitHub Codespaces subscription (paid), you can use this to get started with the project in the web, or if you have access to VSCode on your computer (free) you can get started by cloning the repo and opening it in VSCode, then [opening the project in a devcontainer](https://code.visualstudio.com/docs/devcontainers/tutorial).

## Как запускать миграцию

Автоматизированная миграция разбита на этапы `stage01`–`stage12` согласно [плану](docs/migration_plan.md). Каждый этап имеет единый набор команд, которые можно запускать локально или через CI.

0. (Опционально) Установите и проверьте вспомогательные утилиты командой `automation/bin/ensure_tools.sh`. Скрипт создаёт файл статуса (по умолчанию `automation/status.json` или значение переменной `STATUS_FILE`), соответствующий схеме `automation/status.schema.json`, фиксирует предупреждения о недостающих инструментах и собирает краткую сводку в `extra.tools_summary`.
1. Определите номер этапа, который нужно выполнить, и подставьте его вместо `XX`.
2. Запустите `make stageXX`, чтобы выполнить основной сценарий (`automation/stageXX/run.sh`).
3. Запустите `make stageXX-verify`, чтобы выполнить самопроверку (`automation/stageXX/self_check.sh`).
4. Просмотрите отчёт с помощью `make stageXX-report` — команда выведет содержимое `automation/stageXX/report.md`.

Сценарии не реализованных этапов выводят сообщение вида «Stage XX not implemented», поэтому их можно выполнять повторно без побочных эффектов. Для фиксации статуса и предупреждений можно обновлять `automation/stageXX/status.json`, а для наполнения отчётов — использовать шаблон `automation/templates/report.md`.
