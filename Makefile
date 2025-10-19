DOCKER_COMPOSE ?= docker compose -f docker-compose.dev.yml
ENV_FILE ?= .env
PHINX_ENV ?= development

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export $(shell sed -n 's/^[[:space:]]*\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' $(ENV_FILE))
endif

.PHONY: setup up down logs sh migrate seed

setup:
	@cp -n .env.example .env 2>/dev/null || true
	$(DOCKER_COMPOSE) up -d --build
	composer install
	vendor/bin/phinx migrate -e $(PHINX_ENV)
	vendor/bin/phinx seed:run -e $(PHINX_ENV)

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

sh:
	$(DOCKER_COMPOSE) exec -it web sh

migrate:
	vendor/bin/phinx migrate -e $(PHINX_ENV)

seed:
	vendor/bin/phinx seed:run -e $(PHINX_ENV)
