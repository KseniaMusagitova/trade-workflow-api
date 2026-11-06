# Trade Workflow API (learning project)

FastAPI application for fictional trading records, PostgreSQL persistence, validation, and a grouped notional report. This is a learning prototype, not a production trading platform.

## Run with Docker

```bash
docker compose up --build
```

Open http://localhost:8000/docs for interactive API documentation.

## Example

```bash
curl -X POST http://localhost:8000/trades -H 'Content-Type: application/json' -d '{"symbol":"AAPL","side":"BUY","quantity":10,"price":"187.50"}'
curl http://localhost:8000/reports/notional-by-symbol
```

## Local tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Tests use SQLite locally by default; Docker Compose runs PostgreSQL. The API is a starting point. Next milestones: update endpoint, Alembic migrations, PostgreSQL integration tests, authentication, logging, deployment to AWS. Do not expose the API publicly without authentication and secret management.
