from __future__ import annotations
import os, sys
from pathlib import Path
from logging.config import fileConfig
from typing import Any, Mapping
from alembic import context
from sqlalchemy import engine_from_config, pool

# Make 'app' importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import Base and then load models (this fills Base.metadata)
from app.db.base import Base
import app.models  # <-- triggers the imports in app/models/__init__.py

config = context.config
if config.config_file_name:
    try:
        fileConfig(config.config_file_name, disable_existing_loggers=False)
    except KeyError:
        pass

DB_URL = os.environ["SQLALCHEMY_DATABASE_URI"]
target_metadata = Base.metadata

COMPARE_KWARGS: Mapping[str, Any] = {
    "compare_type": True,
    "compare_server_default": True,
}

def run_migrations_offline() -> None:
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **COMPARE_KWARGS,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = DB_URL
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, **COMPARE_KWARGS)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
