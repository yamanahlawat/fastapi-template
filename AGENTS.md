# AGENTS.md

Agent context and conventions for this FastAPI template.

---

## Project Structure

The backend follows a **domain-driven layout** inside `src/`. Each domain is a self-contained
package with its own router, service, CRUD, schemas, models, and dependencies.

```
src/
├── main.py                  # FastAPI app factory + router registration
├── api/
│   ├── router.py            # Aggregates all domain routers under /api
│   └── health.py            # Health check (no auth, no prefix)
├── core/
│   ├── config.py            # Settings via pydantic-settings
│   ├── constants.py         # Global enums (Environment, etc.)
│   └── redis.py             # Redis client singleton
├── database/
│   ├── base.py               # Metadata / import target for Alembic
│   ├── base_class.py         # Declarative Base with UUID PK + timestamps
│   ├── crud_base.py          # Generic CRUDBase[Model, Create, Update]
│   ├── session.py            # Async engine + sessionmaker
│   └── dependencies.py       # get_db_session() FastAPI dependency
└── <domain>/                 # e.g. auth/, and any new domain you add
    ├── router.py
    ├── service.py
    ├── models.py
    ├── schemas.py
    ├── dependencies.py
    ├── crud/
    │   ├── __init__.py
    │   └── <model>.py         # CRUD<Model>(CRUDBase[...]) + singleton crud_<model>
    └── <helpers>.py            # utils.py, naming.py, etc.
```

### Flat file vs. folder: how to decide

A domain concern (`schemas`, `service`, `dependencies`, ...) starts as a **single flat file**
(`schemas.py`). Only promote it to a **folder** (`schemas/` with an `__init__.py`) once that
concern genuinely needs multiple files — e.g. a domain with several distinct schema groups, or
a service split across more than one file. This is decided **per module, as it grows** — don't
pre-create folders for a concern that only has one file today just because another domain
elsewhere needed a folder.

`crud/` is the one concern that's conventionally a folder from the start once a domain has more
than one model worth its own CRUD file, since it's common to need one file per model
(`crud/user.py`, `crud/account.py`, ...).

The `auth` domain in this template currently has `services/` as a folder (it holds both
`auth.py` and `token_cache.py` — two files, so the folder is justified) and `schemas/` /
`dependencies/` as folders-of-one (only one file each). Don't take that as a strict template —
when you copy this template for a new project and a domain's `schemas`/`dependencies` never
grows past one file, flatten it; if it grows, keep it a folder.

### Layer responsibilities

**`router.py`** — HTTP boundary only.

- Declares `APIRouter(prefix=..., tags=[...])`.
- Injects `current_user` via `Depends(get_current_user)` on every protected endpoint.
- Injects the service via `Depends(get_<domain>_service)`.
- Injects `db: AsyncSession` via `Depends(get_db_session)` when persistence is needed.
- Translates Python exceptions to HTTP: domain-specific exceptions → their status code.
- Contains **no business logic** — delegates entirely to the service.

**`service.py`** — Business logic and orchestration.

- Plain class, no FastAPI coupling. Receives dependencies via `__init__` (e.g. `db`, clients).
- Calls CRUD singletons for DB work, external clients for I/O.
- Raises domain-specific exceptions for user-visible errors; never raises bare `HTTPException`.

```python
class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def login(self, email: str, password: str) -> TokenSchema:
        ...
```

**`crud/<model>.py`** — Database access only.

- Subclass of `CRUDBase[Model, CreateSchema, UpdateSchema]` from `src/database/crud_base.py`.
- Adds domain-specific queries (e.g. `get_by_email`).
- Exports a **module-level singleton** (`crud_user = CRUDUser(User)`) — never instantiate CRUD
  classes elsewhere.
- All methods are `async`, receive `db: AsyncSession` as first positional argument, keyword-only
  after.

**`dependencies.py`** — FastAPI dependency factories.

- Thin functions that wire together service + clients. No business logic; purely construction.

**`schemas.py`** — Pydantic I/O contracts.

- Request bodies, response shapes, internal transfer objects. No SQLAlchemy imports — pure
  Pydantic.

**`models.py`** — SQLAlchemy ORM models.

- Inherit from `TimeStampedBase` (UUID PK, `created_at`, `updated_at` auto-managed). No
  Pydantic here; no business logic.

**`<helpers>.py`** (utils, etc.) — Pure functions.

- No FastAPI, no SQLAlchemy. Stateless transformations, parsing, formatting.

### Why this layout

- **Router stays thin**: exception translation is the only layer concern; swapping HTTP for
  gRPC/CLI requires touching only the router.
- **Service is testable without HTTP**: inject mocked clients/db, no test client setup needed.
- **CRUD singletons prevent proliferation**: one `crud_<model>` per model, used everywhere.
- **Helpers are pure**: independently testable, zero side-effects.

---

## Writing Tests

Tests live in `tests/<domain>/test_<module>.py`, mirroring `src/`.

### Framework and configuration

- **pytest** with `asyncio_mode = "auto"` (all async tests run without explicit
  `@pytest.mark.asyncio`).
- **No real database or network**: all DB sessions and external clients are
  `AsyncMock`/`MagicMock`.
- Tests are **unit tests by default**.
- Test env vars are loaded from `.env.test` via the `pytest-env` plugin
  (`[tool.pytest_env] env_files = [".env.test"]` in `pyproject.toml`), so `.env.test` is the
  single source of test configuration — no separate conftest loading logic needed. This runs
  before any app code (and therefore `src.core.config.settings`) is imported.

### File structure

```python
# tests/auth/test_auth_service.py

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.services.auth import AuthService


class TestAuthenticateUser:
    """Tests for AuthService.authenticate_user()."""

    async def test_valid_credentials_returns_user(self, mock_db):
        with patch("src.auth.services.auth.crud_user") as mock_crud_user:
            mock_crud_user.get_by_email = AsyncMock(return_value=some_user)
            service = AuthService(db=mock_db)
            result = await service.authenticate_user(email="a@b.com", password="pw")

        assert result is some_user
```

### Conventions

1. **Group by method under test**: one class per public method (`TestAuthenticateUser`,
   `TestLogin`).
2. **Descriptive test names**: `test_<scenario>_<expected_outcome>` — e.g.
   `test_wrong_password_raises_invalid_credentials`.
3. **Fixture placement**: shared fixtures (e.g. `mock_db`) live in `tests/conftest.py`
   (global). Domain-specific shared fixtures go in `tests/<domain>/conftest.py`. Test-specific
   fixtures stay in the test file, inside the class that uses them. Only add a shared fixture
   once a test actually uses it — don't pre-create fixtures speculatively.
4. **Mock at the boundary**: mock external clients and DB sessions. Patch module-level imports
   with `patch("src.<domain>.<module>.<symbol>")`.
5. **Assert on behavior, not internals**: check return values and raised exceptions; avoid
   asserting on internal state.
6. **Raise assertions**: use `pytest.raises(SomeException, match="...")` to verify error
   messages, not just exception type.
7. **No `@pytest.mark.asyncio`**: `asyncio_mode = "auto"` handles it — async test methods work
   directly.

```python
# Patching a module-level import
with patch("src.auth.services.auth.TokenCacheService") as mock_token_cache_cls:
    mock_token_cache_cls.return_value.store_refresh_token = AsyncMock(return_value=True)
    tokens = await service.create_session_tokens(user=user)

# Asserting exceptions
with pytest.raises(InvalidCredentialsException, match="Invalid email or password"):
    await service.authenticate_user(email="nobody@example.com", password="anything")
```

### Running tests

```bash
uv sync --group dev
uv run pytest
uv run pytest --cov --cov-report=term-missing
```

No `.env`/`.env` copying needed to run tests — `pytest-env` loads `.env.test` automatically. You
only need `cp .env.test .env` when running the app or other tooling (e.g. `alembic`) outside
of pytest against test-like settings.

---

## Tooling: uv & ruff

This template is opinionated about its tooling. Don't swap these out or work around them —
follow the conventions below.

### Package management (uv)

- **Never hand-edit dependency arrays.** Use `uv add <package>` for runtime dependencies and
  `uv add --group dev <package>` for anything only needed for lint/test/tooling. This keeps
  `uv.lock` in sync with `pyproject.toml` automatically — a manually edited `pyproject.toml`
  with a stale `uv.lock` is a common source of "works on my machine" bugs.
- **Two dependency buckets, kept honest:**
  - `[project.dependencies]` — only what the running app imports in `src/`.
  - `[dependency-groups] dev` — pytest, ruff, pre-commit, ipdb, tomli-w, etc. Nothing here
    should ever be imported by `src/`.
  - When you remove a dependency, remove it from the right bucket and re-run `uv sync` (or
    `uv lock`) so the lockfile drops it and its now-unused transitive packages. Don't leave
    dead entries around "just in case" — that's exactly what got cleaned out of this template
    (`logfire`, `pydantic-ai-slim`, an unused `pytest-env` dependency) after it diverged from
    actual usage.
- **Run everything through `uv run`** (`uv run pytest`, `uv run ruff check .`,
  `uv run alembic ...`, `uv run fastapi dev src/main.py`) instead of activating the venv by
  hand. It guarantees you're using the locked, resolved environment, not whatever happens to
  be on `PATH`.
- **`uv sync --group dev`** for local development and CI (needs the test/lint tooling).
  **`uv sync`** (no group) for anything building a runtime artifact (e.g. the Docker image) —
  it should never need pytest/ruff/ipdb installed.
- **Version floors, not pins.** Dependencies are declared as `>=x.y.z` in `pyproject.toml`;
  `uv.lock` is what pins exact resolved versions. Don't add `==` pins in `pyproject.toml`
  unless there's a specific, documented compatibility reason — that defeats the point of
  having a lockfile.
- **Commit `uv.lock`** alongside every `pyproject.toml` change. It's the reproducibility
  guarantee for CI and every other contributor — never gitignore it.
- **`.python-version` pins the interpreter** (currently `3.14`) that `uv run`/`uv sync` use.
  Bump it deliberately (and update `ruff.toml`'s `target-version` to match) — not as a side
  effect of some other change.

### Linting & formatting (ruff)

- **Config lives in `ruff.toml`**, not `[tool.ruff]` in `pyproject.toml` — keep it there for a
  clean separation between project metadata and lint/format config.
- **The rule selection is deliberate**, not "turn everything on":
  `["E", "W", "F", "I", "B", "UP", "SIM", "C4", "RET", "ASYNC", "RUF"]` — pyflakes/pycodestyle
  correctness, import sorting, bugbear footguns, pyupgrade (keep syntax modern for the pinned
  Python version), simplify, comprehensions, return-statement clarity, async-specific checks,
  and ruff's own rules. If a new rule category seems worth adding, check it doesn't fight an
  existing domain convention first (e.g. some `SIM`/`RET` rules can clash with early-return-
  heavy router code) — prefer a targeted `per-file-ignores` entry over disabling a whole
  category, and prefer disabling a whole category over turning off enforcement entirely.
- **`lint.fixable = ["ALL"]`**: it's expected that `ruff check --fix .` is always safe to run.
  If a future rule genuinely shouldn't be auto-fixed, add it to `lint.unfixable` explicitly
  rather than leaving fixable at `ALL` and hoping nobody runs `--fix`.
- **`migrations/versions/*.py` are exempt** (`E501, RUF, UP, I`) because Alembic autogenerates
  them. Don't hand-fix lint issues in a generated migration — regenerate it, or add the
  specific new exemption if Alembic's output style changes.
- **Format settings**: double quotes, LF line endings, 120-column width. Configure your editor
  to match rather than fighting the formatter — if `ruff format` and a manual edit disagree,
  the formatter wins; don't hand-format code the tool would otherwise reformat.
- **Lint and format are enforced identically** in pre-commit and in CI
  (`ruff check .` / `ruff format --check .` are the exact commands both run). A change that
  passes locally without running pre-commit should still pass CI, since they share the same
  `ruff.toml`. Run `uv run ruff check --fix .` and `uv run ruff format .` before committing if
  you haven't got the pre-commit hook installed.
