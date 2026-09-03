from __future__ import annotations

import argparse
import asyncio
import getpass

from sqlalchemy import select

from app.auth import hash_password
from app.db import SessionLocal
from app.models import User


async def create_user(email: str, password: str) -> None:
    async with SessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise SystemExit(f"User {email} already exists")

        db.add(User(email=email, password_hash=hash_password(password)))
        await db.commit()
    print(f"Created user {email}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-user", help="Create a login user")
    create_parser.add_argument("email")

    args = parser.parse_args()

    if args.command == "create-user":
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            raise SystemExit("Passwords do not match")
        asyncio.run(create_user(args.email, password))


if __name__ == "__main__":
    main()
