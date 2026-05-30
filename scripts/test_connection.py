#!/usr/bin/env python3
"""
测试数据库连接
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# 数据库配置
DATABASE_URL = "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"


async def test_connection():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    logger.info(f"数据库 URL: {DATABASE_URL}")

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        async with engine.connect() as conn:
            # 测试基本查询
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"PostgreSQL 版本: {version}")

            # 测试当前数据库
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"当前数据库: {db_name}")

            # 测试当前用户
            result = await conn.execute(text("SELECT current_user"))
            user = result.scalar()
            logger.info(f"当前用户: {user}")

            # 测试连接数
            result = await conn.execute(text("SELECT count(*) FROM pg_stat_activity"))
            conn_count = result.scalar()
            logger.info(f"当前连接数: {conn_count}")

        logger.info("✓ 数据库连接成功")
        return True

    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {e}")
        logger.error("")
        logger.error("请检查：")
        logger.error("  1. PostgreSQL 是否运行")
        logger.error("  2. 数据库 nanobot 是否存在")
        logger.error("  3. 用户名密码是否正确")
        logger.error("")
        logger.error("创建数据库：")
        logger.error("  CREATE DATABASE nanobot;")
        logger.error("")
        logger.error("创建用户：")
        logger.error("  CREATE USER nanobot WITH PASSWORD 'nanobot';")
        logger.error("  GRANT ALL PRIVILEGES ON DATABASE nanobot TO nanobot;")
        return False

    finally:
        await engine.dispose()


async def main():
    """主函数"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    logger.info("=" * 60)
    logger.info("数据库连接测试")
    logger.info("=" * 60)

    success = await test_connection()

    if success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ 数据库连接测试通过")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("")
        logger.error("=" * 60)
        logger.error("✗ 数据库连接测试失败")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
