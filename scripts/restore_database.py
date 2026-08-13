from __future__ import annotations

import argparse
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import settings
from app.core.postgres_cli import postgres_cli_connection, postgres_cli_server_args

_DB_NAME = re.compile(r"^[A-Za-z0-9_]+$")
EXPECTED_SCHEMA_REVISION = "0030_probe_task_leases"


def restore_sqlite(backup: Path, database_url: str) -> None:
    prefix = "sqlite:///"
    target = Path(database_url[len(prefix):]).expanduser().resolve()
    check = sqlite3.connect(str(backup))
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"backup integrity check failed: {result}")
    finally:
        check.close()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".restore.tmp")
    shutil.copy2(backup, tmp)
    tmp.replace(target)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} is required for PostgreSQL restore")
    return path


def _database_name(database_url: str) -> str:
    name = make_url(database_url).database or ""
    if not _DB_NAME.fullmatch(name):
        raise ValueError("PostgreSQL database name must contain only letters, digits and underscore for staged restore")
    return name


def _derived_database_name(target: str, label: str, stamp: str) -> str:
    """Build a generated PostgreSQL identifier without exceeding NAMEDATALEN.

    PostgreSQL database identifiers are limited to 63 bytes in normal builds. Keep
    enough target context for operators while reserving a suffix for timestamp and
    entropy so a long production database name cannot make staged restore fail.
    """
    suffix = f"_{label}_{stamp}_{secrets.token_hex(3)}"
    max_prefix = 63 - len(suffix)
    if max_prefix < 1:
        raise RuntimeError("generated restore database suffix is too long")
    return f"{target[:max_prefix]}{suffix}"


def _run_psql_scalar(psql: str, database_url: str, database: str, sql: str) -> str:
    args, env = postgres_cli_connection(database_url, database_override=database)
    result = subprocess.run(
        [psql, *args, "--no-psqlrc", "--tuples-only", "--no-align", "--set", "ON_ERROR_STOP=1", "--command", sql],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_staged_postgres(psql: str, database_url: str, staging_name: str) -> None:
    revision = _run_psql_scalar(psql, database_url, staging_name, "SELECT version_num FROM alembic_version LIMIT 1;")
    if revision != EXPECTED_SCHEMA_REVISION:
        raise RuntimeError(f"staged restore schema mismatch: expected {EXPECTED_SCHEMA_REVISION}, got {revision or '<missing>'}")
    required = _run_psql_scalar(
        psql,
        database_url,
        staging_name,
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('raw_observations','opportunities','users','opportunity_score_snapshots');",
    )
    if required != "4":
        raise RuntimeError(f"staged restore missing required tables: count={required or '<missing>'}")


def restore_postgres_staged(backup: Path, database_url: str, *, promote: bool = False) -> str:
    pg_restore = _tool("pg_restore")
    createdb = _tool("createdb")
    dropdb = _tool("dropdb")
    psql = _tool("psql")
    target = _database_name(database_url)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    staging = _derived_database_name(target, "restore", stamp)
    previous = _derived_database_name(target, "previous", stamp)

    # Archive preflight occurs before creating or modifying any database.
    _, env = postgres_cli_connection(database_url)
    subprocess.run([pg_restore, "--list", str(backup)], check=True, env=env, stdout=subprocess.DEVNULL)

    maintenance_args, env = postgres_cli_connection(database_url, database_override="postgres")
    server_args, _ = postgres_cli_server_args(database_url)
    subprocess.run([createdb, *server_args, staging], check=True, env=env)
    try:
        staging_args, env = postgres_cli_connection(database_url, database_override=staging)
        subprocess.run([pg_restore, *staging_args, "--no-owner", "--exit-on-error", str(backup)], check=True, env=env)
        validate_staged_postgres(psql, database_url, staging)
        if not promote:
            return staging

        # Promotion is explicit. The original database is renamed, not dropped, so
        # rollback is available after cutover. Identifiers are generated/validated.
        if not _DB_NAME.fullmatch(previous):
            raise RuntimeError("generated previous database name is unsafe")
        sql = (
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{target}' AND pid <> pg_backend_pid(); "
            f'ALTER DATABASE "{target}" RENAME TO "{previous}"; '
            f'ALTER DATABASE "{staging}" RENAME TO "{target}";'
        )
        subprocess.run(
            [psql, *maintenance_args, "--no-psqlrc", "--set", "ON_ERROR_STOP=1", "--command", sql],
            check=True,
            env=env,
        )
        return previous
    except Exception:
        # A failed staging restore must never touch the target. Clean up only the
        # staging database we created.
        subprocess.run(
            [dropdb, *server_args, "--if-exists", staging],
            check=False,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raise


def restore_postgres_in_place(backup: Path, database_url: str) -> None:
    pg_restore = _tool("pg_restore")
    connection_args, env = postgres_cli_connection(database_url)
    subprocess.run([pg_restore, "--list", str(backup)], check=True, env=env, stdout=subprocess.DEVNULL)
    subprocess.run([pg_restore, *connection_args, "--clean", "--if-exists", "--no-owner", "--exit-on-error", str(backup)], check=True, env=env)



def restore_postgres(backup: Path, database_url: str) -> None:
    """Backward-compatible explicit in-place restore helper.

    The CLI defaults to staged PostgreSQL restore; only direct callers retain the
    historic preflight + in-place behavior through this compatibility function.
    """
    restore_postgres_in_place(backup, database_url)

def main() -> int:
    parser = argparse.ArgumentParser(description="Restore Opportunity Radar database from backup")
    parser.add_argument("backup")
    parser.add_argument("--confirm-restore", action="store_true", help="required because restore changes database state")
    parser.add_argument("--promote-staging", action="store_true", help="PostgreSQL only: atomically rename validated staging database into service")
    parser.add_argument("--unsafe-in-place", action="store_true", help="PostgreSQL only: legacy destructive restore directly into target")
    args = parser.parse_args()
    if not args.confirm_restore:
        raise SystemExit("restore blocked: pass --confirm-restore")
    if args.promote_staging and args.unsafe_in_place:
        raise SystemExit("choose either --promote-staging or --unsafe-in-place")
    backup = Path(args.backup).resolve()
    if not backup.exists():
        raise FileNotFoundError(backup)
    if settings.database_url.startswith("sqlite:///"):
        restore_sqlite(backup, settings.database_url)
        print("RESTORE_PASS")
    elif settings.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        if args.unsafe_in_place:
            restore_postgres_in_place(backup, settings.database_url)
            print("RESTORE_PASS_UNSAFE_IN_PLACE")
        else:
            result = restore_postgres_staged(backup, settings.database_url, promote=args.promote_staging)
            if args.promote_staging:
                print(f"RESTORE_PROMOTED_PREVIOUS_DATABASE={result}")
            else:
                print(f"RESTORE_STAGING_VALIDATED={result}")
    else:
        raise RuntimeError("unsupported DATABASE_URL for restore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
