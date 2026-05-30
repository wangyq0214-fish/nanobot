"""Tests for database storage layer."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from nanobot.storage.database_storage import DatabaseStorage
from nanobot.storage.storage_wrapper import StorageWrapper
from nanobot.models import User, Course, CourseMember, Lesson, Homework, Submission


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def db_storage(mock_session):
    """Create a DatabaseStorage instance with mock session."""
    return DatabaseStorage(mock_session)


@pytest.fixture
def file_storage():
    """Create a StorageWrapper instance for file-based storage."""
    return StorageWrapper(nanobot_dir=Path("/tmp/nanobot_test"))


class TestDatabaseStorage:
    """Test DatabaseStorage class."""

    @pytest.mark.asyncio
    async def test_get_user(self, db_storage, mock_session):
        """Test getting a user."""
        # Mock the session.get to return a user
        mock_user = User(
            role="teacher",
            user_id="teacher1",
            display_name="张老师",
        )
        mock_session.get.return_value = mock_user

        result = await db_storage.get_user("teacher", "teacher1")
        assert result is not None
        assert result.role == "teacher"
        assert result.user_id == "teacher1"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, db_storage, mock_session):
        """Test getting a user that doesn't exist."""
        mock_session.get.return_value = None

        result = await db_storage.get_user("teacher", "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_user(self, db_storage, mock_session):
        """Test creating a user."""
        # Mock the session operations
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        result = await db_storage.create_user("teacher", "teacher1", "张老师")
        assert result is not None
        assert result.role == "teacher"
        assert result.user_id == "teacher1"
        assert result.display_name == "张老师"

    @pytest.mark.asyncio
    async def test_get_course(self, db_storage, mock_session):
        """Test getting a course."""
        mock_course = Course(
            course_id="course123",
            course_name="Python编程基础",
            subject="计算机科学",
            grade="大一",
            teacher_id="teacher1",
            teacher_role="teacher",
            teacher_name="张老师",
            join_code="123456",
        )
        mock_session.get.return_value = mock_course

        result = await db_storage.get_course("course123")
        assert result is not None
        assert result.course_id == "course123"
        assert result.course_name == "Python编程基础"

    @pytest.mark.asyncio
    async def test_create_course(self, db_storage, mock_session):
        """Test creating a course."""
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        course_data = {
            "courseId": "course123",
            "courseName": "Python编程基础",
            "subject": "计算机科学",
            "grade": "大一",
            "teacherId": "teacher1",
            "teacherName": "张老师",
            "joinCode": "123456",
            "isPublic": True,
        }
        result = await db_storage.create_course(course_data)
        assert result is not None
        assert result.course_id == "course123"
        assert result.course_name == "Python编程基础"


class TestStorageWrapper:
    """Test StorageWrapper class."""

    @pytest.mark.asyncio
    async def test_use_database_property(self, file_storage):
        """Test use_database property."""
        assert file_storage.use_database is False

        # Create wrapper with session
        wrapper = StorageWrapper(session=MagicMock())
        assert wrapper.use_database is True

    @pytest.mark.asyncio
    async def test_generate_id(self, file_storage):
        """Test ID generation."""
        id1 = file_storage._generate_id()
        id2 = file_storage._generate_id()
        assert len(id1) == 12
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_generate_join_code(self, file_storage):
        """Test join code generation."""
        code = file_storage._generate_join_code()
        assert len(code) == 6
        assert code.isdigit()


if __name__ == "__main__":
    pytest.main([__file__])
