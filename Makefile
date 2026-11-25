.DEFAULT_GOAL := help

API_PORT ?= 8000
POSTGRES_SERVICE ?= db
RABBITMQ_SERVICE ?= rabbitmq

LMS ?= $(HOME)/.lmstudio/bin/lms
MODEL_ID ?= google/gemma-4-e4b
MODEL_PORT ?= 1234
MODEL_GPU ?= off
MODEL_CONTEXT ?= 2048

.PHONY: help dev api infra postgres rabbitmq infra-stop docker-status \
        model model-status lint format test check health worker

help:
	@printf '%s\n' \
		'make dev           PostgreSQL, RabbitMQ, Gemma и FastAPI' \
		'make api           FastAPI с автоперезапуском' \
		'make infra         PostgreSQL и RabbitMQ' \
		'make postgres      Только PostgreSQL' \
		'make rabbitmq      Только RabbitMQ' \
		'make docker-status Статус контейнеров' \
		'make infra-stop    Остановить PostgreSQL и RabbitMQ' \
		'make model         Загрузить Gemma и запустить её HTTP API' \
		'make model-status  Порт API модели и загруженные модели' \
		'make health        Проверить /health/live и /health/ready' \
		'make lint          Проверить код через Ruff' \
		'make format        Отформатировать код через Ruff' \
		'make test          Запустить pytest' \
		'make check         Запустить линтер и тесты'

dev: infra model api

api:
	uv run fastapi dev app/main.py --port "$(API_PORT)"

infra:
	docker compose up -d "$(POSTGRES_SERVICE)" "$(RABBITMQ_SERVICE)"

postgres:
	docker compose up -d "$(POSTGRES_SERVICE)"

rabbitmq:
	docker compose up -d "$(RABBITMQ_SERVICE)"

docker-status:
	docker compose ps

infra-stop:
	docker compose stop "$(POSTGRES_SERVICE)" "$(RABBITMQ_SERVICE)"

model:
	@models=$$("$(LMS)" ps) || exit $$?; \
	if printf '%s\n' "$$models" | awk -v model="$(MODEL_ID)" \
		'$$1 == model || ($$1 == "Identifier:" && $$2 == model) { found = 1 } END { exit !found }'; then \
		printf 'Модель %s уже загружена\n' "$(MODEL_ID)"; \
	else \
		"$(LMS)" load "$(MODEL_ID)" --gpu "$(MODEL_GPU)" --context-length "$(MODEL_CONTEXT)"; \
	fi
	"$(LMS)" server start --bind 127.0.0.1 --port "$(MODEL_PORT)"

model-status:
	"$(LMS)" server status
	"$(LMS)" ps

health:
	curl -fsS "http://127.0.0.1:$(API_PORT)/health/live"
	@printf '\n'
	curl -fsS "http://127.0.0.1:$(API_PORT)/health/ready"
	@printf '\n'

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest -q

check: lint test

worker:
	uv run celery -A app.workers.celery_app:celery_app worker \
		--hostname=card-worker@%h \
		-Q card.generate,card.critique \
		--concurrency=1 \
		-l info