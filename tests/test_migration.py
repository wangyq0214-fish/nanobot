"""Tests for database migration."""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from nanobot.migrations.file_to_db import (
    migrate_users,
    migrate_courses,
    migrate_course_members,
    migrate_lessons,
    migrate_homework,
    migrate_submissions,
)


@pytest.fixture
def temp_nanobot_dir():
    """Create a temporary nanobot directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nanobot_dir = Path(tmpdir)

        # Create users.json
        users_data = {
            "teacher:teacher1": {
                "role": "teacher",
                "userId": "teacher1",
                "displayName": "张老师",
                "registeredAt": datetime.now(timezone.utc).isoformat(),
            },
            "student:student1": {
                "role": "student",
                "userId": "student1",
                "displayName": "李同学",
                "registeredAt": datetime.now(timezone.utc).isoformat(),
            },
        }
        (nanobot_dir / "users.json").write_text(
            json.dumps(users_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Create course structure
        course_id = "course123"
        course_dir = nanobot_dir / "courses" / course_id
        course_dir.mkdir(parents=True)

        # Course index
        index_data = {
            course_id: {
                "courseId": course_id,
                "courseName": "Python编程基础",
                "subject": "计算机科学",
                "grade": "大一",
                "teacherId": "teacher1",
                "teacherName": "张老师",
                "joinCode": "123456",
                "isPublic": True,
                "memberCount": 1,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
        }
        (nanobot_dir / "courses" / "index.json").write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Course detail
        course_data = {
            **index_data[course_id],
            "description": "Python编程基础课程",
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        (course_dir / "course.json").write_text(
            json.dumps(course_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Members
        members_data = [
            {
                "userId": "student1",
                "displayName": "李同学",
                "joinedAt": datetime.now(timezone.utc).isoformat(),
            }
        ]
        (course_dir / "members.json").write_text(
            json.dumps(members_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Lesson
        lesson_dir = course_dir / "lessons" / "lesson1"
        lesson_dir.mkdir(parents=True)
        lesson_data = {
            "lessonId": "lesson1",
            "title": "Python简介",
            "description": "Python语言的历史和特点",
            "order": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        (lesson_dir / "lesson.json").write_text(
            json.dumps(lesson_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (lesson_dir / "plan.md").write_text("# Python简介\n\nPython是一种解释型编程语言。", encoding="utf-8")

        # Homework
        homework_dir = course_dir / "homework"
        homework_dir.mkdir(parents=True)
        hw_data = {
            "hwId": "hw123",
            "courseId": course_id,
            "title": "Python基础作业",
            "description": "完成以下编程题目",
            "totalPoints": 100,
            "deadline": datetime.now(timezone.utc).isoformat(),
            "createdBy": "teacher1",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "questions": [
                {
                    "id": "q1",
                    "type": "short_answer",
                    "content": "Python是什么类型的编程语言？",
                    "points": 20,
                },
            ],
        }
        (homework_dir / "hw123.json").write_text(
            json.dumps(hw_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Submission
        submissions_dir = homework_dir / "submissions"
        submissions_dir.mkdir(parents=True)
        sub_data = {
            "hwId": "hw123",
            "studentId": "student1",
            "answers": {"q1": "Python是解释型编程语言"},
            "submittedAt": datetime.now(timezone.utc).isoformat(),
            "status": "submitted",
            "score": 0,
            "totalScore": 100,
            "feedback": {},
            "gradedAt": None,
            "gradedBy": None,
        }
        (submissions_dir / "student1.json").write_text(
            json.dumps(sub_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        yield nanobot_dir


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    from unittest.mock import AsyncMock, MagicMock

    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()

    # Mock execute to return empty result
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute.return_value = mock_result

    return session


class TestMigration:
    """Test migration functions."""

    @pytest.mark.asyncio
    async def test_migrate_users(self, mock_session, temp_nanobot_dir):
        """Test migrating users."""
        users_file = temp_nanobot_dir / "users.json"
        count = await migrate_users(mock_session, users_file)
        assert count == 2
        assert mock_session.add.call_count == 2
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_migrate_courses(self, mock_session, temp_nanobot_dir):
        """Test migrating courses."""
        courses_dir = temp_nanobot_dir / "courses"
        count = await migrate_courses(mock_session, courses_dir)
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_migrate_course_members(self, mock_session, temp_nanobot_dir):
        """Test migrating course members."""
        courses_dir = temp_nanobot_dir / "courses"
        count = await migrate_course_members(mock_session, courses_dir)
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_migrate_lessons(self, mock_session, temp_nanobot_dir):
        """Test migrating lessons."""
        courses_dir = temp_nanobot_dir / "courses"
        count = await migrate_lessons(mock_session, courses_dir)
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_migrate_homework(self, mock_session, temp_nanobot_dir):
        """Test migrating homework."""
        courses_dir = temp_nanobot_dir / "courses"
        count = await migrate_homework(mock_session, courses_dir)
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_migrate_submissions(self, mock_session, temp_nanobot_dir):
        """Test migrating submissions."""
        courses_dir = temp_nanobot_dir / "courses"
        count = await migrate_submissions(mock_session, courses_dir)
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_migrate_all(self, mock_session, temp_nanobot_dir):
        """Test migrating all data."""
        from nanobot.migrations.file_to_db import migrate_file_to_database

        results = await migrate_file_to_database(mock_session, temp_nanobot_dir)
        assert results["users"] == 2
        assert results["courses"] == 1
        assert results["members"] == 1
        assert results["lessons"] == 1
        assert results["homework"] == 1
        assert results["submissions"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
