# Product Card AI

Агентная система для генерации карточек товаров.

## Технологии

- Python 3.12
- FastAPI
- SQLAlchemy + asyncpg
- PostgreSQL 16 + pgvector
- Docker Compose
- OpenAI Agents SDK
- uv

## Установка

Клонировать репозиторий:

```bash
git clone https://github.com/BuilovAlmaty/product-card-ai.git
cd product-card-ai
```

Установить зависимости:

```bash
uv sync --locked
```

Создать файл конфигурации:

```bash
cp .env.example .env
```

В файле `.env` указать:

```dotenv
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5433/app
```

## Запуск PostgreSQL

```bash
docker compose up -d
```

Активировать pgvector:

```bash
docker compose exec db psql -U app -d app -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Запуск приложения

```bash
uv run uvicorn app.main:app --reload
```

Документация API:

http://127.0.0.1:8000/docs

## Проверки состояния

- GET /health/live — проверка работы приложения.
- GET /health/ready — проверка подключения к PostgreSQL.

## Тестирование

```bash
uv run python -m pytest -v
```

## Проверка кода

```bash
uv run ruff check .
```

## Остановка PostgreSQL

```bash
docker compose down
```