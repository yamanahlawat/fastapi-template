# FastAPI Template

A production-ready FastAPI template with JWT authentication, async PostgreSQL, Redis caching, and Docker support.

## Features

- **FastAPI** with async/await throughout
- **JWT Authentication** -- access + refresh token pattern with token blacklisting
- **Password Hashing** -- Argon2id (OWASP recommended)
- **PostgreSQL** -- async via SQLAlchemy 2.0 + psycopg3
- **Redis** -- refresh token storage, access token blacklist, session management
- **Alembic** -- async database migrations
- **Docker Compose** -- app, PostgreSQL, and Redis
- **Ruff** -- linting and formatting with pre-commit hooks
- **Pytest** -- unit tests with mocked DB/Redis, coverage reporting
- **CI** -- lint, spell-check, and test jobs on every push/PR via GitHub Actions

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL |
| Cache | Redis |
| Migrations | Alembic |
| Auth | PyJWT + Argon2 |
| Settings | Pydantic Settings |
| Logging | Loguru |
| Testing | Pytest + pytest-cov |
| Package Manager | uv |
| Python | 3.14+ |

## Project Structure

```
src/
├── main.py                  # App entry point, router wiring, CORS
├── api/
│   ├── health.py            # Health check endpoint
│   └── router.py            # Protected API routes (extend here)
├── auth/
│   ├── models.py            # User SQLAlchemy model
│   ├── router.py            # Auth endpoints (login, logout, refresh, me)
│   ├── utils.py             # JWT creation/verification, password hashing
│   ├── exceptions.py        # Auth-specific exceptions
│   ├── crud/user.py         # User database operations
│   ├── dependencies/auth.py # FastAPI dependencies (get_current_user, etc.)
│   ├── schemas/user.py      # Pydantic request/response schemas
│   └── services/
│       ├── auth.py          # Auth business logic
│       └── token_cache.py   # Redis token management
├── core/
│   ├── config.py            # App settings (env-based)
│   ├── constants.py         # Enums
│   └── redis.py             # Async Redis client
└── database/
    ├── base.py              # Model registry for Alembic
    ├── base_class.py        # Base model classes (UUID pk, timestamps)
    ├── crud_base.py         # Generic CRUD operations
    ├── dependencies.py      # DB session dependency
    └── session.py           # Async engine + session factory
```

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd fastapi-template
   ```

2. Copy the environment file and configure it:
   ```bash
   cp .env.example .env
   ```

3. Start the services:
   ```bash
   docker compose up -d
   ```

4. Install dependencies:
   ```bash
   uv sync --group dev
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the dev server:
   ```bash
   fastapi dev src/main.py
   ```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health/` | No | Health check |
| `POST` | `/api/auth/token` | No | Login (email + password) |
| `GET` | `/api/auth/users/me` | Yes | Get current user |
| `POST` | `/api/auth/logout` | Yes | Logout (blacklist token) |
| `POST` | `/api/auth/refresh` | No | Refresh access token |

## Configuration

Configuration is managed via environment variables. Nested settings use `__` as delimiter.

```env
ENVIRONMENT=local

POSTGRES__HOST=db
POSTGRES__USER=fastapi
POSTGRES__PASSWORD=fastapi
POSTGRES__DB=fastapi
POSTGRES__PORT=5432

REDIS__HOST=redis
REDIS__PORT=6379
REDIS__DB=0

JWT_SECRET_KEY=your_secret_key
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Testing

Tests are unit tests only -- no real Postgres/Redis required, everything is mocked.

```bash
# Install test/lint tooling
uv sync --group dev

# Run the test suite
uv run pytest

# With coverage
uv run pytest --cov --cov-report=term-missing
```

Test configuration lives in `.env.test` and is loaded automatically by the `pytest-env` plugin
(see `[tool.pytest_env]` in `pyproject.toml`) -- no manual `.env` setup needed to run tests.

See [`AGENTS.md`](./AGENTS.md) for the project's testing conventions (fixture placement, mocking
style, naming) and layered architecture (`router` / `service` / `crud` / `schemas`).

## Linting

```bash
# Check
ruff check src/

# Fix
ruff check --fix src/

# Format
ruff format src/
```

## Type Checking

```bash
uvx ty check src/
```

## Continuous Integration

Every push and pull request to `main`/`development` runs three GitHub Actions jobs
(`.github/workflows/ci.yml`): lint (`ruff check` + `ruff format --check`), spell-check
(`codespell`), and test (`pytest --cov`, with the coverage report uploaded as a build artifact).

## License

MIT
