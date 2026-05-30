#!/usr/bin/env python3
"""Test script to verify database connection and migration."""

import asyncio
import sys
from pathlib import Path

from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_database_connection():
    """Test database connection."""
    from nanobot.config.database import db_manager

    logger.info("Testing database connection...")

    try:
        await db_manager.initialize()
        logger.info("✓ Database connection successful")

        # Test creating tables
        await db_manager.create_tables()
        logger.info("✓ Tables created successfully")

        # Test session
        async for session in db_manager.get_session():
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            logger.info("✓ Session query successful")

        await db_manager.close()
        logger.info("✓ Database connection closed")

        return True

    except Exception as e:
        logger.error("✗ Database connection failed: {}", e)
        return False


async def test_migration():
    """Test migration from file-based storage."""
    from nanobot.config.database import db_manager, DatabaseManager
    from nanobot.migrations.file_to_db import migrate_file_to_database

    logger.info("\nTesting migration...")

    # Use a test database
    test_db_url = "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot_test"
    test_manager = DatabaseManager(test_db_url)

    try:
        await test_manager.initialize()
        await test_manager.create_tables()
        logger.info("✓ Test database initialized")

        async for session in test_manager.get_session():
            results = await migrate_file_to_database(session)
            logger.info("✓ Migration completed: {}", results)

        await test_manager.close()
        return True

    except Exception as e:
        logger.error("✗ Migration test failed: {}", e)
        return False


async def main():
    """Run all tests."""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    logger.info("=" * 50)
    logger.info("Database Connection and Migration Test")
    logger.info("=" * 50)

    # Test 1: Database connection
    conn_ok = await test_database_connection()

    # Test 2: Migration (only if connection works)
    if conn_ok:
        migration_ok = await test_migration()
    else:
        migration_ok = False

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Test Summary:")
    logger.info("  Database Connection: {}", "✓ PASS" if conn_ok else "✗ FAIL")
    logger.info("  Migration Test: {}", "✓ PASS" if migration_ok else "✗ FAIL")
    logger.info("=" * 50)

    return 0 if (conn_ok and migration_ok) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
