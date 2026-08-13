from __future__ import annotations

import argparse
import sys
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import settings
from app.core.postgres_cli import postgres_cli_connection


def backup_sqlite(database_url: str, output: Path) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("not a sqlite URL")
    source = Path(database_url[len(prefix):]).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    src = sqlite3.connect(str(source))
    dst = sqlite3.connect(str(tmp))
    try:
        src.backup(dst)
        result = dst.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"backup integrity check failed: {result}")
        dst.close()
        src.close()
        tmp.replace(output)
    except Exception:
        dst.close()
        src.close()
        tmp.unlink(missing_ok=True)
        raise
    return output


def backup_postgres(database_url: str, output: Path) -> Path:
    pg_dump = shutil.which("pg_dump")
    pg_restore = shutil.which("pg_restore")
    if not pg_dump or not pg_restore:
        raise RuntimeError("pg_dump and pg_restore are required for PostgreSQL backups")
    output.parent.mkdir(parents=True, exist_ok=True)
    connection_args, env = postgres_cli_connection(database_url)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    try:
        subprocess.run(
            [pg_dump, *connection_args, "--format=custom", "--no-owner", "--file", str(tmp)],
            check=True,
            env=env,
        )
        if not tmp.exists() or tmp.stat().st_size == 0:
            raise RuntimeError("pg_dump produced an empty backup")
        # A non-empty file is not sufficient evidence that a custom-format dump is
        # readable. Preflight it before the atomic rename, matching restore safety.
        subprocess.run([pg_restore, "--list", str(tmp)], check=True, env=env, stdout=subprocess.DEVNULL)
        tmp.replace(output)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a verified Opportunity Radar database backup")
    parser.add_argument("--output-dir", default="backups")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = Path(args.output_dir)
    if settings.database_url.startswith("sqlite:///"):
        path = directory / f"opportunity-radar-{stamp}.sqlite3"
        backup_sqlite(settings.database_url, path)
    elif settings.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        path = directory / f"opportunity-radar-{stamp}.pgdump"
        backup_postgres(settings.database_url, path)
    else:
        raise RuntimeError("unsupported DATABASE_URL for backup")
    print(path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
