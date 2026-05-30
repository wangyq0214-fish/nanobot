"""
Abstract base class for storage implementations.

Defines the interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseStorage(ABC):
    """
    Abstract base class for storage backends.

    All storage implementations (file-based, database, etc.)
    must implement this interface.
    """

    # User operations
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user. Returns created user data."""
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username. Returns None if not found."""
        pass

    @abstractmethod
    async def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data. Returns updated user data."""
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user. Returns True if successful."""
        pass

    @abstractmethod
    async def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all users, optionally filtered by role."""
        pass

    # Course operations
    @abstractmethod
    async def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course. Returns created course data."""
        pass

    @abstractmethod
    async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def update_course(self, course_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update course data. Returns updated course data."""
        pass

    @abstractmethod
    async def delete_course(self, course_id: str) -> bool:
        """Delete course. Returns True if successful."""
        pass

    @abstractmethod
    async def list_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all courses, optionally filtered by user membership."""
        pass

    # Course member operations
    @abstractmethod
    async def add_course_member(self, course_id: str, user_id: str, role: str = "student") -> Dict[str, Any]:
        """Add a member to a course. Returns membership data."""
        pass

    @abstractmethod
    async def remove_course_member(self, course_id: str, user_id: str) -> bool:
        """Remove a member from a course. Returns True if successful."""
        pass

    @abstractmethod
    async def get_course_members(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all members of a course."""
        pass

    @abstractmethod
    async def is_course_member(self, course_id: str, user_id: str) -> bool:
        """Check if a user is a member of a course."""
        pass

    # Lesson operations
    @abstractmethod
    async def create_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lesson. Returns created lesson data."""
        pass

    @abstractmethod
    async def get_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get lesson by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def update_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update lesson data. Returns updated lesson data."""
        pass

    @abstractmethod
    async def delete_lesson(self, lesson_id: int) -> bool:
        """Delete lesson. Returns True if successful."""
        pass

    @abstractmethod
    async def list_lessons(self, course_id: str) -> List[Dict[str, Any]]:
        """List all lessons in a course."""
        pass

    # Homework operations
    @abstractmethod
    async def create_homework(self, homework_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new homework. Returns created homework data."""
        pass

    @abstractmethod
    async def get_homework(self, homework_id: int) -> Optional[Dict[str, Any]]:
        """Get homework by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def update_homework(self, homework_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update homework data. Returns updated homework data."""
        pass

    @abstractmethod
    async def delete_homework(self, homework_id: int) -> bool:
        """Delete homework. Returns True if successful."""
        pass

    @abstractmethod
    async def list_homework(self, course_id: str) -> List[Dict[str, Any]]:
        """List all homework in a course."""
        pass

    # Submission operations
    @abstractmethod
    async def create_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new submission. Returns created submission data."""
        pass

    @abstractmethod
    async def get_submission(self, submission_id: int) -> Optional[Dict[str, Any]]:
        """Get submission by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def update_submission(self, submission_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update submission data. Returns updated submission data."""
        pass

    @abstractmethod
    async def list_submissions(self, homework_id: int, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List submissions for a homework, optionally filtered by student."""
        pass

    # Teacher lesson library operations
    @abstractmethod
    async def create_teacher_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new teacher lesson in personal library. Returns created lesson data."""
        pass

    @abstractmethod
    async def get_teacher_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get teacher lesson by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def update_teacher_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update teacher lesson data. Returns updated lesson data."""
        pass

    @abstractmethod
    async def delete_teacher_lesson(self, lesson_id: int) -> bool:
        """Delete teacher lesson. Returns True if successful."""
        pass

    @abstractmethod
    async def list_teacher_lessons(self, teacher_id: str) -> List[Dict[str, Any]]:
        """List all lessons in a teacher's personal library."""
        pass

    # Notification operations
    @abstractmethod
    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification. Returns created notification data."""
        pass

    @abstractmethod
    async def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get notification by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read. Returns True if successful."""
        pass

    @abstractmethod
    async def list_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """List notifications for a user, optionally filtered by read status."""
        pass

    # Learning progress operations
    @abstractmethod
    async def update_learning_progress(self, user_id: str, lesson_id: int, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update learning progress for a user on a lesson. Returns progress data."""
        pass

    @abstractmethod
    async def get_learning_progress(self, user_id: str, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get learning progress for a user on a lesson. Returns None if not found."""
        pass

    @abstractmethod
    async def get_user_progress(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Get all learning progress for a user in a course."""
        pass

    # Audit log operations
    @abstractmethod
    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audit log entry. Returns created log data."""
        pass

    @abstractmethod
    async def list_audit_logs(self, user_id: Optional[str] = None, action: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List audit logs with optional filters."""
        pass

    # Resource operations
    @abstractmethod
    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource. Returns created resource data."""
        pass

    @abstractmethod
    async def get_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get resource by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def delete_resource(self, resource_id: int) -> bool:
        """Delete resource. Returns True if successful."""
        pass

    @abstractmethod
    async def list_resources(self, course_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List resources in a course, optionally filtered by type."""
        pass

    # Health check
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check storage health. Returns health status dictionary."""
        pass
