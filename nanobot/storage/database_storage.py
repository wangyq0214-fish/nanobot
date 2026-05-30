"""Database storage layer for nanobot courses and users."""

from __future__ import annotations

import json
import uuid
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nanobot.models import User, Course, CourseMember, Lesson, Homework, Question, Submission


class DatabaseStorage:
    """Database storage layer for nanobot.

    This class provides methods to interact with the database,
    replacing the file-based storage functions in websocket.py.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -- User management -------------------------------------------------------

    async def get_user(self, role: str, user_id: str) -> Optional[User]:
        """Get a user by role and user_id."""
        return await self.session.get(User, (role, user_id))

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by user_id (any role)."""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, role: str, user_id: str, display_name: str | None = None) -> User:
        """Create a new user."""
        user = User(
            role=role,
            user_id=user_id,
            display_name=display_name or user_id,
            registered_at=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.commit()
        logger.info("Created user: {} (role={})", user_id, role)
        return user

    async def list_users(self, role: str | None = None) -> list[User]:
        """List all users, optionally filtered by role."""
        query = select(User)
        if role:
            query = query.where(User.role == role)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # -- Course management -----------------------------------------------------

    async def get_course(self, course_id: str) -> Optional[Course]:
        """Get a course by ID."""
        return await self.session.get(Course, course_id)

    async def create_course(self, course_data: dict[str, Any]) -> Course:
        """Create a new course."""
        course = Course(
            course_id=course_data["courseId"],
            course_name=course_data["courseName"],
            subject=course_data["subject"],
            grade=course_data["grade"],
            description=course_data.get("description"),
            teacher_id=course_data["teacherId"],
            teacher_role="teacher",
            teacher_name=course_data["teacherName"],
            join_code=course_data["joinCode"],
            is_public=course_data.get("isPublic", False),
            member_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(course)
        await self.session.commit()
        logger.info("Created course: {} - {}", course.course_id, course.course_name)
        return course

    async def list_courses(
        self,
        role: str | None = None,
        user_id: str | None = None,
        is_public: bool | None = None,
    ) -> list[Course]:
        """List courses with optional filters."""
        query = select(Course)

        if role == "teacher" and user_id:
            query = query.where(Course.teacher_id == user_id)
        elif role == "student" and user_id:
            # Student sees public courses + courses they're a member of
            subquery = select(CourseMember.course_id).where(
                CourseMember.user_id == user_id,
                CourseMember.user_role == "student",
            )
            query = query.where(
                (Course.is_public == True) |  # noqa: E712
                (Course.course_id.in_(subquery))
            )
        elif is_public is not None:
            query = query.where(Course.is_public == is_public)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_course(self, course_id: str, **kwargs) -> Optional[Course]:
        """Update course fields."""
        course = await self.get_course(course_id)
        if not course:
            return None

        for key, value in kwargs.items():
            if hasattr(course, key):
                setattr(course, key, value)

        course.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return course

    # -- Course members --------------------------------------------------------

    async def add_member(self, course_id: str, user_id: str, display_name: str) -> CourseMember:
        """Add a member to a course."""
        member = CourseMember(
            course_id=course_id,
            user_id=user_id,
            user_role="student",
            display_name=display_name,
            joined_at=datetime.now(timezone.utc),
        )
        self.session.add(member)

        # Update member count
        course = await self.get_course(course_id)
        if course:
            course.member_count = (course.member_count or 0) + 1

        await self.session.commit()
        logger.info("Added member {} to course {}", user_id, course_id)
        return member

    async def get_members(self, course_id: str) -> list[CourseMember]:
        """Get all members of a course."""
        result = await self.session.execute(
            select(CourseMember).where(CourseMember.course_id == course_id)
        )
        return list(result.scalars().all())

    async def is_member(self, course_id: str, user_id: str) -> bool:
        """Check if a user is a member of a course."""
        result = await self.session.execute(
            select(CourseMember).where(
                CourseMember.course_id == course_id,
                CourseMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    # -- Lessons ---------------------------------------------------------------

    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Get a lesson by ID."""
        return await self.session.get(Lesson, lesson_id)

    async def list_lessons(self, course_id: str) -> list[Lesson]:
        """List all lessons for a course."""
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.order, Lesson.created_at)
        )
        return list(result.scalars().all())

    async def create_lesson(self, lesson_data: dict[str, Any], course_id: str) -> Lesson:
        """Create a new lesson."""
        lesson = Lesson(
            lesson_id=lesson_data.get("lessonId", self._generate_id()),
            course_id=course_id,
            title=lesson_data.get("title", ""),
            description=lesson_data.get("description"),
            order=lesson_data.get("order", 0),
            plan_path=lesson_data.get("planPath"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(lesson)
        await self.session.commit()
        logger.info("Created lesson: {} in course {}", lesson.lesson_id, course_id)
        return lesson

    async def update_lesson(self, lesson_id: str, **kwargs) -> Optional[Lesson]:
        """Update lesson fields."""
        lesson = await self.get_lesson(lesson_id)
        if not lesson:
            return None

        for key, value in kwargs.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        lesson.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return lesson

    # -- Homework --------------------------------------------------------------

    async def get_homework(self, hw_id: str) -> Optional[Homework]:
        """Get a homework by ID."""
        result = await self.session.execute(
            select(Homework)
            .where(Homework.hw_id == hw_id)
            .options(selectinload(Homework.questions))
        )
        return result.scalar_one_or_none()

    async def list_homework(self, course_id: str) -> list[Homework]:
        """List all homework for a course."""
        result = await self.session.execute(
            select(Homework)
            .where(Homework.course_id == course_id)
            .options(selectinload(Homework.questions))
            .order_by(Homework.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_homework(self, hw_data: dict[str, Any], course_id: str) -> Homework:
        """Create a new homework assignment."""
        hw_id = hw_data.get("hwId", f"hw{self._generate_id()}")
        homework = Homework(
            hw_id=hw_id,
            course_id=course_id,
            title=hw_data["title"],
            description=hw_data.get("description"),
            total_points=hw_data.get("totalPoints", 0),
            deadline=datetime.fromisoformat(hw_data["deadline"]) if hw_data.get("deadline") else None,
            created_by=hw_data.get("createdBy", ""),
            created_at=datetime.now(timezone.utc),
        )

        # Add questions
        for q_data in hw_data.get("questions", []):
            question = Question(
                hw_id=hw_id,
                question_id=q_data["id"],
                question_type=q_data.get("type", "short_answer"),
                content=q_data["content"],
                points=q_data.get("points", 0),
            )
            homework.questions.append(question)

        self.session.add(homework)
        await self.session.commit()
        logger.info("Created homework: {} in course {}", hw_id, course_id)
        return homework

    # -- Submissions -----------------------------------------------------------

    async def get_submission(self, hw_id: str, student_id: str) -> Optional[Submission]:
        """Get a submission by homework and student."""
        result = await self.session.execute(
            select(Submission).where(
                Submission.hw_id == hw_id,
                Submission.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_submissions(self, hw_id: str) -> list[Submission]:
        """List all submissions for a homework."""
        result = await self.session.execute(
            select(Submission).where(Submission.hw_id == hw_id)
        )
        return list(result.scalars().all())

    async def create_submission(self, sub_data: dict[str, Any], course_id: str) -> Submission:
        """Create a new submission."""
        submission = Submission(
            hw_id=sub_data["hwId"],
            student_id=sub_data["studentId"],
            student_role="student",
            course_id=course_id,
            answers=sub_data.get("answers", {}),
            status="submitted",
            score=0,
            total_score=sub_data.get("totalScore", 0),
            feedback={},
            submitted_at=datetime.now(timezone.utc),
        )
        self.session.add(submission)
        await self.session.commit()
        logger.info("Created submission: hw={}, student={}", sub_data["hwId"], sub_data["studentId"])
        return submission

    async def grade_submission(
        self,
        hw_id: str,
        student_id: str,
        score: int,
        feedback: dict,
        graded_by: str,
    ) -> Optional[Submission]:
        """Grade a submission."""
        submission = await self.get_submission(hw_id, student_id)
        if not submission:
            return None

        submission.score = score
        submission.feedback = feedback
        submission.status = "graded"
        submission.graded_at = datetime.now(timezone.utc)
        submission.graded_by = graded_by

        await self.session.commit()
        logger.info("Graded submission: hw={}, student={}, score={}", hw_id, student_id, score)
        return submission

    # -- Utilities -------------------------------------------------------------

    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return uuid.uuid4().hex[:12]

    def _generate_join_code(self) -> str:
        """Generate a 6-digit join code."""
        return f"{secrets.randbelow(1_000_000):06d}"
