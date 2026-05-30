"""Tests for database models."""

import pytest
from datetime import datetime, timezone

from nanobot.models import User, Course, CourseMember, Lesson, Homework, Question, Submission


class TestUser:
    """Test User model."""

    def test_user_creation(self):
        """Test creating a User instance."""
        user = User(
            role="teacher",
            user_id="teacher1",
            display_name="张老师",
            registered_at=datetime.now(timezone.utc),
        )
        assert user.role == "teacher"
        assert user.user_id == "teacher1"
        assert user.display_name == "张老师"

    def test_user_to_dict(self):
        """Test converting User to dictionary."""
        now = datetime.now(timezone.utc)
        user = User(
            role="teacher",
            user_id="teacher1",
            display_name="张老师",
            registered_at=now,
        )
        result = user.to_dict()
        assert result["role"] == "teacher"
        assert result["userId"] == "teacher1"
        assert result["displayName"] == "张老师"
        assert result["registeredAt"] == now.isoformat()

    def test_user_from_dict(self):
        """Test creating User from dictionary."""
        now = datetime.now(timezone.utc)
        data = {
            "role": "teacher",
            "userId": "teacher1",
            "displayName": "张老师",
            "registeredAt": now.isoformat(),
        }
        user = User.from_dict(data)
        assert user.role == "teacher"
        assert user.user_id == "teacher1"
        assert user.display_name == "张老师"


class TestCourse:
    """Test Course model."""

    def test_course_creation(self):
        """Test creating a Course instance."""
        course = Course(
            course_id="course123",
            course_name="Python编程基础",
            subject="计算机科学",
            grade="大一",
            teacher_id="teacher1",
            teacher_role="teacher",
            teacher_name="张老师",
            join_code="123456",
            is_public=True,
            member_count=10,
        )
        assert course.course_id == "course123"
        assert course.course_name == "Python编程基础"
        assert course.join_code == "123456"

    def test_course_to_dict(self):
        """Test converting Course to dictionary."""
        now = datetime.now(timezone.utc)
        course = Course(
            course_id="course123",
            course_name="Python编程基础",
            subject="计算机科学",
            grade="大一",
            teacher_id="teacher1",
            teacher_role="teacher",
            teacher_name="张老师",
            join_code="123456",
            is_public=True,
            member_count=10,
            created_at=now,
            updated_at=now,
        )
        result = course.to_dict()
        assert result["courseId"] == "course123"
        assert result["courseName"] == "Python编程基础"
        assert result["joinCode"] == "123456"
        assert result["memberCount"] == 10

    def test_course_from_dict(self):
        """Test creating Course from dictionary."""
        now = datetime.now(timezone.utc)
        data = {
            "courseId": "course123",
            "courseName": "Python编程基础",
            "subject": "计算机科学",
            "grade": "大一",
            "teacherId": "teacher1",
            "teacherName": "张老师",
            "joinCode": "123456",
            "isPublic": True,
            "memberCount": 10,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        course = Course.from_dict(data)
        assert course.course_id == "course123"
        assert course.teacher_id == "teacher1"
        assert course.join_code == "123456"


class TestCourseMember:
    """Test CourseMember model."""

    def test_course_member_creation(self):
        """Test creating a CourseMember instance."""
        member = CourseMember(
            course_id="course123",
            user_id="student1",
            user_role="student",
            display_name="李同学",
            joined_at=datetime.now(timezone.utc),
        )
        assert member.course_id == "course123"
        assert member.user_id == "student1"

    def test_course_member_to_dict(self):
        """Test converting CourseMember to dictionary."""
        now = datetime.now(timezone.utc)
        member = CourseMember(
            course_id="course123",
            user_id="student1",
            user_role="student",
            display_name="李同学",
            joined_at=now,
        )
        result = member.to_dict()
        assert result["userId"] == "student1"
        assert result["displayName"] == "李同学"
        assert result["joinedAt"] == now.isoformat()


class TestHomework:
    """Test Homework model."""

    def test_homework_creation(self):
        """Test creating a Homework instance."""
        homework = Homework(
            hw_id="hw123",
            course_id="course123",
            title="Python基础作业",
            description="完成以下编程题目",
            total_points=100,
            created_by="teacher1",
        )
        assert homework.hw_id == "hw123"
        assert homework.title == "Python基础作业"
        assert homework.total_points == 100

    def test_homework_to_dict(self):
        """Test converting Homework to dictionary."""
        now = datetime.now(timezone.utc)
        homework = Homework(
            hw_id="hw123",
            course_id="course123",
            title="Python基础作业",
            description="完成以下编程题目",
            total_points=100,
            deadline=now,
            created_by="teacher1",
            created_at=now,
        )
        # Add a question
        question = Question(
            hw_id="hw123",
            question_id="q1",
            question_type="short_answer",
            content="Python是什么类型的编程语言？",
            points=20,
        )
        homework.questions.append(question)

        result = homework.to_dict()
        assert result["hwId"] == "hw123"
        assert result["title"] == "Python基础作业"
        assert len(result["questions"]) == 1
        assert result["questions"][0]["id"] == "q1"


class TestSubmission:
    """Test Submission model."""

    def test_submission_creation(self):
        """Test creating a Submission instance."""
        submission = Submission(
            hw_id="hw123",
            student_id="student1",
            student_role="student",
            course_id="course123",
            answers={"q1": "Python是解释型编程语言"},
            status="submitted",
            score=0,
            total_score=100,
        )
        assert submission.hw_id == "hw123"
        assert submission.student_id == "student1"
        assert submission.status == "submitted"

    def test_submission_to_dict(self):
        """Test converting Submission to dictionary."""
        now = datetime.now(timezone.utc)
        submission = Submission(
            hw_id="hw123",
            student_id="student1",
            student_role="student",
            course_id="course123",
            answers={"q1": "Python是解释型编程语言"},
            submitted_at=now,
            status="graded",
            score=90,
            total_score=100,
            feedback={"q1": "正确"},
            graded_at=now,
            graded_by="teacher1",
        )
        result = submission.to_dict()
        assert result["hwId"] == "hw123"
        assert result["studentId"] == "student1"
        assert result["score"] == 90
        assert result["status"] == "graded"


if __name__ == "__main__":
    pytest.main([__file__])
