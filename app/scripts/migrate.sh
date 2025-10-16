#!/usr/bin/env bash
set -e
python - <<'PY'
import os, time
from sqlalchemy import create_engine, text
dsn = os.environ["SQLALCHEMY_DATABASE_URI"]
eng = create_engine(dsn, pool_pre_ping=True)
for i in range(60):
    try:
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("DB not ready after 60s")
PY
alembic upgrade head
