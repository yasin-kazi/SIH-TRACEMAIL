"""Test database isolation for the standard-library unittest suite.

The SQLAlchemy engine resolves a relative sqlite path at *engine creation*
(not at connect time), so the old "chdir into a temp dir before importing
main" trick does not isolate ``backend/tracemail.db``. Both integration test
modules instead point the whole test process at a single fresh, process-local
database file and read it directly.

Because every test module computes the same per-process path before importing
the app, ``python -m unittest discover`` stays consistent no matter which
module imports ``database`` first.
"""
import os
import tempfile
import uuid
from pathlib import Path

_UNIQUE = uuid.uuid4().hex[:8]
DB_NAME = f"tracemail_test_{_UNIQUE}.db"


def test_db_path() -> Path:
    return Path(tempfile.gettempdir()) / DB_NAME


def test_db_uri() -> str:
    return f"sqlite+aiosqlite:///{test_db_path().as_posix()}"


def set_test_database_env() -> None:
    os.environ["TRACEMAIL_DATABASE_URL"] = test_db_uri()


def teardown_database() -> None:
    """Best-effort dispose of pooled connections and remove the test file."""
    import asyncio

    from database import engine

    asyncio.run(engine.dispose())
    try:
        test_db_path().unlink()
    except OSError:
        pass