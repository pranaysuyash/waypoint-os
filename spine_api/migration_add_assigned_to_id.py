"""
Migration script: Add assigned_to_id column to trips table.

Run once:
    cd spine_api && PYTHONPATH=/path/to/project python migration_add_assigned_to_id.py
"""

import asyncio
import logging
import sys

from sqlalchemy import text

sys.path.insert(0, ".")

from persistence import tripstore_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")


async def run() -> None:
    async with tripstore_session_maker() as session:
        result = await session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'trips' AND column_name = 'assigned_to_id'"
            )
        )
        if result.first():
            logger.info("Column 'assigned_to_id' already exists. Skipping.")
            return

        logger.info("Adding column 'assigned_to_id' to trips table...")
        await session.execute(
            text(
                "ALTER TABLE trips "
                "ADD COLUMN assigned_to_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL"
            )
        )
        await session.commit()
        logger.info("Column added successfully.")


if __name__ == "__main__":
    asyncio.run(run())
