#!/usr/bin/env python3
"""
Migrate users from users.json to PostgreSQL database.

Usage:
    python scripts/migrate_users_to_db.py
"""

import asyncio
import hashlib
import json
import secrets
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def migrate_users():
    """Migrate users from file to database."""
    from nanobot.storage.database_storage import DatabaseStorage
    from nanobot.config.database import init_database, DatabaseConfig

    # Load users from file
    users_file = Path.home() / ".nanobot" / "users.json"
    if not users_file.exists():
        print("[WARN] users.json not found, nothing to migrate")
        return

    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)

    if not users:
        print("[INFO] No users to migrate")
        return

    print(f"[INFO] Found {len(users)} users to migrate")

    # Initialize database
    try:
        db_config = DatabaseConfig()
        await init_database(db_config)
        storage = DatabaseStorage()
        print("[OK] Database connected")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        print("  Make sure PostgreSQL is running and DATABASE_URL is set")
        return

    # Migrate each user
    migrated = 0
    skipped = 0
    errors = 0

    for key, user_data in users.items():
        try:
            # Parse role:user_id from key
            parts = key.split(":", 1)
            if len(parts) != 2:
                print(f"[WARN] Invalid key format: {key}, skipping")
                skipped += 1
                continue

            role, user_id = parts

            # Check if user already exists in database
            existing = await storage.get_user(role, user_id)
            if existing:
                print(f"[SKIP] User {key} already exists in database")
                skipped += 1
                continue

            # Prepare user data for database
            # Support both camelCase and snake_case from old format
            db_user = {
                "role": role,
                "user_id": user_id,
                "display_name": user_data.get("displayName") or user_data.get("display_name", user_id),
                "email": user_data.get("email", ""),
                "password_hash": user_data.get("password_hash", ""),
                "password_salt": user_data.get("password_salt", ""),
                "profile": user_data.get("profile", {}),
                "settings": user_data.get("settings", {}),
            }

            # If user has no password hash, generate a random one (user will need to reset)
            if not db_user["password_hash"]:
                salt = secrets.token_hex(16)
                # Use a random password that won't work - user must re-register or reset
                random_pwd = secrets.token_hex(16)
                db_user["password_hash"] = hashlib.sha256(f"{salt}{random_pwd}".encode()).hexdigest()
                db_user["password_salt"] = salt
                print(f"[WARN] User {key} has no password, generated random hash (user needs to re-register)")

            # Create user in database
            await storage.create_user(db_user)
            print(f"[OK] Migrated user: {key}")
            migrated += 1

        except Exception as e:
            print(f"[ERROR] Failed to migrate user {key}: {e}")
            errors += 1

    print(f"\n" + "=" * 50)
    print(f"Migration complete:")
    print(f"  - Migrated: {migrated}")
    print(f"  - Skipped:  {skipped}")
    print(f"  - Errors:   {errors}")
    print("=" * 50)

    if migrated > 0:
        print("\n[INFO] Users with random passwords need to re-register to set their password.")


if __name__ == "__main__":
    asyncio.run(migrate_users())
