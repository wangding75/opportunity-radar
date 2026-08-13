import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

# Tests exercise the real Alembic migration path before importing the application.
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
command.upgrade(config, "head")

import pytest  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield
