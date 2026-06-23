"""Database seed script.

Populates the database with:
1. Default users (admin, reviewer, viewer)
2. Synthetic sample messages

Run with: python -m app.data.seed
"""

import asyncio
import structlog
from sqlalchemy import select

from app.db.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.models import User, Message, RoleEnum, MessageSourceEnum
from app.data.seed_data import SYNTHETIC_MESSAGES

logger = structlog.get_logger(__name__)

DEFAULT_USERS = [
    {"email": "admin@crisisnet.dev", "password": "admin1234", "role": RoleEnum.admin},
    {"email": "reviewer@crisisnet.dev", "password": "reviewer1234", "role": RoleEnum.human_reviewer},
    {"email": "viewer@crisisnet.dev", "password": "viewer1234", "role": RoleEnum.viewer},
]


async def seed_database():
    """Seed the database with default users and synthetic messages."""

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Seed users
        for user_data in DEFAULT_USERS:
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            if not result.scalar_one_or_none():
                user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                )
                db.add(user)
                logger.info("seeded_user", email=user_data["email"], role=user_data["role"].value)

        await db.commit()

        # Seed synthetic messages
        result = await db.execute(select(Message).limit(1))
        if not result.scalar_one_or_none():
            for msg_data in SYNTHETIC_MESSAGES:
                message = Message(
                    source=MessageSourceEnum.synthetic_seed,
                    original_text_encrypted=msg_data["text"],  # TODO: Encrypt
                    redacted_text=None,  # Will be processed by the pipeline
                )
                db.add(message)

            await db.commit()
            logger.info("seeded_messages", count=len(SYNTHETIC_MESSAGES))
        else:
            logger.info("messages_already_seeded")

    logger.info("seed_complete")


if __name__ == "__main__":
    asyncio.run(seed_database())
