COMPOSE=docker compose

.PHONY: up migrate test

up:
	$(COMPOSE) up -d --build

migrate:
	$(COMPOSE) exec backend alembic upgrade head

test:
	$(COMPOSE) exec backend pytest -q
