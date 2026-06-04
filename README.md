# Autonomous Research Agent

Production-oriented autonomous research backend built with FastAPI, LangGraph, LangChain, vector search, PostgreSQL, Redis, Celery, Playwright, Prometheus, and Grafana.

## What V2 Implements

- Auth APIs with JWT, bcrypt password hashing, and role hooks.
- Research APIs for starting, listing, inspecting, monitoring, and deleting research jobs.
- LangGraph workflow: query decomposition, web search, browser navigation, indexing, semantic retrieval, reasoning, validation, and report generation.
- LangChain LLM synthesis path when `OPENAI_API_KEY` is configured, with deterministic fallback for local tests.
- Vector search abstraction with Chroma, FAISS, and in-memory fallback.
- PostgreSQL schema with Alembic migration for users, research queries, tasks, sources, reports, and metrics.
- Redis-backed rate limiting, Pub/Sub execution updates, and Celery broker integration.
- Playwright-based page navigation and BeautifulSoup extraction.
- Prometheus metrics and Grafana provisioning.
- Docker Compose for backend, worker, PostgreSQL, Redis, Prometheus, and Grafana.

## Local Setup

```bash
cp .env.example .env
docker-compose up --build
```

Services:

- FastAPI: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Run Locally Without Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

The default local database is SQLite. Set `DATABASE_URL` to PostgreSQL for production parity.

## API Flow

1. `POST /api/v1/auth/register`
2. `POST /api/v1/auth/login`
3. `POST /api/v1/research/start`
4. `GET /api/v1/research/status/{query_id}`
5. `GET /api/v1/research/{query_id}`

## Worker Mode

Set `USE_CELERY=true` and run:

```bash
celery -A app.tasks.celery_app worker --loglevel=INFO -Q research
```

When `USE_CELERY=false`, FastAPI background tasks execute research jobs.

## Tests

```bash
pytest
ruff check .
```

## Benchmarking

The 60% efficiency improvement claim is not asserted by this repository until benchmark data exists. See `docs/BENCHMARKING.md`.

```bash
python benchmarks/retrieval_benchmark.py --iterations 50
```

## Production Notes

- Replace `SECRET_KEY`.
- Use managed PostgreSQL and Redis.
- Set `AUTO_CREATE_TABLES=false` and run Alembic migrations.
- Enable Celery workers for long-running research.
- Add authenticated access or network-level protection for `/api/v1/monitoring/metrics` in production.
- Add browser e2e tests against known fixture pages before claiming dynamic-site coverage.

