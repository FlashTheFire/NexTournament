import asyncio
import logging
from sqlalchemy import select
from src.database.connection import engine, async_session_factory
from src.database.models import Base, User, UserRole
from src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("init_db")


async def init_database() -> None:
    """Creates all database tables and seeds default SuperAdmin."""
    logger.info("Initializing PostgreSQL schema and tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT FALSE;"))
        except Exception as e:
            logger.debug(f"Column migration check: {e}")
    logger.info("Database tables verified successfully.")

    # Seed default SuperAdmin if not existing
    async with async_session_factory() as session:
        for admin_id in settings.SUPER_ADMIN_IDS:
            result = await session.execute(select(User).where(User.telegram_id == admin_id))
            user = result.scalar_one_or_none()
            if not user:
                admin_user = User(
                    telegram_id=admin_id,
                    first_name=f"Admin {admin_id}",
                    role=UserRole.SUPERADMIN
                )
                session.add(admin_user)
                logger.info(f"Seeded initial SuperAdmin: {admin_id}")
            else:
                if user.role != UserRole.SUPERADMIN:
                    user.role = UserRole.SUPERADMIN
                    logger.info(f"Elevated user {admin_id} to SUPERADMIN role.")
        await session.commit()
    logger.info("SuperAdmin verification completed.")


if __name__ == "__main__":
    asyncio.run(init_database())
