"""Migration script to move data from file-based storage to PostgreSQL database."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nanobot.models import User, Course, CourseMember, Lesson, Homework, Question, Submission


async def migrate_users(session: AsyncSession, users_file: Path) -> int:
    """Migrate users from users.json to database."""
    if not users_file.exists():
        logger.warning("Users file not found: {}", users_file)
        return 0

    try:
        data = json.loads(users_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to read users file: {}", e)
        return 0

    count = 0
    for key, user_data in data.items():
        try:
            # Check if user already exists
            existing = await session.get(User, (user_data["role"], user_data["userId"]))
            if existing:
                logger.debug("User already exists: {}", key)
                continue

            user = User.from_dict(user_data)
            session.add(user)
            count += 1
        except Exception as e:
            logger.error("Failed to migrate user {}: {}", key, e)

    await session.commit()
    logger.info("Migrated {} users", count)
    return count


async def migrate_courses(session: AsyncSession, courses_dir: Path) -> int:
    """Migrate courses from file-based storage to database."""
    index_file = courses_dir / "index.json"
    if not index_file.exists():
        logger.warning("Courses index file not found: {}", index_file)
        return 0

    try:
        index_data = json.loads(index_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to read courses index: {}", e)
        return 0

    count = 0
    for course_id, _ in index_data.items():
        try:
            # Check if course already exists
            existing = await session.get(Course, course_id)
            if existing:
                logger.debug("Course already exists: {}", course_id)
                continue

            # Load full course data
            course_file = courses_dir / course_id / "course.json"
            if not course_file.exists():
                logger.warning("Course file not found: {}", course_file)
                continue

            course_data = json.loads(course_file.read_text(encoding="utf-8"))
            course = Course.from_dict(course_data)
            session.add(course)
            count += 1
        except Exception as e:
            logger.error("Failed to migrate course {}: {}", course_id, e)

    await session.commit()
    logger.info("Migrated {} courses", count)
    return count


async def migrate_course_members(session: AsyncSession, courses_dir: Path) -> int:
    """Migrate course members from file-based storage to database."""
    count = 0

    # Get all course directories
    for course_dir in courses_dir.iterdir():
        if not course_dir.is_dir():
            continue

        course_id = course_dir.name
        members_file = course_dir / "members.json"
        if not members_file.exists():
            continue

        try:
            members_data = json.loads(members_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read members for course {}: {}", course_id, e)
            continue

        for member_data in members_data:
            try:
                # Check if member already exists
                existing = await session.execute(
                    select(CourseMember).where(
                        CourseMember.course_id == course_id,
                        CourseMember.user_id == member_data["userId"],
                        CourseMember.user_role == "student",
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                member = CourseMember.from_dict(member_data, course_id)
                session.add(member)
                count += 1
            except Exception as e:
                logger.error("Failed to migrate member {} in course {}: {}",
                           member_data.get("userId"), course_id, e)

    await session.commit()
    logger.info("Migrated {} course members", count)
    return count


async def migrate_lessons(session: AsyncSession, courses_dir: Path) -> int:
    """Migrate lessons from file-based storage to database."""
    count = 0

    for course_dir in courses_dir.iterdir():
        if not course_dir.is_dir():
            continue

        course_id = course_dir.name
        lessons_dir = course_dir / "lessons"
        if not lessons_dir.is_dir():
            continue

        for lesson_dir in lessons_dir.iterdir():
            if not lesson_dir.is_dir():
                continue

            lesson_file = lesson_dir / "lesson.json"
            if not lesson_file.exists():
                continue

            try:
                lesson_data = json.loads(lesson_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to read lesson {}: {}", lesson_dir.name, e)
                continue

            try:
                # Check if lesson already exists
                existing = await session.get(Lesson, lesson_data.get("lessonId", lesson_dir.name))
                if existing:
                    continue

                # Ensure lessonId is set
                if "lessonId" not in lesson_data:
                    lesson_data["lessonId"] = lesson_dir.name

                # Calculate plan path (relative to courses directory)
                plan_file = lesson_dir / "plan.md"
                if plan_file.exists():
                    lesson_data["planPath"] = str(plan_file.relative_to(courses_dir))

                lesson = Lesson.from_dict(lesson_data, course_id)
                session.add(lesson)
                count += 1
            except Exception as e:
                logger.error("Failed to migrate lesson {}: {}", lesson_dir.name, e)

    await session.commit()
    logger.info("Migrated {} lessons", count)
    return count


async def migrate_homework(session: AsyncSession, courses_dir: Path) -> int:
    """Migrate homework from file-based storage to database."""
    count = 0

    for course_dir in courses_dir.iterdir():
        if not course_dir.is_dir():
            continue

        course_id = course_dir.name
        homework_dir = course_dir / "homework"
        if not homework_dir.is_dir():
            continue

        for hw_file in homework_dir.glob("*.json"):
            try:
                hw_data = json.loads(hw_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to read homework {}: {}", hw_file.name, e)
                continue

            try:
                # Check if homework already exists
                existing = await session.get(Homework, hw_data["hwId"])
                if existing:
                    continue

                homework = Homework.from_dict(hw_data)

                # Add questions
                for q_data in hw_data.get("questions", []):
                    question = Question.from_dict(q_data, hw_data["hwId"])
                    homework.questions.append(question)

                session.add(homework)
                count += 1
            except Exception as e:
                logger.error("Failed to migrate homework {}: {}", hw_file.name, e)

    await session.commit()
    logger.info("Migrated {} homework assignments", count)
    return count


async def migrate_submissions(session: AsyncSession, courses_dir: Path) -> int:
    """Migrate submissions from file-based storage to database."""
    count = 0

    for course_dir in courses_dir.iterdir():
        if not course_dir.is_dir():
            continue

        course_id = course_dir.name
        submissions_dir = course_dir / "homework" / "submissions"
        if not submissions_dir.is_dir():
            continue

        for sub_file in submissions_dir.glob("*.json"):
            try:
                sub_data = json.loads(sub_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to read submission {}: {}", sub_file.name, e)
                continue

            try:
                # Check if submission already exists
                existing = await session.execute(
                    select(Submission).where(
                        Submission.hw_id == sub_data["hwId"],
                        Submission.student_id == sub_data["studentId"],
                        Submission.student_role == "student",
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                submission = Submission.from_dict(sub_data, course_id)
                session.add(submission)
                count += 1
            except Exception as e:
                logger.error("Failed to migrate submission {}: {}", sub_file.name, e)

    await session.commit()
    logger.info("Migrated {} submissions", count)
    return count


async def migrate_file_to_database(session: AsyncSession, nanobot_dir: Path | None = None) -> dict[str, int]:
    """Run all migration steps from file-based storage to database.

    Args:
        session: Database session
        nanobot_dir: Path to ~/.nanobot directory (defaults to ~/.nanobot)

    Returns:
        Dictionary with counts of migrated entities
    """
    if nanobot_dir is None:
        nanobot_dir = Path.home() / ".nanobot"

    users_file = nanobot_dir / "users.json"
    courses_dir = nanobot_dir / "courses"

    logger.info("Starting migration from file-based storage to database")
    logger.info("Users file: {}", users_file)
    logger.info("Courses directory: {}", courses_dir)

    results = {}

    # Migrate in order of dependencies
    results["users"] = await migrate_users(session, users_file)
    results["courses"] = await migrate_courses(session, courses_dir)
    results["members"] = await migrate_course_members(session, courses_dir)
    results["lessons"] = await migrate_lessons(session, courses_dir)
    results["homework"] = await migrate_homework(session, courses_dir)
    results["submissions"] = await migrate_submissions(session, courses_dir)

    logger.info("Migration complete: {}", results)
    return results
