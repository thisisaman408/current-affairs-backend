"""
Alembic Environment Configuration
Loads models and database URL from config.py
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import settings
from src.database.base import Base

# Import all models (needed for autogenerate)
from src.models import (
    PDFJob,
    Question,
    User,
    UserPreferences,
    DeviceToken,
    DeliveryLog
)

# Alembic Config object
config = context.config

# Set database URL from settings
db_url = settings.DATABASE_URL
if db_url is None:
    raise RuntimeError("DATABASE_URL is not configured in settings.DATABASE_URL")
config.set_main_option('sqlalchemy.url', db_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    cfg_section = config.get_section(config.config_ini_section)
    if cfg_section is None:
        raise RuntimeError(f"Alembic config section '{config.config_ini_section}' is missing")
    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
