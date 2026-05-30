#!/usr/bin/env python3
"""Quick script to check database connection."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def check_connection():
    """Check database connection."""
    from nanobot.config.database import db_manager

    print("Checking database connection...")

    try:
        await db_manager.initialize()
        print("✓ Database connection successful")

        async for session in db_manager.get_session():
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("✓ Database query successful")

        await db_manager.close()
        print("✓ Database connection closed")
        return True

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def main():
    """Main function."""
    success = await check_connection()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
