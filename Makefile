COMPOSE=docker compose
STAGES := 01 02 03 04 05 06 07 08 09 10 11 12

.PHONY: up migrate test

up:
	$(COMPOSE) up -d --build

migrate:
	$(COMPOSE) exec backend alembic upgrade head

test:
	$(COMPOSE) exec backend pytest -q

define stage_template
.PHONY: stage$(1) stage$(1)-verify stage$(1)-report
stage$(1):
	./automation/stage$(1)/run.sh

stage$(1)-verify:
	./automation/stage$(1)/self_check.sh

stage$(1)-report:
	@cat automation/stage$(1)/report.md
endef

$(foreach stage,$(STAGES),$(eval $(call stage_template,$(stage))))
.PHONY: bootstrap-dev
bootstrap-dev:
	./scripts/bootstrap_dev.sh

