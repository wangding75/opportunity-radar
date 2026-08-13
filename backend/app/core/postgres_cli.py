from __future__ import annotations

import os
from collections.abc import Mapping

from sqlalchemy.engine import make_url

_SSL_ENV = {
    "sslmode": "PGSSLMODE",
    "sslrootcert": "PGSSLROOTCERT",
    "sslcert": "PGSSLCERT",
    "sslkey": "PGSSLKEY",
}


def postgres_cli_connection(database_url: str, *, database_override: str | None = None) -> tuple[list[str], dict[str, str]]:
    """Convert a SQLAlchemy PostgreSQL URL into libpq CLI args and a safe env.

    Credentials are deliberately kept out of argv so process listings do not expose
    the database password. SQLAlchemy driver suffixes such as +psycopg are removed
    by parsing the URL rather than forwarding it verbatim to pg_dump/pg_restore.
    """
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("not a PostgreSQL DATABASE_URL")
    if not url.database:
        raise ValueError("PostgreSQL DATABASE_URL must include a database name")
    database = database_override or url.database

    args: list[str] = []
    if url.host:
        args += ["--host", url.host]
    if url.port:
        args += ["--port", str(url.port)]
    if url.username:
        args += ["--username", url.username]
    args += ["--dbname", database]

    env = os.environ.copy()
    if url.password is not None:
        env["PGPASSWORD"] = url.password

    query: Mapping[str, object] = url.query
    for key, env_name in _SSL_ENV.items():
        value = query.get(key)
        if value is not None:
            if isinstance(value, tuple):
                value = value[-1]
            env[env_name] = str(value)
    return args, env


def postgres_cli_server_args(database_url: str) -> tuple[list[str], dict[str, str]]:
    """Return host/port/user CLI args without a database selector."""
    args, env = postgres_cli_connection(database_url)
    result: list[str] = []
    index = 0
    while index < len(args):
        if args[index] == "--dbname":
            index += 2
            continue
        result.append(args[index])
        if args[index] in {"--host", "--port", "--username"} and index + 1 < len(args):
            result.append(args[index + 1])
            index += 2
        else:
            index += 1
    return result, env
