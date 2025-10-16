# Fashion Store API (FastAPI + Postgres + Alembic)

A production-style setup that runs Postgres, applies Alembic migrations as a **one-shot job**, then starts the API. Includes optional pgAdmin.

## Prerequisites

- Docker & Docker Compose v2
- (Optional) Python 3.12+ if you want to run local scripts

## Services

- `db` — Postgres 16
- `migrate` — one-shot Alembic upgrade (gates API start)
- `api` — FastAPI (Uvicorn)
- `pgadmin` — DB UI (optional)

> Migrations run separately from app startup. This is the safest, “best practice” pattern.

---

## Environment

Set in `docker-compose.yml` (or a `.env` file in the project root):

```yaml
# Required
SQLALCHEMY_DATABASE_URI: "postgresql+psycopg://appuser:apppass@db:5432/appdb"

# API routing (normalized to always start with '/')
API_PREFIX: "/api"
API_VERSION: "v1"

# CORS
# - Use "*" (no credentials)
# - Or JSON array / CSV of allowed origins
CORS_ORIGINS: "*"
# CORS_ORIGINS: '["http://localhost:5173","http://localhost:3000"]'
# CORS_ORIGINS: http://localhost:5173,http://localhost:3000
```

> In `app/core/config.py`, we parse `CORS_ORIGINS` (JSON, CSV, or `*`) and normalize `API_PREFIX`/`API_VERSION`.

---

## First-time setup

> Only needed once per fresh repo/DB.

1) **Build images**
```bash
docker compose build --no-cache
```

2) **Initialize Alembic structure**
```bash
docker compose run --rm --no-deps api alembic init migrations
```

3) **Wire Alembic**
- `alembic.ini` → keep `sqlalchemy.url` **empty** (we read from env).
- `migrations/env.py` → import **your** `Base` and **all** models so `Base.metadata` is populated, and read `SQLALCHEMY_DATABASE_URI` from env.
  - Sanity check:
    ```bash
    docker compose run --rm --no-deps api sh -lc '
    python - <<PY
    from app.db.base import Base
    import app.models  # ensures all model modules are imported
    print("tables:", list(Base.metadata.tables.keys()))
    PY'
    ```
    You should see your table names, not `[]`.

4) **Create the initial migration from models**
```bash
docker compose run --rm --no-deps api alembic revision --autogenerate -m "init schema"
```

5) **Apply migrations (one-shot job)**
```bash
docker compose run --rm migrate
```

6) **Start the API**
```bash
docker compose up -d api
```

Open **http://localhost:8000/docs**

---

## Daily dev workflow

After you change models:

```bash
# generate new migration
docker compose run --rm --no-deps api alembic revision --autogenerate -m "change xyz"

# apply it
docker compose run --rm migrate

# (re)start api if needed
docker compose up -d api
```

Follow logs:
```bash
docker compose logs -f migrate
docker compose logs -f api
```

---

## pgAdmin (optional)

Add the `pgadmin` service in `docker-compose.yml` (if not already present), then:

```bash
docker compose up -d pgadmin
```

Open **http://localhost:8081**

Create a server:
- **Name:** Local Postgres (anything)
- **Host:** `db`
- **Port:** `5432`
- **Database:** `appdb`
- **Username:** `appuser`
- **Password:** `apppass`

Tables: `Servers → Local Postgres → Databases → appdb → Schemas → public → Tables`

---

## Useful commands

**Bring everything up (db → migrate → api)**
```bash
docker compose up -d
```

**Current DB revision**
```bash
docker compose run --rm --no-deps api alembic current
```

**List public tables**
```bash
docker compose exec db psql -U appuser -d appdb -c "\dt public.*"
```

**alembic_version row**
```bash
docker compose exec db psql -U appuser -d appdb -c "SELECT * FROM alembic_version;"
```

**One-off shell in the API image**
```bash
docker compose run --rm --no-deps api sh
```

**Rebuild after dependency changes**
```bash
docker compose build --no-cache
```

**Tear down**
```bash
docker compose down
# DANGER: also deletes Postgres data volume
# docker compose down -v
```

---

## Troubleshooting

**`service "migrate" didn't complete successfully: exit 127`**
- Your image doesn’t have `bash` or `alembic`. We run with `sh -lc` in compose, and Dockerfile must install:
  ```bash
  pip install "alembic>=1.13" "SQLAlchemy>=2" "psycopg[binary]>=3" "uvicorn[standard]"
  ```
- Rebuild: `docker compose build --no-cache`

**`KeyError: 'formatters'` from Alembic**
- Your `alembic.ini` is missing logging sections. Use the standard template (with `[loggers]`, `[handlers]`, `[formatters]`) or wrap `fileConfig(...)` in a try/except in `env.py`.

**Autogenerate creates empty migration**
- `migrations/env.py` isn’t importing your models → `Base.metadata` is empty.
- Ensure `import app.models` (and that `app/models/__init__.py` imports all submodules or dynamically loads them).

**Pydantic “schema for unknown type … InventoryMovement”**
- Never use ORM classes in `response_model` or Pydantic fields. Create DTOs (e.g., `InventoryMovementOut`) with `model_config = ConfigDict(from_attributes=True)` and use them in routes and `Page[T]`.

**CORS**
- Want wildcard? Set `CORS_ORIGINS: "*"` (allows all origins **without credentials**).
- Need credentials from any origin? Use `allow_origin_regex=".*"` in `main.py` (risky; dev only).

**FastAPI `AssertionError: A path prefix must start with '/'`**
- Set `API_PREFIX: "/api"` (with a leading slash), and normalize in code if needed.

---

## Notes on volumes & naming

To keep your DB data when changing the Compose project name, pin the volume:

```yaml
volumes:
  pg_data:
    name: pg_data
```

(Optional) pin network:
```yaml
networks:
  app-net:
    name: app-net
```

---

## Structure (abridged)

```
backend/
├─ app/
│  ├─ main.py
│  ├─ core/config.py
│  ├─ db/base.py
│  ├─ models/          # ORM models (SQLAlchemy)
│  └─ schemas/         # Pydantic DTOs (response/request)
├─ migrations/         # Alembic env + versions
├─ docker-compose.yml
└─ requirements.txt
```

---

## Quick start (TL;DR)

```bash
docker compose build --no-cache
docker compose run --rm --no-deps api alembic init migrations
# edit migrations/env.py (import Base + models, read DSN from env)
docker compose run --rm --no-deps api alembic revision --autogenerate -m "init schema"
docker compose run --rm migrate
docker compose up -d
# http://localhost:8000/docs   |   http://localhost:8081 (pgAdmin)
```
