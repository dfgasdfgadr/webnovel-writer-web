"""Create a default dev user if it does not exist."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import async_session, engine, Base
from app.models.user import User
from app.services.auth import hash_password


DEV_USERNAME = "admin"
DEV_PASSWORD = "admin123456"
DEV_DISPLAY_NAME = "管理员"


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == DEV_USERNAME))
        if result.scalar_one_or_none():
            print(f"Dev user already exists: {DEV_USERNAME}")
            return

        user = User(
            username=DEV_USERNAME,
            display_name=DEV_DISPLAY_NAME,
            hashed_password=hash_password(DEV_PASSWORD),
        )
        db.add(user)
        await db.commit()
        print(f"Created dev user: {DEV_USERNAME} / {DEV_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
