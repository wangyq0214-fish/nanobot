"""
File-based storage implementation.

Implements the BaseStorage interface using JSON files.
This preserves the existing file-based storage logic.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseStorage

logger = logging.getLogger(__name__)


class FileStorage(BaseStorage):
    """
    File-based storage implementation.

    Uses JSON files for data persistence, maintaining compatibility
    with the existing storage structure.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize file storage.

        Args:
            base_path: Base directory for storage. Defaults to ~/.nanobot/
        """
        if base_path is None:
            base_path = Path.home() / ".nanobot"
        self.base_path = Path(base_path)
        self.courses_path = self.base_path / "courses"
        self.users_file = self.base_path / "users.json"

        # Ensure directories exist
        self.courses_path.mkdir(parents=True, exist_ok=True)

    def _load_json(self, path: Path) -> Any:
        """Load JSON from file."""
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {path}: {e}")
            return None

    def _save_json(self, path: Path, data: Any) -> None:
        """Save JSON to file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except IOError as e:
            logger.error(f"Failed to save {path}: {e}")
            raise

    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user. Returns created user data."""
        users = self._load_json(self.users_file) or {}

        user_id = user_data.get("user_id") or str(uuid.uuid4())
        user_data["user_id"] = user_id
        user_data["created_at"] = datetime.utcnow().isoformat()
        user_data["updated_at"] = datetime.utcnow().isoformat()

        key = f"{user_data.get('role', 'student')}:{user_id}"
        users[key] = user_data
        self._save_json(self.users_file, users)

        # Create user workspace
        workspace = self.base_path / "users" / user_data.get("role", "student") / user_id
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "sessions").mkdir(exist_ok=True)
        (workspace / "source").mkdir(exist_ok=True)
        (workspace / "memory").mkdir(exist_ok=True)

        logger.info(f"Created user: {user_id}")
        return user_data

    async def get_user(self, role: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by role and user_id. Returns None if not found."""
        users = self._load_json(self.users_file) or {}
        key = f"{role}:{user_id}"
        return users.get(key)

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username. Returns None if not found."""
        users = self._load_json(self.users_file) or {}
        for key, user in users.items():
            if user.get("username") == username:
                return user
        return None

    async def update_user(self, role: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data. Returns updated user data."""
        users = self._load_json(self.users_file) or {}
        key = f"{role}:{user_id}"
        if key not in users:
            raise ValueError(f"User not found: {key}")
        users[key].update(data)
        users[key]["updated_at"] = datetime.utcnow().isoformat()
        self._save_json(self.users_file, users)
        return users[key]

    async def delete_user(self, role: str, user_id: str) -> bool:
        """Delete user. Returns True if successful."""
        users = self._load_json(self.users_file) or {}
        key = f"{role}:{user_id}"
        if key in users:
            del users[key]
            self._save_json(self.users_file, users)
            return True
        return False

    async def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all users, optionally filtered by role."""
        users = self._load_json(self.users_file) or {}
        result = []
        for key, user in users.items():
            if role is None or user.get("role") == role:
                result.append(user)
        return result

    # Course operations
    async def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course. Returns created course data."""
        course_id = course_data.get("course_id") or str(uuid.uuid4())[:8]
        course_data["course_id"] = course_id
        course_data["created_at"] = datetime.utcnow().isoformat()
        course_data["updated_at"] = datetime.utcnow().isoformat()

        # Create course directory
        course_dir = self.courses_path / course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        (course_dir / "lessons").mkdir(exist_ok=True)
        (course_dir / "homework").mkdir(exist_ok=True)

        # Save course data
        self._save_json(course_dir / "course.json", course_data)

        # Update course index
        index = self._load_json(self.courses_path / "index.json") or {}
        index[course_id] = {
            "course_id": course_id,
            "name": course_data.get("name"),
            "created_at": course_data["created_at"],
        }
        self._save_json(self.courses_path / "index.json", index)

        logger.info(f"Created course: {course_id}")
        return course_data

    async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID. Returns None if not found."""
        course_file = self.courses_path / course_id / "course.json"
        return self._load_json(course_file)

    async def update_course(self, course_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update course data. Returns updated course data."""
        course_file = self.courses_path / course_id / "course.json"
        course = self._load_json(course_file)
        if not course:
            raise ValueError(f"Course not found: {course_id}")

        course.update(data)
        course["updated_at"] = datetime.utcnow().isoformat()
        self._save_json(course_file, course)
        return course

    async def delete_course(self, course_id: str) -> bool:
        """Delete course. Returns True if successful."""
        import shutil
        course_dir = self.courses_path / course_id
        if course_dir.exists():
            shutil.rmtree(course_dir)

            # Update index
            index = self._load_json(self.courses_path / "index.json") or {}
            if course_id in index:
                del index[course_id]
                self._save_json(self.courses_path / "index.json", index)

            return True
        return False

    async def list_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all courses, optionally filtered by user membership."""
        index = self._load_json(self.courses_path / "index.json") or {}
        courses = []

        for course_id in index:
            course = await self.get_course(course_id)
            if course:
                if user_id:
                    # Check if user is member
                    members_file = self.courses_path / course_id / "members.json"
                    members = self._load_json(members_file) or []
                    if any(m.get("user_id") == user_id for m in members):
                        courses.append(course)
                else:
                    courses.append(course)

        return courses

    async def get_teacher_courses(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get all courses for a specific teacher."""
        courses = await self.list_courses()
        # Support both camelCase and snake_case keys
        return [c for c in courses if c.get("teacher_id") == teacher_id or c.get("teacherId") == teacher_id]

    async def get_student_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all courses a student is enrolled in."""
        return await self.list_courses(user_id=user_id)

    async def get_course_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        """Find a course by its join code."""
        courses = await self.list_courses()
        for course in courses:
            # Support both camelCase and snake_case keys
            if course.get("join_code") == join_code or course.get("joinCode") == join_code:
                return course
        return None

    # Course member operations
    async def add_course_member(self, course_id: str, user_id: str, role: str = "student", display_name: str = "") -> Dict[str, Any]:
        """Add a member to a course. Returns membership data."""
        members_file = self.courses_path / course_id / "members.json"
        members = self._load_json(members_file) or []

        # Check if already member
        if any(m.get("user_id") == user_id for m in members):
            raise ValueError(f"User {user_id} is already a member of course {course_id}")

        member = {
            "user_id": user_id,
            "role": role,
            "display_name": display_name,
            "joined_at": datetime.utcnow().isoformat(),
        }
        members.append(member)
        self._save_json(members_file, members)

        logger.info(f"Added {user_id} to course {course_id} as {role}")
        return member

    async def remove_course_member(self, course_id: str, user_id: str) -> bool:
        """Remove a member from a course. Returns True if successful."""
        members_file = self.courses_path / course_id / "members.json"
        members = self._load_json(members_file) or []

        original_count = len(members)
        members = [m for m in members if m.get("user_id") != user_id]

        if len(members) < original_count:
            self._save_json(members_file, members)
            return True
        return False

    async def get_course_members(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all members of a course."""
        members_file = self.courses_path / course_id / "members.json"
        return self._load_json(members_file) or []

    async def is_course_member(self, course_id: str, user_id: str) -> bool:
        """Check if a user is a member of a course."""
        members = await self.get_course_members(course_id)
        return any(m.get("user_id") == user_id for m in members)

    async def get_course_members_count(self, course_id: str) -> int:
        """Get the number of members in a course."""
        members = await self.get_course_members(course_id)
        return len(members)

    # Lesson operations
    async def create_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lesson. Returns created lesson data."""
        course_id = lesson_data.get("course_id")
        lesson_id = lesson_data.get("lesson_id") or str(uuid.uuid4())[:8]
        lesson_data["lesson_id"] = lesson_id
        lesson_data["created_at"] = datetime.utcnow().isoformat()
        lesson_data["updated_at"] = datetime.utcnow().isoformat()

        # Create lesson directory
        lesson_dir = self.courses_path / course_id / "lessons" / lesson_id
        lesson_dir.mkdir(parents=True, exist_ok=True)

        # Save lesson data
        self._save_json(lesson_dir / "lesson.json", lesson_data)

        # Save plan content if provided
        if "plan_content" in lesson_data:
            (lesson_dir / "plan.md").write_text(lesson_data["plan_content"], encoding="utf-8")

        logger.info(f"Created lesson: {lesson_id}")
        return lesson_data

    async def get_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get lesson by ID. Returns None if not found."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                lessons_dir = course_dir / "lessons"
                if lessons_dir.exists():
                    for lesson_dir in lessons_dir.iterdir():
                        if lesson_dir.is_dir():
                            lesson_file = lesson_dir / "lesson.json"
                            lesson = self._load_json(lesson_file)
                            if lesson and lesson.get("lesson_id") == str(lesson_id):
                                # Load plan content if exists
                                plan_file = lesson_dir / "plan.md"
                                if plan_file.exists():
                                    lesson["plan_content"] = plan_file.read_text(encoding="utf-8")
                                return lesson
        return None

    async def update_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update lesson data. Returns updated lesson data."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                lessons_dir = course_dir / "lessons"
                if lessons_dir.exists():
                    for lesson_dir in lessons_dir.iterdir():
                        if lesson_dir.is_dir():
                            lesson_file = lesson_dir / "lesson.json"
                            lesson = self._load_json(lesson_file)
                            if lesson and lesson.get("lesson_id") == str(lesson_id):
                                lesson.update(data)
                                lesson["updated_at"] = datetime.utcnow().isoformat()
                                self._save_json(lesson_file, lesson)

                                # Update plan content if provided
                                if "plan_content" in data:
                                    (lesson_dir / "plan.md").write_text(data["plan_content"], encoding="utf-8")

                                return lesson
        raise ValueError(f"Lesson not found: {lesson_id}")

    async def delete_lesson(self, lesson_id: int) -> bool:
        """Delete lesson. Returns True if successful."""
        import shutil
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                lessons_dir = course_dir / "lessons"
                if lessons_dir.exists():
                    for lesson_dir in lessons_dir.iterdir():
                        if lesson_dir.is_dir():
                            lesson_file = lesson_dir / "lesson.json"
                            lesson = self._load_json(lesson_file)
                            if lesson and lesson.get("lesson_id") == str(lesson_id):
                                shutil.rmtree(lesson_dir)
                                return True
        return False

    async def list_lessons(self, course_id: str) -> List[Dict[str, Any]]:
        """List all lessons in a course."""
        lessons_dir = self.courses_path / course_id / "lessons"
        if not lessons_dir.exists():
            return []

        lessons = []
        for lesson_dir in lessons_dir.iterdir():
            if lesson_dir.is_dir():
                lesson_file = lesson_dir / "lesson.json"
                lesson = self._load_json(lesson_file)
                if lesson:
                    lessons.append(lesson)

        # Sort by order_index if available
        lessons.sort(key=lambda x: x.get("order_index", 0))
        return lessons

    # Homework operations
    async def create_homework(self, homework_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new homework. Returns created homework data."""
        course_id = homework_data.get("course_id")
        homework_id = homework_data.get("homework_id") or homework_data.get("hw_id") or str(uuid.uuid4())[:8]
        homework_data["homework_id"] = homework_id
        homework_data["created_at"] = datetime.utcnow().isoformat()
        homework_data["updated_at"] = datetime.utcnow().isoformat()

        # Save homework data
        homework_file = self.courses_path / course_id / "homework" / f"{homework_id}.json"
        self._save_json(homework_file, homework_data)

        # Create submissions directory
        submissions_dir = self.courses_path / course_id / "homework" / "submissions"
        submissions_dir.mkdir(exist_ok=True)

        logger.info(f"Created homework: {homework_id}")
        return homework_data

    async def get_homework(self, hw_id: str) -> Optional[Dict[str, Any]]:
        """Get homework by ID. Returns None if not found."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                homework_dir = course_dir / "homework"
                if homework_dir.exists():
                    homework_file = homework_dir / f"{hw_id}.json"
                    if homework_file.exists():
                        return self._load_json(homework_file)
        return None

    async def update_homework(self, hw_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update homework data. Returns updated homework data."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                homework_dir = course_dir / "homework"
                if homework_dir.exists():
                    homework_file = homework_dir / f"{hw_id}.json"
                    if homework_file.exists():
                        homework = self._load_json(homework_file)
                        homework.update(data)
                        homework["updated_at"] = datetime.utcnow().isoformat()
                        self._save_json(homework_file, homework)
                        return homework
        raise ValueError(f"Homework not found: {hw_id}")

    async def delete_homework(self, hw_id: str) -> bool:
        """Delete homework. Returns True if successful."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                homework_dir = course_dir / "homework"
                if homework_dir.exists():
                    homework_file = homework_dir / f"{hw_id}.json"
                    if homework_file.exists():
                        homework_file.unlink()
                        return True
        return False

    async def list_homework(self, course_id: str) -> List[Dict[str, Any]]:
        """List all homework in a course."""
        homework_dir = self.courses_path / course_id / "homework"
        if not homework_dir.exists():
            return []

        homework_list = []
        for homework_file in homework_dir.glob("*.json"):
            if homework_file.name != "index.json":
                homework = self._load_json(homework_file)
                if homework:
                    homework_list.append(homework)

        # Sort by created_at descending
        homework_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return homework_list

    # Submission operations
    async def create_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new submission. Returns created submission data."""
        course_id = submission_data.get("course_id")
        homework_id = submission_data.get("homework_id")
        student_id = submission_data.get("student_id")
        submission_id = submission_data.get("submission_id") or str(uuid.uuid4())[:8]
        submission_data["submission_id"] = submission_id
        submission_data["submitted_at"] = datetime.utcnow().isoformat()
        submission_data["updated_at"] = datetime.utcnow().isoformat()

        # Save submission data
        submissions_dir = self.courses_path / course_id / "homework" / "submissions"
        submissions_dir.mkdir(exist_ok=True)
        submission_file = submissions_dir / f"{student_id}.json"
        self._save_json(submission_file, submission_data)

        logger.info(f"Created submission: {submission_id}")
        return submission_data

    async def get_submission(self, hw_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """Get submission by homework ID and student ID. Returns None if not found."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                submissions_dir = course_dir / "homework" / "submissions"
                if submissions_dir.exists():
                    submission_file = submissions_dir / f"{student_id}.json"
                    if submission_file.exists():
                        submission = self._load_json(submission_file)
                        if submission and submission.get("hw_id") == hw_id:
                            return submission
        return None

    async def update_submission(self, submission_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update submission data. Returns updated submission data."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                submissions_dir = course_dir / "homework" / "submissions"
                if submissions_dir.exists():
                    for submission_file in submissions_dir.glob("*.json"):
                        submission = self._load_json(submission_file)
                        if submission and submission.get("submission_id") == str(submission_id):
                            submission.update(data)
                            submission["updated_at"] = datetime.utcnow().isoformat()
                            self._save_json(submission_file, submission)
                            return submission
        raise ValueError(f"Submission not found: {submission_id}")

    async def list_submissions(self, hw_id: str, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List submissions for a homework, optionally filtered by student."""
        # Search through all courses
        submissions = []
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                homework_dir = course_dir / "homework"
                if homework_dir.exists():
                    submissions_dir = homework_dir / "submissions"
                    if submissions_dir.exists():
                        for submission_file in submissions_dir.glob("*.json"):
                            submission = self._load_json(submission_file)
                            if submission:
                                if submission.get("hw_id") == hw_id:
                                    if student_id is None or submission.get("student_id") == student_id:
                                        submissions.append(submission)

        # Sort by submitted_at descending
        submissions.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
        return submissions

    # Teacher lesson library operations
    async def create_teacher_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new teacher lesson in personal library. Returns created lesson data."""
        teacher_id = lesson_data.get("teacher_id")
        lesson_id = lesson_data.get("lesson_id") or str(uuid.uuid4())[:8]
        lesson_data["lesson_id"] = lesson_id
        lesson_data["created_at"] = datetime.utcnow().isoformat()
        lesson_data["updated_at"] = datetime.utcnow().isoformat()

        # Create teacher lessons directory
        teacher_dir = self.base_path / "users" / "teacher" / teacher_id / "source" / "lessons"
        teacher_dir.mkdir(parents=True, exist_ok=True)

        # Save lesson data
        lesson_file = teacher_dir / f"{lesson_id}.json"
        self._save_json(lesson_file, lesson_data)

        # Save plan content if provided
        if "plan_content" in lesson_data:
            plan_file = teacher_dir / f"{lesson_id}_plan.md"
            plan_file.write_text(lesson_data["plan_content"], encoding="utf-8")

        logger.info(f"Created teacher lesson: {lesson_id}")
        return lesson_data

    async def get_teacher_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get teacher lesson by ID. Returns None if not found."""
        # Search through all teachers
        teachers_dir = self.base_path / "users" / "teacher"
        if not teachers_dir.exists():
            return None

        for teacher_dir in teachers_dir.iterdir():
            if teacher_dir.is_dir():
                lessons_dir = teacher_dir / "source" / "lessons"
                if lessons_dir.exists():
                    lesson_file = lessons_dir / f"{lesson_id}.json"
                    if lesson_file.exists():
                        lesson = self._load_json(lesson_file)
                        # Load plan content if exists
                        plan_file = lessons_dir / f"{lesson_id}_plan.md"
                        if plan_file.exists():
                            lesson["plan_content"] = plan_file.read_text(encoding="utf-8")
                        return lesson
        return None

    async def update_teacher_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update teacher lesson data. Returns updated lesson data."""
        # Search through all teachers
        teachers_dir = self.base_path / "users" / "teacher"
        if not teachers_dir.exists():
            raise ValueError(f"Teacher lesson not found: {lesson_id}")

        for teacher_dir in teachers_dir.iterdir():
            if teacher_dir.is_dir():
                lessons_dir = teacher_dir / "source" / "lessons"
                if lessons_dir.exists():
                    lesson_file = lessons_dir / f"{lesson_id}.json"
                    if lesson_file.exists():
                        lesson = self._load_json(lesson_file)
                        lesson.update(data)
                        lesson["updated_at"] = datetime.utcnow().isoformat()
                        self._save_json(lesson_file, lesson)

                        # Update plan content if provided
                        if "plan_content" in data:
                            plan_file = lessons_dir / f"{lesson_id}_plan.md"
                            plan_file.write_text(data["plan_content"], encoding="utf-8")

                        return lesson
        raise ValueError(f"Teacher lesson not found: {lesson_id}")

    async def delete_teacher_lesson(self, lesson_id: int) -> bool:
        """Delete teacher lesson. Returns True if successful."""
        # Search through all teachers
        teachers_dir = self.base_path / "users" / "teacher"
        if not teachers_dir.exists():
            return False

        for teacher_dir in teachers_dir.iterdir():
            if teacher_dir.is_dir():
                lessons_dir = teacher_dir / "source" / "lessons"
                if lessons_dir.exists():
                    lesson_file = lessons_dir / f"{lesson_id}.json"
                    if lesson_file.exists():
                        lesson_file.unlink()
                        # Also delete plan file if exists
                        plan_file = lessons_dir / f"{lesson_id}_plan.md"
                        if plan_file.exists():
                            plan_file.unlink()
                        return True
        return False

    async def list_teacher_lessons(self, teacher_id: str) -> List[Dict[str, Any]]:
        """List all lessons in a teacher's personal library."""
        lessons_dir = self.base_path / "users" / "teacher" / teacher_id / "source" / "lessons"
        if not lessons_dir.exists():
            return []

        lessons = []
        for lesson_file in lessons_dir.glob("*.json"):
            lesson = self._load_json(lesson_file)
            if lesson:
                lessons.append(lesson)

        # Sort by updated_at descending
        lessons.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return lessons

    # Notification operations
    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification. Returns created notification data."""
        user_id = notification_data.get("user_id")
        notification_id = notification_data.get("notification_id") or str(uuid.uuid4())[:8]
        notification_data["notification_id"] = notification_id
        notification_data["created_at"] = datetime.utcnow().isoformat()
        notification_data["is_read"] = False

        # Create notifications directory
        notifications_dir = self.base_path / "users" / notification_data.get("role", "student") / user_id / "notifications"
        notifications_dir.mkdir(parents=True, exist_ok=True)

        # Save notification data
        notification_file = notifications_dir / f"{notification_id}.json"
        self._save_json(notification_file, notification_data)

        return notification_data

    async def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get notification by ID. Returns None if not found."""
        # Search through all users
        users_dir = self.base_path / "users"
        if not users_dir.exists():
            return None

        for role_dir in users_dir.iterdir():
            if role_dir.is_dir():
                for user_dir in role_dir.iterdir():
                    if user_dir.is_dir():
                        notifications_dir = user_dir / "notifications"
                        if notifications_dir.exists():
                            notification_file = notifications_dir / f"{notification_id}.json"
                            if notification_file.exists():
                                return self._load_json(notification_file)
        return None

    async def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read. Returns True if successful."""
        notification = await self.get_notification(notification_id)
        if notification:
            notification["is_read"] = True
            notification["read_at"] = datetime.utcnow().isoformat()

            # Find and update the file
            users_dir = self.base_path / "users"
            if users_dir.exists():
                for role_dir in users_dir.iterdir():
                    if role_dir.is_dir():
                        for user_dir in role_dir.iterdir():
                            if user_dir.is_dir():
                                notifications_dir = user_dir / "notifications"
                                if notifications_dir.exists():
                                    notification_file = notifications_dir / f"{notification_id}.json"
                                    if notification_file.exists():
                                        self._save_json(notification_file, notification)
                                        return True
        return False

    async def list_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """List notifications for a user, optionally filtered by read status."""
        # Search through all roles for this user
        users_dir = self.base_path / "users"
        if not users_dir.exists():
            return []

        notifications = []
        for role_dir in users_dir.iterdir():
            if role_dir.is_dir():
                user_dir = role_dir / user_id
                if user_dir.exists():
                    notifications_dir = user_dir / "notifications"
                    if notifications_dir.exists():
                        for notification_file in notifications_dir.glob("*.json"):
                            notification = self._load_json(notification_file)
                            if notification:
                                if not unread_only or not notification.get("is_read", False):
                                    notifications.append(notification)

        # Sort by created_at descending
        notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return notifications

    # Learning progress operations
    async def update_learning_progress(self, user_id: str, lesson_id: int, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update learning progress for a user on a lesson. Returns progress data."""
        # Find the course this lesson belongs to
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                lessons_dir = course_dir / "lessons"
                if lessons_dir.exists():
                    for lesson_dir in lessons_dir.iterdir():
                        if lesson_dir.is_dir():
                            lesson_file = lesson_dir / "lesson.json"
                            lesson = self._load_json(lesson_file)
                            if lesson and lesson.get("lesson_id") == str(lesson_id):
                                # Found the lesson, now update progress
                                progress_dir = lesson_dir / "progress"
                                progress_dir.mkdir(exist_ok=True)
                                progress_file = progress_dir / f"{user_id}.json"

                                progress = self._load_json(progress_file) or {}
                                progress.update(progress_data)
                                progress["user_id"] = user_id
                                progress["lesson_id"] = str(lesson_id)
                                progress["updated_at"] = datetime.utcnow().isoformat()

                                self._save_json(progress_file, progress)
                                return progress

        raise ValueError(f"Lesson not found: {lesson_id}")

    async def get_learning_progress(self, user_id: str, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get learning progress for a user on a lesson. Returns None if not found."""
        # Find the course this lesson belongs to
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                lessons_dir = course_dir / "lessons"
                if lessons_dir.exists():
                    for lesson_dir in lessons_dir.iterdir():
                        if lesson_dir.is_dir():
                            lesson_file = lesson_dir / "lesson.json"
                            lesson = self._load_json(lesson_file)
                            if lesson and lesson.get("lesson_id") == str(lesson_id):
                                progress_dir = lesson_dir / "progress"
                                if progress_dir.exists():
                                    progress_file = progress_dir / f"{user_id}.json"
                                    if progress_file.exists():
                                        return self._load_json(progress_file)
        return None

    async def get_user_progress(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Get all learning progress for a user in a course."""
        course_dir = self.courses_path / course_id
        if not course_dir.exists():
            return []

        progress_list = []
        lessons_dir = course_dir / "lessons"
        if lessons_dir.exists():
            for lesson_dir in lessons_dir.iterdir():
                if lesson_dir.is_dir():
                    progress_dir = lesson_dir / "progress"
                    if progress_dir.exists():
                        progress_file = progress_dir / f"{user_id}.json"
                        if progress_file.exists():
                            progress = self._load_json(progress_file)
                            if progress:
                                progress_list.append(progress)

        return progress_list

    # Audit log operations
    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audit log entry. Returns created log data."""
        log_id = log_data.get("log_id") or str(uuid.uuid4())[:8]
        log_data["log_id"] = log_id
        log_data["created_at"] = datetime.utcnow().isoformat()

        # Create audit logs directory
        logs_dir = self.base_path / "audit_logs"
        logs_dir.mkdir(exist_ok=True)

        # Save to daily log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = logs_dir / f"{date_str}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

        return log_data

    async def list_audit_logs(self, user_id: Optional[str] = None, action: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List audit logs with optional filters."""
        logs_dir = self.base_path / "audit_logs"
        if not logs_dir.exists():
            return []

        logs = []
        for log_file in sorted(logs_dir.glob("*.jsonl"), reverse=True):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log = json.loads(line.strip())
                        if user_id and log.get("user_id") != user_id:
                            continue
                        if action and log.get("action") != action:
                            continue
                        logs.append(log)
                        if len(logs) >= limit:
                            return logs
                    except json.JSONDecodeError:
                        continue

        return logs

    # Resource operations
    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource. Returns created resource data."""
        course_id = resource_data.get("course_id")
        resource_id = resource_data.get("resource_id") or str(uuid.uuid4())[:8]
        resource_data["resource_id"] = resource_id
        resource_data["created_at"] = datetime.utcnow().isoformat()

        # Create resources directory
        resources_dir = self.courses_path / course_id / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)

        # Save resource data
        resource_file = resources_dir / f"{resource_id}.json"
        self._save_json(resource_file, resource_data)

        return resource_data

    async def get_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get resource by ID. Returns None if not found."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                resources_dir = course_dir / "resources"
                if resources_dir.exists():
                    resource_file = resources_dir / f"{resource_id}.json"
                    if resource_file.exists():
                        return self._load_json(resource_file)
        return None

    async def delete_resource(self, resource_id: int) -> bool:
        """Delete resource. Returns True if successful."""
        # Search through all courses
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                resources_dir = course_dir / "resources"
                if resources_dir.exists():
                    resource_file = resources_dir / f"{resource_id}.json"
                    if resource_file.exists():
                        resource_file.unlink()
                        return True
        return False

    async def list_resources(self, course_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List resources in a course, optionally filtered by type."""
        resources_dir = self.courses_path / course_id / "resources"
        if not resources_dir.exists():
            return []

        resources = []
        for resource_file in resources_dir.glob("*.json"):
            resource = self._load_json(resource_file)
            if resource:
                if resource_type is None or resource.get("resource_type") == resource_type:
                    resources.append(resource)

        # Sort by created_at descending
        resources.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return resources

    # Tutor profile operations
    async def get_tutor_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get tutor profile for a student. Returns None if not found."""
        profile_file = self.base_path / "users" / "student" / student_id / "tutor_profile.json"
        return self._load_json(profile_file)

    async def update_tutor_profile(self, student_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tutor profile for a student. Returns updated profile."""
        profile_file = self.base_path / "users" / "student" / student_id / "tutor_profile.json"
        profile = self._load_json(profile_file) or {
            "student_id": student_id,
            "knowledge_points": [],
            "error_records": [],
            "strategies": [],
            "total_submissions": 0,
        }
        profile.update(data)
        profile["student_id"] = student_id
        profile["last_active"] = datetime.utcnow().isoformat()
        self._save_json(profile_file, profile)
        return profile

    # Paper operations (for researcher paper management)
    async def create_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new paper. Returns created paper data."""
        papers_dir = self.base_path / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)

        # Generate paper ID
        paper_id = len(list(papers_dir.glob("*.json"))) + 1
        paper_data["id"] = paper_id
        paper_data["created_at"] = datetime.utcnow().isoformat()
        paper_data["updated_at"] = datetime.utcnow().isoformat()

        # Normalize keys to camelCase for frontend
        paper_record = {
            "id": paper_id,
            "title": paper_data.get("title", ""),
            "authors": paper_data.get("authors", ""),
            "abstract": paper_data.get("abstract", ""),
            "year": paper_data.get("year", 0),
            "doi": paper_data.get("doi", ""),
            "citationCount": paper_data.get("citation_count", 0),
            "venue": paper_data.get("venue", ""),
            "filePath": paper_data.get("file_path", ""),
            "fileName": paper_data.get("file_name", ""),
            "pageCount": paper_data.get("page_count", 0),
            "source": paper_data.get("source", "upload"),
            "sourceId": paper_data.get("source_id", ""),
            "pdfUrl": paper_data.get("pdf_url", ""),
            "userId": paper_data.get("user_id", ""),
            "isFavorite": False,
            "tags": [],
            "createdAt": paper_data["created_at"],
            "updatedAt": paper_data["updated_at"],
        }

        # Save paper data
        paper_file = papers_dir / f"{paper_id}.json"
        self._save_json(paper_file, paper_record)

        # Save full text separately (too large for main JSON)
        full_text = paper_data.get("full_text", "")
        if full_text:
            text_file = papers_dir / f"{paper_id}_text.txt"
            text_file.write_text(full_text, encoding="utf-8")

        logger.info(f"Created paper: {paper_id} - {paper_record['title']}")
        return paper_record

    async def get_paper(self, paper_id: int) -> Optional[Dict[str, Any]]:
        """Get paper by ID. Returns None if not found."""
        papers_dir = self.base_path / "papers"
        paper_file = papers_dir / f"{paper_id}.json"
        if not paper_file.exists():
            return None
        paper = self._load_json(paper_file)
        if paper:
            # Load full text from separate file if it exists
            text_file = papers_dir / f"{paper_id}_text.txt"
            if text_file.exists():
                try:
                    paper["fullText"] = text_file.read_text(encoding="utf-8")
                except Exception:
                    pass
        return paper

    async def list_papers(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List papers, optionally filtered by user."""
        papers_dir = self.base_path / "papers"
        if not papers_dir.exists():
            return []

        papers = []
        for paper_file in papers_dir.glob("*.json"):
            if paper_file.name.endswith("_text.json"):
                continue
            paper = self._load_json(paper_file)
            if paper:
                if user_id and paper.get("userId") != user_id:
                    continue
                papers.append(paper)

        # Sort by created_at descending
        papers.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return papers

    async def delete_paper(self, paper_id: int) -> bool:
        """Delete paper and its chunks. Returns True if successful."""
        papers_dir = self.base_path / "papers"
        paper_file = papers_dir / f"{paper_id}.json"

        if not paper_file.exists():
            return False

        # Delete main file
        paper_file.unlink()

        # Delete text file if exists
        text_file = papers_dir / f"{paper_id}_text.txt"
        if text_file.exists():
            text_file.unlink()

        # Delete chunks file if exists
        chunks_file = papers_dir / f"{paper_id}_chunks.json"
        if chunks_file.exists():
            chunks_file.unlink()

        logger.info(f"Deleted paper: {paper_id}")
        return True

    async def update_paper(self, paper_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update paper data. Returns updated paper data."""
        papers_dir = self.base_path / "papers"
        paper_file = papers_dir / f"{paper_id}.json"

        if not paper_file.exists():
            raise ValueError(f"Paper not found: {paper_id}")

        paper = self._load_json(paper_file)

        # Map snake_case keys to camelCase
        key_map = {
            "is_favorite": "isFavorite",
            "citation_count": "citationCount",
        }

        for key, value in data.items():
            camel_key = key_map.get(key, key)
            paper[camel_key] = value

        paper["updatedAt"] = datetime.utcnow().isoformat()
        self._save_json(paper_file, paper)

        logger.info(f"Updated paper: {paper_id}")
        return paper

    async def create_paper_chunks(self, paper_id: int, chunks: List[Dict[str, Any]]) -> int:
        """Create paper chunks. Returns count of chunks created."""
        papers_dir = self.base_path / "papers"
        chunks_file = papers_dir / f"{paper_id}_chunks.json"

        # Load existing chunks or create new list
        existing_chunks = self._load_json(chunks_file) or []

        # Add new chunks
        for chunk in chunks:
            chunk["paper_id"] = paper_id
            existing_chunks.append(chunk)

        self._save_json(chunks_file, existing_chunks)

        logger.info(f"Created {len(chunks)} chunks for paper {paper_id}")
        return len(chunks)

    async def get_paper_chunks(self, paper_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a paper."""
        papers_dir = self.base_path / "papers"
        chunks_file = papers_dir / f"{paper_id}_chunks.json"

        if not chunks_file.exists():
            return []

        return self._load_json(chunks_file) or []

    # Question bank operations
    def _get_qb_file(self, course_id: str) -> Path:
        """Get the question bank JSON file path for a course."""
        return self.courses_path / course_id / "question_bank.json"

    def _load_question_bank(self, course_id: str) -> List[Dict[str, Any]]:
        """Load all questions for a course."""
        qb_file = self._get_qb_file(course_id)
        return self._load_json(qb_file) or []

    def _save_question_bank(self, course_id: str, questions: List[Dict[str, Any]]) -> None:
        """Save all questions for a course."""
        qb_file = self._get_qb_file(course_id)
        qb_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_json(qb_file, questions)

    def _next_qb_id(self, course_id: str) -> int:
        """Get the next available question bank integer ID for a course."""
        questions = self._load_question_bank(course_id)
        if not questions:
            return 1
        return max(q.get("id", 0) for q in questions) + 1

    async def add_to_question_bank(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a question to the question bank."""
        course_id = question_data.get("course_id")
        if not course_id:
            raise ValueError("course_id is required")

        valid_fields = {'course_id', 'question_id', 'question_type', 'content', 'points',
                        'answer', 'options', 'explanation', 'tags', 'source', 'created_by'}
        data = {k: v for k, v in question_data.items() if k in valid_fields}

        if 'question_id' not in data:
            data['question_id'] = f"qb{uuid.uuid4().hex[:8]}"

        data['id'] = self._next_qb_id(course_id)
        data['created_at'] = datetime.utcnow().isoformat()

        questions = self._load_question_bank(course_id)
        questions.append(data)
        self._save_question_bank(course_id, questions)

        logger.info(f"Added question to bank: {data['question_id']}")
        return data

    async def get_question_bank(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Get question from bank by ID."""
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                questions = self._load_question_bank(course_dir.name)
                for q in questions:
                    if q.get("id") == question_id:
                        return q
        return None

    async def list_question_bank(self, course_id: str, question_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List questions in the bank for a course, optionally filtered by type."""
        questions = self._load_question_bank(course_id)
        if question_type:
            questions = [q for q in questions if q.get("question_type") == question_type]
        questions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return questions

    async def delete_from_question_bank(self, question_id: int) -> bool:
        """Delete question from bank."""
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                questions = self._load_question_bank(course_dir.name)
                for i, q in enumerate(questions):
                    if q.get("id") == question_id:
                        questions.pop(i)
                        self._save_question_bank(course_dir.name, questions)
                        return True
        return False

    async def update_question_bank(self, question_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a question in the bank."""
        updatable_fields = {'question_type', 'content', 'points', 'answer', 'options', 'explanation', 'tags'}
        for course_dir in self.courses_path.iterdir():
            if course_dir.is_dir():
                questions = self._load_question_bank(course_dir.name)
                for q in questions:
                    if q.get("id") == question_id:
                        for key, value in update_data.items():
                            if key in updatable_fields:
                                q[key] = value
                        self._save_question_bank(course_dir.name, questions)
                        logger.info(f"Updated question in bank: id={question_id}")
                        return q
        return None

    async def batch_add_to_question_bank(self, questions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add multiple questions to the question bank."""
        valid_fields = {'course_id', 'question_id', 'question_type', 'content', 'points',
                        'answer', 'options', 'explanation', 'tags', 'source', 'created_by'}
        results = []
        for q_data in questions_data:
            result = await self.add_to_question_bank(q_data)
            results.append(result)
        return results

    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check storage health. Returns health status dictionary."""
        try:
            # Check if base directory is writable
            test_file = self.base_path / ".health_check"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()

            return {
                "status": "healthy",
                "backend": "file",
                "base_path": str(self.base_path),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
