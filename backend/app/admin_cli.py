from __future__ import annotations

import argparse
import getpass

from app.db.session import SessionLocal
from app.services.auth import create_user


def main() -> int:
    parser = argparse.ArgumentParser(description="Opportunity Radar administration CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user", help="create a local RBAC user")
    create.add_argument("username")
    create.add_argument("--role", default="OWNER", choices=["OWNER", "ADMIN", "RESEARCHER", "VIEWER"])
    create.add_argument("--password")
    args = parser.parse_args()
    if args.command == "create-user":
        password = args.password or getpass.getpass("Password: ")
        with SessionLocal() as db:
            user = create_user(db, args.username, password, role=args.role)
            db.commit()
            print(f"USER_CREATED id={user.id} username={user.username} role={user.role}")
        return 0
    raise RuntimeError("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
