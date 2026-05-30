"""Storage wrapper that provides unified interface for database and file-based storage."""

from __future__ import annotations

import json
import uuid
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from nanobot.storage.database_storage import DatabaseStorage


class StorageWrapper:
    """Unified storage interface that can use database or file-based storage.

    This wrapper allows gradual migration from file-based storage to database.
    When database is available, it uses DatabaseStorage.
    When database is not available, it falls back to file-based storage.
    """

    def __init__(self, session: AsyncSession | None = None, nanobot_dir: Path | None = None):
        """Initialize storage wrapper.

        Args:
            session: AsyncSession for database storage (None for file-based)
            nanobot_dir: Path to ~/.nanobot directory for file-based storage
        """
        self.session = session
        self.nanobot_dir = nanobot_dir or Path.home() / ".nanobot"
        self.db_storage = DatabaseStorage(session) if session else None

    @property
    def use_database(self) -> bool:
        """Check if database storage is available."""
        return self.db_storage is not None

    # -- User management -------------------------------------------------------

    async def get_user(self, role: str, user_id: str) -> dict[str, Any] | None:
        """Get a user by role and user_id."""
        if self.use_database:
            user = await self.db_storage.get_user(role, user_id)
            return user.to_dict() if user else None

        # Fallback to file-based storage
        users_file = self.nanobot_dir / "users.json"
        if not users_file.exists():
            return None
        try:
            data = json.loads(users_file.read_text(encoding="utf-8"))
            key = f"{role}:{user_id}"
            return data.get(key)
        except (json.JSONDecodeError, OSError):
            return None

    async def create_user(self, role: str, user_id: str, display_name: str | None = None) -> dict[str, Any]:
        """Create a new user."""
        if self.use_database:
            user = await self.db_storage.create_user(role, user_id, display_name)
            return user.to_dict()

        # Fallback to file-based storage
        users_file = self.nanobot_dir / "users.json"
        users_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = json.loads(users_file.read_text(encoding="utf-8")) if users_file.exists() else {}
        except (json.JSONDecodeError, OSError):
            data = {}

        key = f"{role}:{user_id}"
        user_data = {
            "role": role,
            "userId": user_id,
            "displayName": display_name or user_id,
            "registeredAt": datetime.now(timezone.utc).isoformat(),
        }
        data[key] = user_data
        users_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info("Created user: {} (role={})", user_id, role)
        return user_data

    # -- Course management -----------------------------------------------------

    async def get_course(self, course_id: str) -> dict[str, Any] | None:
        """Get a course by ID."""
        if self.use_database:
            course = await self.db_storage.get_course(course_id)
            return course.to_dict() if course else None

        # Fallback to file-based storage
        course_file = self.nanobot_dir / "courses" / course_id / "course.json"
        if not course_file.exists():
            return None
        try:
            return json.loads(course_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    async def create_course(self, course_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new course."""
        if self.use_database:
            course = await self.db_storage.create_course(course_data)
            return course.to_dict()

        # Fallback to file-based storage
        course_id = course_data["courseId"]
        courses_dir = self.nanobot_dir / "courses"
        course_dir = courses_dir / course_id
        course_dir.mkdir(parents=True, exist_ok=True)

        # Save course.json
        course_file = course_dir / "course.json"
        course_file.write_text(json.dumps(course_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Update index
        index_file = courses_dir / "index.json"
        try:
            index = json.loads(index_file.read_text(encoding="utf-8")) if index_file.exists() else {}
        except (json.JSONDecodeError, OSError):
            index = {}

        index[course_id] = course_data
        index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info("Created course: {} - {}", course_id, course_data.get("courseName"))
        return course_data

    async def list_courses(
        self,
        role: str | None = None,
        user_id: str | None = None,
        is_public: bool | None = None,
    ) -> list[dict[str, Any]]:
        """List courses with optional filters."""
        if self.use_database:
            courses = await self.db_storage.list_courses(role, user_id, is_public)
            return [c.to_dict() for c in courses]

        # Fallback to file-based storage
        index_file = self.nanobot_dir / "courses" / "index.json"
        if not index_file.exists():
            return []

        try:
            index = json.loads(index_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        courses = list(index.values())

        # Apply filters
        if role == "teacher" and user_id:
            courses = [c for c in courses if c.get("teacherId") == user_id]
        elif role == "student" and user_id:
            # For students, return public courses + courses they're members of
            # This is a simplified version - in production, check members.json
            courses = [c for c in courses if c.get("isPublic", False)]

        return courses

    # -- Course members --------------------------------------------------------

    async def add_member(self, course_id: str, user_id: str, display_name: str) -> dict[str, Any]:
        """Add a member to a course."""
        if self.use_database:
            member = await self.db_storage.add_member(course_id, user_id, display_name)
            return member.to_dict()

        # Fallback to file-based storage
        members_file = self.nanobot_dir / "courses" / course_id / "members.json"
        members_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            members = json.loads(members_file.read_text(encoding="utf-8")) if members_file.exists() else []
        except (json.JSONDecodeError, OSError):
            members = []

        member_data = {
            "userId": user_id,
            "displayName": display_name,
            "joinedAt": datetime.now(timezone.utc).isoformat(),
        }
        members.append(member_data)
        members_file.write_text(json.dumps(members, ensure_ascii=False, indent=2), encoding="utf-8")

        # Update member count in course
        course_file = self.nanobot_dir / "courses" / course_id / "course.json"
        if course_file.exists():
            try:
                course = json.loads(course_file.read_text(encoding="utf-8"))
                course["memberCount"] = len(members)
                course_file.write_text(json.dumps(course, ensure_ascii=False, indent=2), encoding="utf-8")
            except (json.JSONDecodeError, OSError):
                pass

        logger.info("Added member {} to course {}", user_id, course_id)
        return member_data

    async def get_members(self, course_id: str) -> list[dict[str, Any]]:
        """Get all members of a course."""
        if self.use_database:
            members = await self.db_storage.get_members(course_id)
            return [m.to_dict() for m in members]

        # Fallback to file-based storage
        members_file = self.nanobot_dir / "courses" / course_id / "members.json"
        if not members_file.exists():
            return []
        try:
            return json.loads(members_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    # -- Lessons ---------------------------------------------------------------

    async def get_lesson(self, lesson_id: str) -> dict[str, Any] | None:
        """Get a lesson by ID."""
        if self.use_database:
            lesson = await self.db_storage.get_lesson(lesson_id)
            return lesson.to_dict() if lesson else None

        # Fallback to file-based storage - requires course_id
        # This is a limitation of file-based storage
        return None

    async def list_lessons(self, course_id: str) -> list[dict[str, Any]]:
        """List all lessons for a course."""
        if self.use_database:
            lessons = await self.db_storage.list_lessons(course_id)
            return [l.to_dict() for l in lessons]

        # Fallback to file-based storage
        lessons_dir = self.nanobot_dir / "courses" / course_id / "lessons"
        if not lessons_dir.is_dir():
            return []

        lessons = []
        for d in sorted(lessons_dir.iterdir()):
            if d.is_dir():
                lesson_file = d / "lesson.json"
                if lesson_file.exists():
                    try:
                        lessons.append(json.loads(lesson_file.read_text(encoding="utf-8")))
                    except (json.JSONDecodeError, OSError):
                        continue
        return lessons

    # -- Homework --------------------------------------------------------------

    async def get_homework(self, hw_id: str) -> dict[str, Any] | None:
        """Get a homework by ID."""
        if self.use_database:
            homework = await self.db_storage.get_homework(hw_id)
            return homework.to_dict() if homework else None

        # Fallback to file-based storage - requires course_id
        return None

    async def list_homework(self, course_id: str) -> list[dict[str, Any]]:
        """List all homework for a course."""
        if self.use_database:
            homework_list = await self.db_storage.list_homework(course_id)
            return [h.to_dict() for h in homework_list]

        # Fallback to file-based storage
        hw_dir = self.nanobot_dir / "courses" / course_id / "homework"
        if not hw_dir.is_dir():
            return []

        result = []
        for f in sorted(hw_dir.glob("*.json")):
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return result

    # -- Submissions -----------------------------------------------------------

    async def get_submission(self, hw_id: str, student_id: str) -> dict[str, Any] | None:
        """Get a submission by homework and student."""
        if self.use_database:
            submission = await self.db_storage.get_submission(hw_id, student_id)
            return submission.to_dict() if submission else None

        # Fallback to file-based storage - requires course_id
        return None

    async def list_submissions(self, hw_id: str) -> list[dict[str, Any]]:
        """List all submissions for a homework."""
        if self.use_database:
            submissions = await self.db_storage.list_submissions(hw_id)
            return [s.to_dict() for s in submissions]

        # Fallback to file-based storage - requires course_id
        return []

    # -- Utilities -------------------------------------------------------------

    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return uuid.uuid4().hex[:12]

    def _generate_join_code(self) -> str:
        """Generate a 6-digit join code."""
        return f"{secrets.randbelow(1_000_000):06d}"
