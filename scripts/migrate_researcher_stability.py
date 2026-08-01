"""Idempotent PostgreSQL migration for researcher-side stabilization.

Run with the same DATABASE_URL used by the service.  The statements only add
columns/tables/indexes and never remove or rewrite existing user data.
"""

from __future__ import annotations

import asyncio
import os

from sqlalchemy import text

from nanobot.config.database import get_engine


STATEMENTS = [
    "ALTER TABLE papers ADD COLUMN IF NOT EXISTS user_role VARCHAR(20) NOT NULL DEFAULT 'researcher'",
    "UPDATE papers SET user_role = 'researcher' WHERE user_role IS NULL OR user_role = ''",
    "ALTER TABLE research_artifacts ADD COLUMN IF NOT EXISTS project_id INTEGER NULL",
    "ALTER TABLE research_attachments ADD COLUMN IF NOT EXISTS job_id INTEGER NULL",
    "CREATE INDEX IF NOT EXISTS ix_papers_user_role ON papers (user_id, user_role)",
    "CREATE INDEX IF NOT EXISTS ix_research_artifacts_project_id ON research_artifacts (project_id)",
    "CREATE INDEX IF NOT EXISTS ix_research_attachments_job_id ON research_attachments (job_id)",
    """
    CREATE TABLE IF NOT EXISTS research_project_papers (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
        paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_research_project_paper UNIQUE (project_id, paper_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_project_results (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
        result_id INTEGER NOT NULL REFERENCES research_results(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_research_project_result UNIQUE (project_id, result_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS research_jobs (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(64) NOT NULL,
        user_role VARCHAR(20) NOT NULL DEFAULT 'researcher',
        job_type VARCHAR(40) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'queued',
        progress INTEGER NOT NULL DEFAULT 0,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        result JSONB NOT NULL DEFAULT '{}'::jsonb,
        error_message TEXT NOT NULL DEFAULT '',
        attempts INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP NULL,
        finished_at TIMESTAMP NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_research_jobs_owner_status ON research_jobs (user_id, user_role, status)",
    "CREATE INDEX IF NOT EXISTS ix_research_jobs_type_status ON research_jobs (job_type, status)",
]


async def main() -> None:
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required")
    engine = get_engine()
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("researcher stability migration completed")


if __name__ == "__main__":
    asyncio.run(main())
