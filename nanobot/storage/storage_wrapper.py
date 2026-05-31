"""
Storage wrapper for websocket.py integration.

Provides a unified interface that can use either file-based or database storage.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseStorage
from .factory import get_storage

logger = logging.getLogger(__name__)


class StorageWrapper:
    """
    Wrapper class for integrating storage with websocket.py.

    Provides methods that match the existing websocket.py interface
    while using the storage backend (file or database).
    """

    def __init__(self, storage: Optional[BaseStorage] = None):
        """Initialize with optional storage backend."""
        self._storage = storage

    def _normalize_course(self, course: Dict[str, Any]) -> Dict[str, Any]:
        """Convert snake_case to camelCase for frontend compatibility."""
        if not course:
            return course
        # Get member count from cache or default
        member_count = course.get("member_count", 0)
        if member_count == 0 and hasattr(self, '_member_count_cache'):
            member_count = self._member_count_cache.get(course.get("course_id", ""), 0)
        return {
            "courseId": course.get("course_id", ""),
            "courseName": course.get("course_name", ""),
            "subject": course.get("subject", ""),
            "grade": course.get("grade", ""),
            "description": course.get("description", ""),
            "teacherId": course.get("teacher_id", ""),
            "teacherRole": course.get("teacher_role", ""),
            "teacherName": course.get("teacher_name", ""),
            "joinCode": course.get("join_code", ""),
            "isPublic": course.get("is_public", False),
            "memberCount": member_count,
            "metadata": course.get("metadata", {}),
            "settings": course.get("settings", {}),
            "createdAt": course.get("created_at", ""),
            "updatedAt": course.get("updated_at", ""),
        }

    @staticmethod
    def _normalize_member(member: Dict[str, Any]) -> Dict[str, Any]:
        """Convert member data to camelCase for frontend compatibility."""
        if not member:
            return member
        return {
            "id": member.get("id"),
            "courseId": member.get("course_id", ""),
            "userId": member.get("user_id", ""),
            "userRole": member.get("user_role", ""),
            "displayName": member.get("display_name", ""),
            "metadata": member.get("metadata", {}),
            "joinedAt": member.get("joined_at", ""),
        }

    @staticmethod
    def _normalize_homework(hw: Dict[str, Any]) -> Dict[str, Any]:
        """Convert homework data to camelCase for frontend compatibility."""
        if not hw:
            return hw
        # Get questions from settings if available
        settings = hw.get("settings", {}) or {}
        questions = settings.get("questions", [])
        return {
            "hwId": hw.get("hw_id", ""),
            "courseId": hw.get("course_id", ""),
            "title": hw.get("title", ""),
            "description": hw.get("description", ""),
            "totalPoints": hw.get("total_points", 0),
            "deadline": hw.get("deadline", ""),
            "createdBy": hw.get("created_by", ""),
            "questions": questions,
            "settings": settings,
            "createdAt": hw.get("created_at", ""),
        }

    @property
    def storage(self) -> BaseStorage:
        """Get the storage backend."""
        if self._storage is None:
            self._storage = get_storage()
        return self._storage

    # User operations
    async def load_users(self) -> Dict[str, Any]:
        """Load all users. Returns dict keyed by 'role:user_id'."""
        users = await self.storage.list_users()
        result = {}
        for u in users:
            # Support both camelCase and snake_case keys
            role = u.get('role', '')
            user_id = u.get('user_id') or u.get('userId', '')
            if role and user_id:
                result[f"{role}:{user_id}"] = u
        return result

    async def save_users(self, data: Dict[str, Any]) -> None:
        """Save users data. Note: This is for compatibility only."""
        # In database mode, users are saved individually
        pass

    async def get_user(self, role: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by role and user_id."""
        return await self.storage.get_user(role, user_id)

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        return await self.storage.create_user(user_data)

    async def update_user(self, role: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data."""
        return await self.storage.update_user(role, user_id, data)

    # Course operations
    async def load_courses_index(self) -> Dict[str, Any]:
        """Load courses index."""
        courses = await self.storage.list_courses()
        return {c['course_id']: c for c in courses}

    async def save_courses_index(self, data: Dict[str, Any]) -> None:
        """Save courses index. Note: This is for compatibility only."""
        pass

    async def load_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Load course by ID."""
        return await self.storage.get_course(course_id)

    async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID. Alias for load_course."""
        course = await self.storage.get_course(course_id)
        return self._normalize_course(course) if course else None

    async def save_course(self, course_id: str, data: Dict[str, Any]) -> None:
        """Save course data."""
        await self.storage.update_course(course_id, data)

    async def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course."""
        return await self.storage.create_course(course_data)

    async def delete_course(self, course_id: str) -> bool:
        """Delete a course."""
        return await self.storage.delete_course(course_id)

    async def list_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all courses, optionally filtered by user membership."""
        courses = await self.storage.list_courses(user_id)
        return [self._normalize_course(c) for c in courses]

    async def get_teacher_courses(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get all courses for a specific teacher."""
        courses = await self.storage.get_teacher_courses(teacher_id)
        return [self._normalize_course(c) for c in courses]

    async def get_student_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all courses a student is enrolled in."""
        courses = await self.storage.get_student_courses(user_id)
        return [self._normalize_course(c) for c in courses]

    async def get_course_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        """Find a course by its join code."""
        course = await self.storage.get_course_by_join_code(join_code)
        return self._normalize_course(course) if course else None

    # Course member operations
    async def load_members(self, course_id: str) -> List[Dict[str, Any]]:
        """Load course members."""
        return await self.storage.get_course_members(course_id)

    async def save_members(self, course_id: str, members: List[Dict[str, Any]]) -> None:
        """Save course members. Note: This is for compatibility only."""
        pass

    async def add_member(self, course_id: str, user_id: str, role: str = "student") -> Dict[str, Any]:
        """Add a member to a course."""
        return await self.storage.add_course_member(course_id, user_id, role)

    async def add_course_member(self, course_id: str, user_id: str, role: str = "student", display_name: str = "") -> Dict[str, Any]:
        """Add a member to a course with display name."""
        return await self.storage.add_course_member(course_id, user_id, role, display_name)

    async def remove_member(self, course_id: str, user_id: str) -> bool:
        """Remove a member from a course."""
        return await self.storage.remove_course_member(course_id, user_id)

    async def is_member(self, course_id: str, user_id: str) -> bool:
        """Check if user is a member of course."""
        return await self.storage.is_course_member(course_id, user_id)

    async def is_course_member(self, course_id: str, user_id: str) -> bool:
        """Check if user is a member of course. Alias for is_member."""
        return await self.storage.is_course_member(course_id, user_id)

    async def get_course_members(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all members of a course."""
        members = await self.storage.get_course_members(course_id)
        return [self._normalize_member(m) for m in members]

    async def get_course_members_count(self, course_id: str) -> int:
        """Get the number of members in a course."""
        members = await self.storage.get_course_members(course_id)
        return len(members)

    # Lesson operations
    async def load_lessons(self, course_id: str) -> List[Dict[str, Any]]:
        """Load lessons for a course."""
        return await self.storage.list_lessons(course_id)

    async def get_course_lessons(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all lessons for a course."""
        return await self.storage.get_course_lessons(course_id)

    async def save_lesson(self, course_id: str, lesson_id: str, data: Dict[str, Any]) -> None:
        """Save lesson data."""
        await self.storage.update_lesson(int(lesson_id), data)

    async def create_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lesson."""
        return await self.storage.create_lesson(lesson_data)

    async def get_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get lesson by ID."""
        return await self.storage.get_lesson(lesson_id)

    async def delete_lesson(self, lesson_id: int) -> bool:
        """Delete a lesson."""
        return await self.storage.delete_lesson(lesson_id)

    # Homework operations
    async def load_homework(self, course_id: str, hw_id: str) -> Optional[Dict[str, Any]]:
        """Load homework by ID."""
        hw = await self.storage.get_homework(hw_id)
        return self._normalize_homework(hw) if hw else None

    async def get_homework(self, hw_id: str) -> Optional[Dict[str, Any]]:
        """Get homework by ID."""
        hw = await self.storage.get_homework(hw_id)
        return self._normalize_homework(hw) if hw else None

    async def list_homework(self, course_id: str) -> List[Dict[str, Any]]:
        """List homework for a course."""
        hw_list = await self.storage.list_homework(course_id)
        return [self._normalize_homework(hw) for hw in hw_list]

    async def get_course_homework(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all homework for a course."""
        hw_list = await self.storage.get_course_homework(course_id)
        return [self._normalize_homework(hw) for hw in hw_list]

    async def save_homework(self, course_id: str, hw_id: str, data: Dict[str, Any]) -> None:
        """Save homework data."""
        await self.storage.update_homework(hw_id, data)

    async def create_homework(self, homework_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new homework."""
        hw = await self.storage.create_homework(homework_data)
        return self._normalize_homework(hw)

    async def delete_homework(self, hw_id: str) -> bool:
        """Delete homework."""
        return await self.storage.delete_homework(hw_id)

    @staticmethod
    def _normalize_submission(sub: Dict[str, Any]) -> Dict[str, Any]:
        """Convert submission data to camelCase for frontend compatibility."""
        if not sub:
            return sub
        return {
            "id": sub.get("id"),
            "hwId": sub.get("hw_id", ""),
            "studentId": sub.get("student_id", ""),
            "studentName": sub.get("student_name", sub.get("student_id", "")),
            "studentRole": sub.get("student_role", ""),
            "courseId": sub.get("course_id", ""),
            "attemptNumber": sub.get("attempt_number", 1),
            "answers": sub.get("answers", {}),
            "status": sub.get("status", "submitted"),
            "score": sub.get("score", 0),
            "feedback": sub.get("feedback", {}),
            "submittedAt": sub.get("submitted_at", ""),
            "gradedAt": sub.get("graded_at", ""),
            "gradedBy": sub.get("graded_by", ""),
        }

    async def get_homework_submissions(self, hw_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a homework assignment."""
        subs = await self.storage.get_homework_submissions(hw_id)
        return [self._normalize_submission(s) for s in subs]

    # Submission operations
    async def get_submission(self, hw_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """Load submission by homework and student."""
        sub = await self.storage.get_submission(hw_id, student_id)
        return self._normalize_submission(sub) if sub else None

    async def list_submissions(self, hw_id: str, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List submissions for homework."""
        subs = await self.storage.list_submissions(hw_id, student_id)
        return [self._normalize_submission(s) for s in subs]

    async def create_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new submission."""
        sub = await self.storage.create_submission(submission_data)
        return self._normalize_submission(sub)

    async def create_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create submission data."""
        return await self.storage.create_submission(submission_data)

    async def update_submission(self, submission_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update submission data."""
        return await self.storage.update_submission(submission_id, data)

    # Teacher lesson library operations
    async def list_teacher_lessons(self, teacher_id: str) -> List[Dict[str, Any]]:
        """List teacher's personal lessons."""
        return await self.storage.list_teacher_lessons(teacher_id)

    async def create_teacher_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a teacher lesson."""
        return await self.storage.create_teacher_lesson(lesson_data)

    async def delete_teacher_lesson(self, lesson_id: int) -> bool:
        """Delete a teacher lesson."""
        return await self.storage.delete_teacher_lesson(lesson_id)

    # Notification operations
    async def list_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """List notifications for a user."""
        return await self.storage.list_notifications(user_id, unread_only)

    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a notification."""
        return await self.storage.create_notification(notification_data)

    async def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read."""
        return await self.storage.mark_notification_read(notification_id)

    # Resource operations
    async def list_resources(self, course_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List resources for a course."""
        return await self.storage.list_resources(course_id, resource_type)

    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a resource."""
        return await self.storage.create_resource(resource_data)

    async def delete_resource(self, resource_id: int) -> bool:
        """Delete a resource."""
        return await self.storage.delete_resource(resource_id)

    # Utility methods
    def generate_id(self) -> str:
        """Generate a unique ID."""
        import uuid
        return uuid.uuid4().hex[:12]

    def generate_join_code(self) -> str:
        """Generate a 6-digit join code."""
        import secrets
        return f"{secrets.randbelow(1_000_000):06d}"
