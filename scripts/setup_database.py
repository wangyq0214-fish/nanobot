#!/usr/bin/env python3
"""
数据库设置脚本
功能：连接数据库并创建所有表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# 数据库配置
DATABASE_URL = "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"


async def test_connection(engine):
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        logger.info("✓ 数据库连接成功")
        return True
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {e}")
        return False


async def create_tables(engine):
    """创建所有表"""
    logger.info("创建数据库表...")

    # 读取建表脚本
    script_path = Path(__file__).parent.parent / "docs" / "数据库表结构设计.md"

    # 提取 SQL 语句
    sql_statements = []
    in_sql_block = False
    current_sql = []

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == "```sql":
                in_sql_block = True
                current_sql = []
            elif line.strip() == "```" and in_sql_block:
                in_sql_block = False
                sql = "\n".join(current_sql).strip()
                if sql and sql.startswith("CREATE"):
                    sql_statements.append(sql)
            elif in_sql_block:
                current_sql.append(line)

    # 执行 SQL 语句
    async with engine.begin() as conn:
        for i, sql in enumerate(sql_statements, 1):
            try:
                # 提取表名
                table_name = sql.split("(")[0].replace("CREATE TABLE", "").strip()
                logger.info(f"  创建表 {i}/{len(sql_statements)}: {table_name}")
                await conn.execute(text(sql))
            except Exception as e:
                logger.warning(f"  跳过表 {i}: {e}")

    logger.info(f"✓ 成功创建 {len(sql_statements)} 个表")


async def create_indexes(engine):
    """创建索引"""
    logger.info("创建索引...")

    # 读取建表脚本
    script_path = Path(__file__).parent.parent / "docs" / "数据库表结构设计.md"

    # 提取索引 SQL
    index_statements = []
    in_sql_block = False
    current_sql = []

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == "```sql":
                in_sql_block = True
                current_sql = []
            elif line.strip() == "```" and in_sql_block:
                in_sql_block = False
                sql = "\n".join(current_sql).strip()
                if sql and sql.startswith("CREATE INDEX"):
                    index_statements.append(sql)
            elif in_sql_block:
                current_sql.append(line)

    # 执行索引 SQL
    async with engine.begin() as conn:
        for i, sql in enumerate(index_statements, 1):
            try:
                # 提取索引名
                index_name = sql.split("ON")[0].replace("CREATE INDEX", "").strip()
                logger.info(f"  创建索引 {i}/{len(index_statements)}: {index_name}")
                await conn.execute(text(sql))
            except Exception as e:
                logger.warning(f"  跳过索引 {i}: {e}")

    logger.info(f"✓ 成功创建 {len(index_statements)} 个索引")


async def verify_tables(engine):
    """验证表是否创建成功"""
    logger.info("验证表...")

    async with engine.connect() as conn:
        # 查询所有表
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]

        logger.info(f"数据库中的表 ({len(tables)} 个):")
        for table in tables:
            logger.info(f"  - {table}")

        # 检查必需的表
        required_tables = [
            'users',
            'courses',
            'course_members',
            'teacher_lessons',
            'course_lessons',
            'homework',
            'questions',
            'submissions',
            'course_resources',
            'learning_progress',
            'notifications',
            'audit_logs'
        ]

        missing_tables = [t for t in required_tables if t not in tables]
        if missing_tables:
            logger.warning(f"缺少表: {missing_tables}")
            return False

        logger.info("✓ 所有必需的表都已创建")
        return True


async def main():
    """主函数"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    logger.info("=" * 60)
    logger.info("数据库设置")
    logger.info("=" * 60)
    logger.info(f"数据库 URL: {DATABASE_URL}")

    # 创建引擎
    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        # 1. 测试连接
        if not await test_connection(engine):
            logger.error("无法连接数据库，请检查：")
            logger.error("  1. PostgreSQL 是否运行")
            logger.error("  2. 数据库 nanobot 是否存在")
            logger.error("  3. 用户名密码是否正确")
            return 1

        # 2. 创建表
        await create_tables(engine)

        # 3. 创建索引
        await create_indexes(engine)

        # 4. 验证表
        if await verify_tables(engine):
            logger.info("")
            logger.info("=" * 60)
            logger.info("✓ 数据库设置完成！")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("数据库设置失败")
            return 1

    except Exception as e:
        logger.error(f"数据库设置失败: {e}")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
