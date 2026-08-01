"""
Database storage implementation.

Implements the BaseStorage interface using PostgreSQL with SQLAlchemy.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseStorage
from ..config.database import get_engine, get_session
from ..models import (
    User,
    Course,
    CourseMember,
    CourseLesson,
    TeacherLesson,
    Homework,
    Question,
    Submission,
    CourseResource,
    StudentCategory,
    StudentResource,
    LearningProgress,
    Notification,
    AuditLog,
    QuestionBank,
    Paper,
    PaperChunk,
    ResearchResult,
    ResearchArtifact,
    ResearchJob,
    ResearchProjectPaper,
    ResearchProjectResult,
    ResearchAttachment,
    ResearchAttachmentChunk,
    ResearchProject,
    LatexCompileRecord,
    LatexDraft,
    LatexDraftAttachment,
    LatexDraftVersion,
)
from ..models.base import Base

logger = logging.getLogger(__name__)


class DatabaseStorage(BaseStorage):
    """
    PostgreSQL database storage implementation.

    Uses SQLAlchemy async sessions for all database operations.
    """

    _research_workspace_tables_ensured = False

    async def _ensure_research_workspace_tables(self) -> None:
        """Create researcher workspace tables for databases initialized before this feature existed."""
        if self._research_workspace_tables_ensured:
            return

        tables = [
            ResearchProject.__table__,
            ResearchAttachment.__table__,
            ResearchAttachmentChunk.__table__,
            LatexDraft.__table__,
            LatexDraftVersion.__table__,
            LatexCompileRecord.__table__,
            LatexDraftAttachment.__table__,
            ResearchArtifact.__table__,
            ResearchProjectPaper.__table__,
            ResearchProjectResult.__table__,
            ResearchJob.__table__,
        ]
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        self._research_workspace_tables_ensured = True

    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user. Returns created user data."""
        async with get_session() as session:
            user = User(**user_data)
            session.add(user)
            await session.flush()
            await session.refresh(user)
            logger.info(f"Created user: {user.user_id}")
            return user.to_dict()

    async def get_user(self, role: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by role and user_id. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(
                    and_(User.role == role, User.user_id == user_id)
                )
            )
            user = result.scalar_one_or_none()
            return user.to_dict() if user else None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username. Returns None if not found."""
        # Note: Database schema doesn't have username column
        # This method is kept for interface compatibility
        return None

    async def update_user(self, role: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data. Returns updated user data."""
        async with get_session() as session:
            data["updated_at"] = datetime.utcnow()
            await session.execute(
                update(User).where(
                    and_(User.role == role, User.user_id == user_id)
                ).values(**data)
            )
            await session.flush()
            return await self.get_user(role, user_id)

    async def delete_user(self, role: str, user_id: str) -> bool:
        """Delete user. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(User).where(
                    and_(User.role == role, User.user_id == user_id)
                )
            )
            return result.rowcount > 0

    async def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all users, optionally filtered by role."""
        async with get_session() as session:
            query = select(User)
            if role:
                query = query.where(User.role == role)
            result = await session.execute(query)
            users = result.scalars().all()
            return [user.to_dict() for user in users]

    # Course operations
    async def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course. Returns created course data."""
        async with get_session() as session:
            course = Course(**course_data)
            session.add(course)
            await session.flush()
            await session.refresh(course)
            logger.info(f"Created course: {course.course_id}")
            return course.to_dict()

    async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(Course).where(Course.course_id == course_id)
            )
            course = result.scalar_one_or_none()
            return course.to_dict() if course else None

    async def update_course(self, course_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update course data. Returns updated course data."""
        async with get_session() as session:
            data["updated_at"] = datetime.utcnow()
            await session.execute(
                update(Course).where(Course.course_id == course_id).values(**data)
            )
            await session.flush()
            return await self.get_course(course_id)

    async def delete_course(self, course_id: str) -> bool:
        """Delete course. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(Course).where(Course.course_id == course_id)
            )
            return result.rowcount > 0

    async def list_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all courses, optionally filtered by user membership."""
        async with get_session() as session:
            if user_id:
                # Get courses where user is a member
                query = (
                    select(Course)
                    .join(CourseMember, Course.course_id == CourseMember.course_id)
                    .where(CourseMember.user_id == user_id)
                )
            else:
                query = select(Course)
            result = await session.execute(query)
            courses = result.scalars().all()
            return [course.to_dict() for course in courses]

    async def get_teacher_courses(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get all courses for a specific teacher."""
        async with get_session() as session:
            query = select(Course).where(Course.teacher_id == teacher_id)
            result = await session.execute(query)
            courses = result.scalars().all()
            return [course.to_dict() for course in courses]

    async def get_student_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all courses a student is enrolled in."""
        async with get_session() as session:
            query = (
                select(Course)
                .join(CourseMember, Course.course_id == CourseMember.course_id)
                .where(CourseMember.user_id == user_id)
            )
            result = await session.execute(query)
            courses = result.scalars().all()
            return [course.to_dict() for course in courses]

    async def get_course_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        """Find a course by its join code."""
        async with get_session() as session:
            result = await session.execute(
                select(Course).where(Course.join_code == join_code)
            )
            course = result.scalar_one_or_none()
            return course.to_dict() if course else None

    # Course member operations
    async def add_course_member(self, course_id: str, user_id: str, role: str = "student", display_name: str = "") -> Dict[str, Any]:
        """Add a member to a course. Returns membership data."""
        async with get_session() as session:
            # Get user display name if not provided
            if not display_name:
                user_result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                display_name = user.display_name if user else user_id

            member = CourseMember(
                course_id=course_id,
                user_id=user_id,
                user_role=role,
                display_name=display_name,
            )
            session.add(member)
            await session.flush()
            await session.refresh(member)
            logger.info(f"Added {user_id} to course {course_id} as {role}")
            return member.to_dict()

    async def remove_course_member(self, course_id: str, user_id: str) -> bool:
        """Remove a member from a course. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(CourseMember).where(
                    and_(
                        CourseMember.course_id == course_id,
                        CourseMember.user_id == user_id,
                    )
                )
            )
            return result.rowcount > 0

    async def get_course_members(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all members of a course."""
        async with get_session() as session:
            result = await session.execute(
                select(CourseMember).where(CourseMember.course_id == course_id)
            )
            members = result.scalars().all()
            return [member.to_dict() for member in members]

    async def is_course_member(self, course_id: str, user_id: str) -> bool:
        """Check if a user is a member of a course."""
        async with get_session() as session:
            result = await session.execute(
                select(CourseMember).where(
                    and_(
                        CourseMember.course_id == course_id,
                        CourseMember.user_id == user_id,
                    )
                )
            )
            return result.scalar_one_or_none() is not None

    # Lesson operations
    async def create_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lesson. Returns created lesson data."""
        async with get_session() as session:
            lesson = CourseLesson(**lesson_data)
            session.add(lesson)
            await session.flush()
            await session.refresh(lesson)
            logger.info(f"Created lesson: {lesson.id}")
            return lesson.to_dict()

    async def get_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get lesson by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(CourseLesson).where(CourseLesson.id == lesson_id)
            )
            lesson = result.scalar_one_or_none()
            return lesson.to_dict() if lesson else None

    async def update_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update lesson data. Returns updated lesson data."""
        async with get_session() as session:
            data["updated_at"] = datetime.utcnow()
            await session.execute(
                update(CourseLesson).where(CourseLesson.id == lesson_id).values(**data)
            )
            await session.flush()
            return await self.get_lesson(lesson_id)

    async def delete_lesson(self, lesson_id: int) -> bool:
        """Delete lesson. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(CourseLesson).where(CourseLesson.id == lesson_id)
            )
            return result.rowcount > 0

    async def list_lessons(self, course_id: str) -> List[Dict[str, Any]]:
        """List all lessons in a course."""
        async with get_session() as session:
            result = await session.execute(
                select(CourseLesson)
                .where(CourseLesson.course_id == course_id)
                .order_by(CourseLesson.order)
            )
            lessons = result.scalars().all()
            return [lesson.to_dict() for lesson in lessons]

    # Homework operations
    async def create_homework(self, homework_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new homework. Returns created homework data."""
        from datetime import datetime

        async with get_session() as session:
            # Only pass fields that Homework model supports
            valid_fields = {'hw_id', 'course_id', 'title', 'description', 'total_points', 'deadline', 'created_by', 'status', 'settings', 'created_at'}
            data = {k: v for k, v in homework_data.items() if k in valid_fields}

            # Convert deadline string to datetime if needed
            if 'deadline' in data and isinstance(data['deadline'], str):
                try:
                    data['deadline'] = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00')).replace(tzinfo=None)
                except:
                    data['deadline'] = None

            # Convert created_at string to datetime if needed
            if 'created_at' in data and isinstance(data['created_at'], str):
                try:
                    data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
                except:
                    data['created_at'] = datetime.utcnow()

            # Store questions in settings if provided
            if 'questions' in homework_data:
                settings = data.get('settings') or {}
                settings['questions'] = homework_data['questions']
                data['settings'] = settings

            homework = Homework(**data)
            session.add(homework)
            await session.flush()
            await session.refresh(homework)
            logger.info(f"Created homework: {homework.hw_id}")
            return homework.to_dict()

    async def get_homework(self, hw_id: str) -> Optional[Dict[str, Any]]:
        """Get homework by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(Homework).where(Homework.hw_id == hw_id)
            )
            homework = result.scalar_one_or_none()
            return homework.to_dict() if homework else None

    async def update_homework(self, hw_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update homework data. Returns updated homework data."""
        async with get_session() as session:
            await session.execute(
                update(Homework).where(Homework.hw_id == hw_id).values(**data)
            )
            await session.flush()
            return await self.get_homework(hw_id)

    async def delete_homework(self, hw_id: str) -> bool:
        """Delete homework and all related submissions. Returns True if successful."""
        async with get_session() as session:
            # Delete related submissions first
            await session.execute(
                delete(Submission).where(Submission.hw_id == hw_id)
            )
            result = await session.execute(
                delete(Homework).where(Homework.hw_id == hw_id)
            )
            return result.rowcount > 0

    async def list_homework(self, course_id: str) -> List[Dict[str, Any]]:
        """List all homework in a course."""
        async with get_session() as session:
            result = await session.execute(
                select(Homework)
                .where(Homework.course_id == course_id)
                .order_by(Homework.created_at.desc())
            )
            homework_list = result.scalars().all()
            return [hw.to_dict() for hw in homework_list]

    # Submission operations
    async def create_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new submission. Returns created submission data."""
        async with get_session() as session:
            # Filter to valid fields and convert date strings to datetime
            valid_fields = {'hw_id', 'student_id', 'student_role', 'course_id', 'attempt_number', 'answers', 'status', 'score', 'feedback', 'submitted_at', 'graded_at', 'graded_by'}
            data = {k: v for k, v in submission_data.items() if k in valid_fields}
            for date_field in ('submitted_at', 'graded_at'):
                if date_field in data and isinstance(data[date_field], str) and data[date_field]:
                    try:
                        data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00')).replace(tzinfo=None)
                    except Exception:
                        data[date_field] = None
            submission = Submission(**data)
            session.add(submission)
            await session.flush()
            await session.refresh(submission)
            logger.info(f"Created submission: {submission.id}")
            return submission.to_dict()

    async def get_submission(self, hw_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """Get submission by homework ID and student ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(Submission, CourseMember.display_name)
                .outerjoin(
                    CourseMember,
                    and_(
                        Submission.student_id == CourseMember.user_id,
                        Submission.course_id == CourseMember.course_id,
                    ),
                )
                .where(
                    and_(
                        Submission.hw_id == hw_id,
                        Submission.student_id == student_id,
                    )
                )
            )
            row = result.one_or_none()
            if not row:
                return None
            sub, display_name = row
            data = sub.to_dict()
            data["student_name"] = display_name or sub.student_id
            return data

    async def update_submission(self, submission_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update submission data. Returns updated submission data."""
        async with get_session() as session:
            # Use session.get() + direct attribute update to avoid SQL generation issues
            submission = await session.get(Submission, submission_id)
            if not submission:
                return None
            for key, value in data.items():
                if hasattr(submission, key):
                    setattr(submission, key, value)
            await session.flush()
            await session.refresh(submission)
            return submission.to_dict()

    async def list_submissions(self, hw_id: str, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List submissions for a homework, optionally filtered by student."""
        async with get_session() as session:
            # Join with course_members to get student display name
            query = (
                select(Submission, CourseMember.display_name)
                .outerjoin(
                    CourseMember,
                    and_(
                        Submission.student_id == CourseMember.user_id,
                        Submission.course_id == CourseMember.course_id,
                    ),
                )
                .where(Submission.hw_id == hw_id)
            )
            if student_id:
                query = query.where(Submission.student_id == student_id)
            query = query.order_by(Submission.submitted_at.desc())
            result = await session.execute(query)
            rows = result.all()

            submissions = []
            for sub, display_name in rows:
                data = sub.to_dict()
                data["student_name"] = display_name or sub.student_id
                submissions.append(data)
            return submissions

    # Teacher lesson library operations
    async def create_teacher_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new teacher lesson in personal library. Returns created lesson data."""
        async with get_session() as session:
            lesson = TeacherLesson(**lesson_data)
            session.add(lesson)
            await session.flush()
            await session.refresh(lesson)
            logger.info(f"Created teacher lesson: {lesson.lesson_id}")
            return lesson.to_dict()

    async def get_teacher_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get teacher lesson by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(TeacherLesson).where(TeacherLesson.lesson_id == str(lesson_id))
            )
            lesson = result.scalar_one_or_none()
            return lesson.to_dict() if lesson else None

    async def update_teacher_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update teacher lesson data. Returns updated lesson data."""
        async with get_session() as session:
            data["updated_at"] = datetime.utcnow()
            await session.execute(
                update(TeacherLesson).where(TeacherLesson.lesson_id == str(lesson_id)).values(**data)
            )
            await session.flush()
            return await self.get_teacher_lesson(lesson_id)

    async def delete_teacher_lesson(self, lesson_id: int) -> bool:
        """Delete teacher lesson. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(TeacherLesson).where(TeacherLesson.lesson_id == str(lesson_id))
            )
            return result.rowcount > 0

    async def list_teacher_lessons(self, teacher_id: str) -> List[Dict[str, Any]]:
        """List all lessons in a teacher's personal library."""
        async with get_session() as session:
            result = await session.execute(
                select(TeacherLesson)
                .where(TeacherLesson.teacher_id == teacher_id)
                .order_by(TeacherLesson.updated_at.desc())
            )
            lessons = result.scalars().all()
            return [lesson.to_dict() for lesson in lessons]

    # Notification operations
    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification. Returns created notification data."""
        async with get_session() as session:
            notification = Notification(**notification_data)
            session.add(notification)
            await session.flush()
            await session.refresh(notification)
            return notification.to_dict()

    async def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """Get notification by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            return notification.to_dict() if notification else None

    async def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read. Returns True if successful."""
        async with get_session() as session:
            await session.execute(
                update(Notification)
                .where(Notification.id == notification_id)
                .values(is_read=True)
            )
            return True

    async def list_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """List notifications for a user, optionally filtered by read status."""
        async with get_session() as session:
            query = select(Notification).where(Notification.user_id == user_id)
            if unread_only:
                query = query.where(Notification.is_read == False)
            query = query.order_by(Notification.created_at.desc())
            result = await session.execute(query)
            notifications = result.scalars().all()
            return [notif.to_dict() for notif in notifications]

    # Learning progress operations
    async def update_learning_progress(self, user_id: str, lesson_id: int, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update learning progress for a user on a lesson. Returns progress data."""
        async with get_session() as session:
            # Try to get existing progress
            result = await session.execute(
                select(LearningProgress).where(
                    and_(
                        LearningProgress.student_id == user_id,
                        LearningProgress.lesson_id == lesson_id,
                    )
                )
            )
            progress = result.scalar_one_or_none()

            if progress:
                # Update existing progress
                for key, value in progress_data.items():
                    setattr(progress, key, value)
                progress.last_accessed = datetime.utcnow()
            else:
                # Create new progress
                progress = LearningProgress(
                    student_id=user_id,
                    lesson_id=lesson_id,
                    **progress_data,
                )
                session.add(progress)

            await session.flush()
            await session.refresh(progress)
            return progress.to_dict()

    async def get_learning_progress(self, user_id: str, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Get learning progress for a user on a lesson. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(LearningProgress).where(
                    and_(
                        LearningProgress.student_id == user_id,
                        LearningProgress.lesson_id == lesson_id,
                    )
                )
            )
            progress = result.scalar_one_or_none()
            return progress.to_dict() if progress else None

    async def get_user_progress(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Get all learning progress for a user in a course."""
        async with get_session() as session:
            result = await session.execute(
                select(LearningProgress)
                .where(
                    and_(
                        LearningProgress.student_id == user_id,
                        LearningProgress.course_id == course_id,
                    )
                )
            )
            progress_list = result.scalars().all()
            return [progress.to_dict() for progress in progress_list]

    # Audit log operations
    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audit log entry. Returns created log data."""
        async with get_session() as session:
            log = AuditLog(**log_data)
            session.add(log)
            await session.flush()
            await session.refresh(log)
            return log.to_dict()

    async def list_audit_logs(self, user_id: Optional[str] = None, action: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List audit logs with optional filters."""
        async with get_session() as session:
            query = select(AuditLog)
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            if action:
                query = query.where(AuditLog.action == action)
            query = query.order_by(AuditLog.created_at.desc()).limit(limit)
            result = await session.execute(query)
            logs = result.scalars().all()
            return [log.to_dict() for log in logs]

    # Resource operations
    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource. Returns created resource data."""
        async with get_session() as session:
            resource = CourseResource(**resource_data)
            session.add(resource)
            await session.flush()
            await session.refresh(resource)
            return resource.to_dict()

    async def get_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get resource by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(CourseResource).where(CourseResource.id == resource_id)
            )
            resource = result.scalar_one_or_none()
            return resource.to_dict() if resource else None

    async def delete_resource(self, resource_id: int) -> bool:
        """Delete resource. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(CourseResource).where(CourseResource.id == resource_id)
            )
            return result.rowcount > 0

    async def list_resources(self, course_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List resources in a course, optionally filtered by type."""
        async with get_session() as session:
            query = select(CourseResource).where(CourseResource.course_id == course_id)
            if resource_type:
                query = query.where(CourseResource.resource_type == resource_type)
            query = query.order_by(CourseResource.created_at.desc())
            result = await session.execute(query)
            resources = result.scalars().all()
            return [resource.to_dict() for resource in resources]

    # Student resource operations
    async def create_student_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a student resource. Returns created resource data."""
        async with get_session() as session:
            resource = StudentResource(**resource_data)
            session.add(resource)
            await session.flush()
            await session.refresh(resource)
            return resource.to_dict()

    async def get_student_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get student resource by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(StudentResource).where(StudentResource.id == resource_id)
            )
            resource = result.scalar_one_or_none()
            return resource.to_dict() if resource else None

    async def delete_student_resource(self, resource_id: int, student_id: str) -> bool:
        """Delete student resource. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(StudentResource).where(
                    StudentResource.id == resource_id,
                    StudentResource.student_id == student_id
                )
            )
            return result.rowcount > 0

    async def list_student_resources(self, student_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List student resources, optionally filtered by type."""
        async with get_session() as session:
            query = select(StudentResource).where(StudentResource.student_id == student_id)
            if resource_type:
                query = query.where(StudentResource.resource_type == resource_type)
            query = query.order_by(StudentResource.created_at.desc())
            result = await session.execute(query)
            resources = result.scalars().all()
            return [resource.to_dict() for resource in resources]

    async def update_student_resource(self, resource_id: int, student_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update student resource. Returns updated resource or None."""
        async with get_session() as session:
            result = await session.execute(
                select(StudentResource).where(
                    StudentResource.id == resource_id,
                    StudentResource.student_id == student_id
                )
            )
            resource = result.scalar_one_or_none()

            if resource is None:
                return None

            for key, value in update_data.items():
                if hasattr(resource, key):
                    setattr(resource, key, value)

            await session.flush()
            await session.refresh(resource)
            return resource.to_dict()

    # Student category operations
    async def create_student_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a student category. Returns created category data."""
        async with get_session() as session:
            category = StudentCategory(**category_data)
            session.add(category)
            await session.flush()
            await session.refresh(category)
            return category.to_dict()

    async def get_student_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get student category by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(StudentCategory).where(StudentCategory.id == category_id)
            )
            category = result.scalar_one_or_none()
            return category.to_dict() if category else None

    async def delete_student_category(self, category_id: int, student_id: str) -> bool:
        """Delete student category. Returns True if successful."""
        async with get_session() as session:
            # First, set category_id to NULL for all resources in this category
            await session.execute(
                update(StudentResource)
                .where(StudentResource.category_id == category_id)
                .values(category_id=None)
            )
            # Then delete the category
            result = await session.execute(
                delete(StudentCategory).where(
                    StudentCategory.id == category_id,
                    StudentCategory.student_id == student_id
                )
            )
            return result.rowcount > 0

    async def list_student_categories(self, student_id: str) -> List[Dict[str, Any]]:
        """List student categories."""
        async with get_session() as session:
            query = select(StudentCategory).where(StudentCategory.student_id == student_id)
            query = query.order_by(StudentCategory.name)
            result = await session.execute(query)
            categories = result.scalars().all()
            return [category.to_dict() for category in categories]

    async def update_student_category(self, category_id: int, student_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update student category. Returns updated category or None."""
        async with get_session() as session:
            result = await session.execute(
                select(StudentCategory).where(
                    StudentCategory.id == category_id,
                    StudentCategory.student_id == student_id
                )
            )
            category = result.scalar_one_or_none()

            if category is None:
                return None

            for key, value in update_data.items():
                if hasattr(category, key):
                    setattr(category, key, value)

            await session.flush()
            await session.refresh(category)
            return category.to_dict()

    async def update_category_question_count(self, category_id: int) -> None:
        """Update the question count for a category."""
        async with get_session() as session:
            # Count questions in this category
            count_result = await session.execute(
                select(func.count(StudentResource.id))
                .where(StudentResource.category_id == category_id)
            )
            count = count_result.scalar() or 0

            # Update the category
            await session.execute(
                update(StudentCategory)
                .where(StudentCategory.id == category_id)
                .values(question_count=count)
            )

    # Tutor profile operations
    async def get_tutor_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get tutor profile for a student. Returns None if not found."""
        async with get_session() as session:
            from ..models.tutor_profile import TutorProfile
            result = await session.execute(
                select(TutorProfile).where(TutorProfile.student_id == student_id)
            )
            profile = result.scalar_one_or_none()
            return profile.to_dict() if profile else None

    async def update_tutor_profile(self, student_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tutor profile for a student. Returns updated profile."""
        async with get_session() as session:
            from ..models.tutor_profile import TutorProfile
            result = await session.execute(
                select(TutorProfile).where(TutorProfile.student_id == student_id)
            )
            profile = result.scalar_one_or_none()

            if profile is None:
                profile = TutorProfile(
                    student_id=student_id,
                    knowledge_points=data.get("knowledge_points", []),
                    error_records=data.get("error_records", []),
                    strategies=data.get("strategies", []),
                    total_submissions=data.get("total_submissions", 0),
                )
                session.add(profile)
            else:
                if "knowledge_points" in data:
                    profile.knowledge_points = data["knowledge_points"]
                if "error_records" in data:
                    profile.error_records = data["error_records"]
                if "strategies" in data:
                    profile.strategies = data["strategies"]
                if "total_submissions" in data:
                    profile.total_submissions = data["total_submissions"]
                if "recommended_questions" in data:
                    profile.recommended_questions = data["recommended_questions"]
                if "recommended_at" in data:
                    profile.recommended_at = data["recommended_at"]

            from datetime import datetime
            profile.last_active = datetime.utcnow()
            await session.flush()
            await session.refresh(profile)
            return profile.to_dict()

    # Paper operations (for researcher paper management)
    async def create_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new paper. Returns created paper data."""
        async with get_session() as session:
            # Filter to valid fields
            valid_fields = {
                'title', 'authors', 'abstract', 'year', 'doi', 'citation_count', 'venue',
                'file_path', 'file_name', 'page_count', 'full_text',
                'source', 'source_id', 'pdf_url', 'url',
                'ai_summary', 'user_id', 'user_role', 'is_favorite', 'tags', 'annotations',
            }
            data = {k: v for k, v in paper_data.items() if k in valid_fields}
            # Ensure JSON fields are serialized
            import json
            if 'tags' in data and isinstance(data['tags'], list):
                data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
            if 'annotations' in data and isinstance(data['annotations'], list):
                data['annotations'] = json.dumps(data['annotations'], ensure_ascii=False)

            paper = Paper(**data)
            session.add(paper)
            await session.flush()
            await session.refresh(paper)
            logger.info(f"Created paper: {paper.id} - {paper.title[:50]}")
            return paper.to_dict()

    async def get_paper(self, paper_id: int) -> Optional[Dict[str, Any]]:
        """Get paper by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(Paper).where(Paper.id == paper_id)
            )
            paper = result.scalar_one_or_none()
            return paper.to_dict() if paper else None

    async def list_papers(self, user_id: Optional[str] = None, user_role: str = "researcher") -> List[Dict[str, Any]]:
        """List papers, optionally filtered by user."""
        async with get_session() as session:
            query = select(Paper)
            if user_id:
                query = query.where(Paper.user_id == user_id)
                query = query.where(Paper.user_role == user_role)
            query = query.order_by(Paper.created_at.desc())
            result = await session.execute(query)
            papers = result.scalars().all()
            return [p.to_summary_dict() for p in papers]

    async def delete_paper(self, paper_id: int) -> bool:
        """Delete paper and its chunks. Returns True if successful."""
        async with get_session() as session:
            # Delete chunks first
            await session.execute(
                delete(PaperChunk).where(PaperChunk.paper_id == paper_id)
            )
            result = await session.execute(
                delete(Paper).where(Paper.id == paper_id)
            )
            return result.rowcount > 0

    async def update_paper(self, paper_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update paper data. Returns updated paper data."""
        async with get_session() as session:
            # Handle JSON field serialization
            import json
            if 'tags' in data and isinstance(data['tags'], list):
                data['tags'] = json.dumps(data['tags'], ensure_ascii=False)
            if 'annotations' in data and isinstance(data['annotations'], list):
                data['annotations'] = json.dumps(data['annotations'], ensure_ascii=False)
            data['updated_at'] = datetime.utcnow()
            await session.execute(
                update(Paper).where(Paper.id == paper_id).values(**data)
            )
            await session.flush()
            return await self.get_paper(paper_id)

    async def create_paper_chunks(self, paper_id: int, chunks: List[Dict[str, Any]]) -> int:
        """Create paper chunks. Returns count of chunks created."""
        async with get_session() as session:
            count = 0
            for chunk in chunks:
                pc = PaperChunk(
                    paper_id=paper_id,
                    chunk_index=chunk.get("chunk_index", 0),
                    page_number=chunk.get("page_number", 0),
                    content=chunk.get("content", ""),
                )
                session.add(pc)
                count += 1
            await session.flush()
            logger.info(f"Created {count} chunks for paper {paper_id}")
            return count

    async def get_paper_chunks(self, paper_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a paper."""
        async with get_session() as session:
            result = await session.execute(
                select(PaperChunk)
                .where(PaperChunk.paper_id == paper_id)
                .order_by(PaperChunk.chunk_index)
            )
            chunks = result.scalars().all()
            return [c.to_dict() for c in chunks]

    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check storage health. Returns health status dictionary."""
        try:
            from ..config.database import check_database_health
            return await check_database_health()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    # Question Bank operations
    async def add_to_question_bank(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a question to the question bank. Returns created question data."""
        async with get_session() as session:
            # Generate question_id if not provided
            if 'question_id' not in question_data:
                question_data['question_id'] = f"qb{uuid.uuid4().hex[:8]}"

            # Filter to valid fields
            valid_fields = {'course_id', 'question_id', 'question_type', 'content', 'points',
                          'answer', 'options', 'explanation', 'tags', 'source', 'created_by'}
            data = {k: v for k, v in question_data.items() if k in valid_fields}

            question = QuestionBank(**data)
            session.add(question)
            await session.flush()
            await session.refresh(question)
            logger.info(f"Added question to bank: {question.question_id}")
            return question.to_dict()

    async def get_question_bank(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Get question from bank by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(QuestionBank).where(QuestionBank.id == question_id)
            )
            question = result.scalar_one_or_none()
            return question.to_dict() if question else None

    async def list_question_bank(self, course_id: str, question_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List questions in the bank for a course, optionally filtered by type."""
        async with get_session() as session:
            query = select(QuestionBank).where(QuestionBank.course_id == course_id)
            if question_type:
                query = query.where(QuestionBank.question_type == question_type)
            query = query.order_by(QuestionBank.created_at.desc())
            result = await session.execute(query)
            questions = result.scalars().all()
            return [q.to_dict() for q in questions]

    async def delete_from_question_bank(self, question_id: int) -> bool:
        """Delete question from bank. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(QuestionBank).where(QuestionBank.id == question_id)
            )
            return result.rowcount > 0

    async def update_question_bank(self, question_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a question in the bank. Returns updated question or None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(QuestionBank).where(QuestionBank.id == question_id)
            )
            question = result.scalar_one_or_none()
            if not question:
                return None

            # Filter to updatable fields
            updatable_fields = {'question_type', 'content', 'points', 'answer', 'options', 'explanation', 'tags'}
            for key, value in update_data.items():
                if key in updatable_fields:
                    setattr(question, key, value)

            await session.flush()
            await session.refresh(question)
            logger.info(f"Updated question in bank: {question.question_id}")
            return question.to_dict()

    async def batch_add_to_question_bank(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add multiple questions to the question bank in a single session."""
        valid_fields = {'course_id', 'question_id', 'question_type', 'content', 'points',
                        'answer', 'options', 'explanation', 'tags', 'source', 'created_by'}
        results = []
        async with get_session() as session:
            for q in questions:
                # Generate question_id if not provided
                if 'question_id' not in q:
                    q['question_id'] = f"qb{uuid.uuid4().hex[:8]}"

                data = {k: v for k, v in q.items() if k in valid_fields}
                question = QuestionBank(**data)
                session.add(question)
                await session.flush()
                await session.refresh(question)
                logger.info(f"Added question to bank: {question.question_id}")
                results.append(question.to_dict())
        return results

    # Research result operations
    async def create_research_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new research result. Returns created result data."""
        async with get_session() as session:
            # Filter to valid fields
            valid_fields = {
                'user_id', 'user_role', 'title', 'content',
                'chat_id', 'session_title', 'source_message_id',
                'project_id', 'project_name', 'status', 'sections',
                'citations', 'attachments', 'resources', 'tags', 'metadata_'
            }
            filtered = {}
            for k, v in data.items():
                if k == 'metadata':
                    filtered['metadata_'] = v
                elif k in valid_fields:
                    filtered[k] = v

            result = ResearchResult(**filtered)
            session.add(result)
            await session.flush()
            await session.refresh(result)
            logger.info(f"Created research result: {result.id} for user {result.user_id}")
            return result.to_dict()

    async def get_research_result(self, result_id: int) -> Optional[Dict[str, Any]]:
        """Get research result by ID. Returns None if not found."""
        async with get_session() as session:
            result = await session.execute(
                select(ResearchResult).where(ResearchResult.id == result_id)
            )
            item = result.scalar_one_or_none()
            return item.to_dict() if item else None

    async def list_research_results(self, user_id: str, user_role: str = "researcher") -> List[Dict[str, Any]]:
        """List research results for a user."""
        async with get_session() as session:
            query = (
                select(ResearchResult)
                .where(
                    and_(
                        ResearchResult.user_id == user_id,
                        ResearchResult.user_role == user_role,
                    )
                )
                .order_by(ResearchResult.created_at.desc())
            )
            result = await session.execute(query)
            items = result.scalars().all()
            return [item.to_summary_dict() for item in items]

    async def delete_research_result(self, result_id: int) -> bool:
        """Delete research result. Returns True if successful."""
        async with get_session() as session:
            result = await session.execute(
                delete(ResearchResult).where(ResearchResult.id == result_id)
            )
            return result.rowcount > 0

    async def update_research_result(self, result_id: int, data: Dict[str, Any]) -> bool:
        """Update research result data. Returns True if successful."""
        async with get_session() as session:
            # Filter to updatable fields
            updatable_fields = {
                'title', 'content', 'tags', 'session_title',
                'source_message_id', 'project_id', 'project_name', 'status',
                'sections', 'citations', 'attachments', 'resources', 'metadata_',
            }
            if "metadata" in data:
                data = {**data, "metadata_": data["metadata"]}
            filtered = {k: v for k, v in data.items() if k in updatable_fields}
            if not filtered:
                return False

            result = await session.execute(
                update(ResearchResult)
                .where(ResearchResult.id == result_id)
                .values(**filtered)
            )
            return result.rowcount > 0

    # Research workspace operations
    async def create_research_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a researcher project."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            valid_fields = {'user_id', 'user_role', 'name', 'description', 'status', 'metadata_'}
            filtered = {}
            for k, v in data.items():
                if k == "metadata":
                    filtered["metadata_"] = v
                elif k in valid_fields:
                    filtered[k] = v
            project = ResearchProject(**filtered)
            session.add(project)
            await session.flush()
            await session.refresh(project)
            return project.to_dict()

    async def list_research_projects(self, user_id: str, user_role: str = "researcher") -> List[Dict[str, Any]]:
        """List researcher projects."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(ResearchProject)
                .where(and_(ResearchProject.user_id == user_id, ResearchProject.user_role == user_role))
                .order_by(ResearchProject.updated_at.desc())
            )
            return [item.to_dict() for item in result.scalars().all()]

    async def create_research_attachment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workspace attachment."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            valid_fields = {
                'user_id', 'user_role', 'project_id', 'job_id', 'chat_id', 'file_name',
                'file_type', 'file_path', 'parse_status', 'summary', 'metadata_'
            }
            filtered = {}
            for k, v in data.items():
                if k == "metadata":
                    filtered["metadata_"] = v
                elif k in valid_fields:
                    filtered[k] = v
            attachment = ResearchAttachment(**filtered)
            session.add(attachment)
            await session.flush()
            await session.refresh(attachment)
            return attachment.to_dict()

    async def get_research_attachment(self, attachment_id: int) -> Optional[Dict[str, Any]]:
        """Get a workspace attachment."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(ResearchAttachment).where(ResearchAttachment.id == attachment_id)
            )
            item = result.scalar_one_or_none()
            return item.to_dict() if item else None

    async def list_research_attachments(
        self,
        user_id: str,
        user_role: str = "researcher",
        chat_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List workspace attachments for a researcher."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            query = select(ResearchAttachment).where(
                and_(ResearchAttachment.user_id == user_id, ResearchAttachment.user_role == user_role)
            )
            if chat_id:
                query = query.where(ResearchAttachment.chat_id == chat_id)
            query = query.order_by(ResearchAttachment.created_at.desc())
            result = await session.execute(query)
            return [item.to_dict() for item in result.scalars().all()]

    async def create_research_attachment_chunks(self, attachment_id: int, chunks: List[Dict[str, Any]]) -> int:
        """Create chunks for a workspace attachment."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            count = 0
            for chunk in chunks:
                item = ResearchAttachmentChunk(
                    attachment_id=attachment_id,
                    chunk_index=chunk.get("chunk_index", chunk.get("chunkIndex", count)),
                    page_number=chunk.get("page_number", chunk.get("pageNumber", 0)),
                    sheet_name=chunk.get("sheet_name", chunk.get("sheetName", "")),
                    content=chunk.get("content", ""),
                    metadata_=chunk.get("metadata", {}),
                )
                session.add(item)
                count += 1
            return count

    async def get_research_attachment_chunks(self, attachment_id: int) -> List[Dict[str, Any]]:
        """Get chunks for a workspace attachment."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(ResearchAttachmentChunk)
                .where(ResearchAttachmentChunk.attachment_id == attachment_id)
                .order_by(ResearchAttachmentChunk.chunk_index)
            )
            return [item.to_dict() for item in result.scalars().all()]

    async def update_research_attachment(self, attachment_id: int, data: Dict[str, Any]) -> bool:
        await self._ensure_research_workspace_tables()
        aliases = {"parseStatus": "parse_status", "errorMessage": "error_message"}
        values = {aliases.get(key, key): value for key, value in data.items()}
        if "metadata" in values:
            values["metadata_"] = values.pop("metadata")
        allowed = {"parse_status", "summary", "metadata_", "project_id", "job_id"}
        values = {key: value for key, value in values.items() if key in allowed}
        async with get_session() as session:
            result = await session.execute(update(ResearchAttachment).where(ResearchAttachment.id == attachment_id).values(**values))
            return result.rowcount > 0

    async def delete_research_attachment(self, attachment_id: int) -> Optional[Dict[str, Any]]:
        """Delete an attachment and its extracted chunks."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(ResearchAttachment).where(ResearchAttachment.id == attachment_id)
            )
            attachment = result.scalar_one_or_none()
            if not attachment:
                return None
            value = attachment.to_dict()
            await session.execute(
                delete(ResearchAttachmentChunk).where(ResearchAttachmentChunk.attachment_id == attachment_id)
            )
            await session.delete(attachment)
            return value

    # Research artifact operations
    async def create_research_artifact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            valid_fields = {
                "user_id", "user_role", "project_id", "artifact_type", "title", "status",
                "source_refs", "content", "metadata_", "error_message",
            }
            filtered = {}
            for key, value in data.items():
                if key == "type":
                    filtered["artifact_type"] = value
                elif key == "metadata":
                    filtered["metadata_"] = value
                elif key in valid_fields:
                    filtered[key] = value
            artifact = ResearchArtifact(**filtered)
            session.add(artifact)
            await session.flush()
            await session.refresh(artifact)
            return artifact.to_dict()

    async def get_research_artifact(self, artifact_id: int) -> Optional[Dict[str, Any]]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(select(ResearchArtifact).where(ResearchArtifact.id == artifact_id))
            artifact = result.scalar_one_or_none()
            return artifact.to_dict() if artifact else None

    async def list_research_artifacts(self, user_id: str, user_role: str = "researcher") -> List[Dict[str, Any]]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(ResearchArtifact)
                .where(and_(ResearchArtifact.user_id == user_id, ResearchArtifact.user_role == user_role))
                .order_by(ResearchArtifact.updated_at.desc())
            )
            return [item.to_summary_dict() for item in result.scalars().all()]

    async def update_research_artifact(self, artifact_id: int, data: Dict[str, Any]) -> bool:
        await self._ensure_research_workspace_tables()
        updatable = {"title", "status", "source_refs", "content", "metadata_", "error_message"}
        if "metadata" in data:
            data = {**data, "metadata_": data["metadata"]}
        if "errorMessage" in data:
            data = {**data, "error_message": data["errorMessage"]}
        if "sourceRefs" in data:
            data = {**data, "source_refs": data["sourceRefs"]}
        filtered = {key: value for key, value in data.items() if key in updatable}
        if not filtered:
            return False
        async with get_session() as session:
            result = await session.execute(
                update(ResearchArtifact).where(ResearchArtifact.id == artifact_id).values(**filtered)
            )
            return result.rowcount > 0

    async def delete_research_artifact(self, artifact_id: int) -> Optional[Dict[str, Any]]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(select(ResearchArtifact).where(ResearchArtifact.id == artifact_id))
            artifact = result.scalar_one_or_none()
            if not artifact:
                return None
            value = artifact.to_dict()
            await session.delete(artifact)
            return value

    async def get_research_project(self, project_id: int, user_id: str, user_role: str = "researcher") -> Optional[Dict[str, Any]]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(select(ResearchProject).where(and_(
                ResearchProject.id == project_id,
                ResearchProject.user_id == user_id,
                ResearchProject.user_role == user_role,
            )))
            item = result.scalar_one_or_none()
            return item.to_dict() if item else None

    async def update_research_project(self, project_id: int, user_id: str, user_role: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        project = await self.get_research_project(project_id, user_id, user_role)
        if not project:
            return None
        filtered = {key: value for key, value in data.items() if key in {"name", "description", "status", "metadata_"}}
        if "metadata" in data:
            filtered["metadata_"] = data["metadata"]
        if filtered:
            async with get_session() as session:
                await session.execute(update(ResearchProject).where(ResearchProject.id == project_id).values(**filtered))
        return await self.get_research_project(project_id, user_id, user_role)

    async def delete_research_project(self, project_id: int, user_id: str, user_role: str = "researcher") -> bool:
        project = await self.get_research_project(project_id, user_id, user_role)
        if not project:
            return False
        async with get_session() as session:
            await session.execute(delete(ResearchProjectPaper).where(ResearchProjectPaper.project_id == project_id))
            await session.execute(delete(ResearchProjectResult).where(ResearchProjectResult.project_id == project_id))
            result = await session.execute(delete(ResearchProject).where(ResearchProject.id == project_id))
            return result.rowcount > 0

    async def get_research_project_links(self, project_id: int, user_id: str, user_role: str = "researcher") -> Optional[Dict[str, Any]]:
        if not await self.get_research_project(project_id, user_id, user_role):
            return None
        async with get_session() as session:
            papers = await session.execute(select(ResearchProjectPaper.paper_id).where(ResearchProjectPaper.project_id == project_id))
            results = await session.execute(select(ResearchProjectResult.result_id).where(ResearchProjectResult.project_id == project_id))
            return {"paperIds": list(papers.scalars().all()), "resultIds": list(results.scalars().all())}

    async def replace_research_project_links(self, project_id: int, user_id: str, user_role: str, paper_ids: list[int], result_ids: list[int]) -> Optional[Dict[str, Any]]:
        if not await self.get_research_project(project_id, user_id, user_role):
            return None
        async with get_session() as session:
            paper_query = select(Paper.id).where(and_(Paper.id.in_(paper_ids or [-1]), Paper.user_id == user_id, Paper.user_role == user_role))
            result_query = select(ResearchResult.id).where(and_(ResearchResult.id.in_(result_ids or [-1]), ResearchResult.user_id == user_id, ResearchResult.user_role == user_role))
            valid_papers = list((await session.execute(paper_query)).scalars().all())
            valid_results = list((await session.execute(result_query)).scalars().all())
            await session.execute(delete(ResearchProjectPaper).where(ResearchProjectPaper.project_id == project_id))
            await session.execute(delete(ResearchProjectResult).where(ResearchProjectResult.project_id == project_id))
            for paper_id in valid_papers:
                session.add(ResearchProjectPaper(project_id=project_id, paper_id=paper_id))
            for result_id in valid_results:
                session.add(ResearchProjectResult(project_id=project_id, result_id=result_id))
            return {"paperIds": valid_papers, "resultIds": valid_results}

    async def create_research_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            job = ResearchJob(**{key: value for key, value in data.items() if key in {
                "user_id", "user_role", "job_type", "status", "progress", "payload", "result",
                "error_message", "attempts", "max_attempts",
            }})
            session.add(job)
            await session.flush()
            await session.refresh(job)
            return job.to_dict()

    async def get_research_job(self, job_id: int, user_id: str, user_role: str = "researcher") -> Optional[Dict[str, Any]]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(select(ResearchJob).where(and_(
                ResearchJob.id == job_id, ResearchJob.user_id == user_id, ResearchJob.user_role == user_role,
            )))
            job = result.scalar_one_or_none()
            return job.to_dict() if job else None

    async def recover_research_jobs(self) -> None:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            await session.execute(update(ResearchJob).where(ResearchJob.status == "running").values(status="queued", started_at=None))

    async def claim_research_job(self) -> Optional[Dict[str, Any]]:
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(select(ResearchJob).where(
                ResearchJob.status == "queued", ResearchJob.attempts < ResearchJob.max_attempts,
            ).order_by(ResearchJob.created_at).with_for_update(skip_locked=True).limit(20))
            job = None
            for candidate in result.scalars().all():
                if candidate.job_type != "attachment_parse":
                    job = candidate
                    break
                running = await session.execute(select(func.count(ResearchJob.id)).where(and_(
                    ResearchJob.user_id == candidate.user_id,
                    ResearchJob.user_role == candidate.user_role,
                    ResearchJob.job_type == "attachment_parse",
                    ResearchJob.status == "running",
                )))
                if (running.scalar() or 0) < 2:
                    job = candidate
                    break
            if not job:
                return None
            job.status = "running"
            job.attempts += 1
            job.started_at = datetime.utcnow()
            job.progress = max(job.progress, 1)
            await session.flush()
            await session.refresh(job)
            return job.to_dict()

    async def update_research_job(self, job_id: int, data: Dict[str, Any]) -> bool:
        await self._ensure_research_workspace_tables()
        aliases = {"errorMessage": "error_message", "jobType": "job_type"}
        values = {aliases.get(key, key): value for key, value in data.items()}
        values = {key: value for key, value in values.items() if key in {
            "status", "progress", "result", "error_message", "started_at", "finished_at", "payload",
        }}
        async with get_session() as session:
            result = await session.execute(update(ResearchJob).where(ResearchJob.id == job_id).values(**values))
            return result.rowcount > 0

    async def retry_research_job(self, job_id: int, user_id: str, user_role: str = "researcher") -> Optional[Dict[str, Any]]:
        job = await self.get_research_job(job_id, user_id, user_role)
        if not job:
            return None
        async with get_session() as session:
            await session.execute(update(ResearchJob).where(ResearchJob.id == job_id).values(
                status="queued", progress=0, error_message="", finished_at=None,
            ))
        return await self.get_research_job(job_id, user_id, user_role)

    async def save_latex_draft(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a LaTeX draft and append a version when content changes."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            draft = None
            draft_id = data.get("id") or data.get("draft_id")
            user_id = data.get("user_id", "")
            user_role = data.get("user_role", "researcher")
            file_name = data.get("file_name", "")
            if draft_id:
                result = await session.execute(select(LatexDraft).where(LatexDraft.id == int(draft_id)))
                draft = result.scalar_one_or_none()
            if draft is None and user_id and file_name:
                result = await session.execute(
                    select(LatexDraft)
                    .where(
                        and_(
                            LatexDraft.user_id == user_id,
                            LatexDraft.user_role == user_role,
                            LatexDraft.file_name == file_name,
                        )
                    )
                    .order_by(LatexDraft.updated_at.desc())
                )
                draft = result.scalars().first()

            content = str(data.get("content", ""))
            metadata = data.get("metadata", {})
            if draft is None:
                draft = LatexDraft(
                    user_id=user_id,
                    user_role=user_role,
                    project_id=data.get("project_id"),
                    chat_id=data.get("chat_id", ""),
                    title=data.get("title") or file_name.replace(".tex", "") or "Untitled",
                    file_name=file_name or "document.tex",
                    content=content,
                    current_version=1,
                    status=data.get("status", "draft"),
                    tags=data.get("tags", []),
                    metadata_=metadata,
                )
                session.add(draft)
                await session.flush()
                version = LatexDraftVersion(
                    draft_id=draft.id,
                    version_number=1,
                    content=content,
                    change_source=data.get("change_source", "autosave"),
                    metadata_=metadata,
                )
                session.add(version)
            else:
                if draft.user_id != user_id or draft.user_role != user_role:
                    raise PermissionError("latex draft access denied")
                content_changed = draft.content != content
                if data.get("project_id") is not None:
                    draft.project_id = data.get("project_id")
                draft.chat_id = data.get("chat_id", draft.chat_id) or draft.chat_id
                draft.title = data.get("title") or draft.title
                draft.file_name = file_name or draft.file_name
                draft.content = content
                draft.status = data.get("status", draft.status)
                if isinstance(data.get("tags"), list):
                    draft.tags = data.get("tags")
                if isinstance(metadata, dict):
                    draft.metadata_ = metadata
                if content_changed:
                    draft.current_version = (draft.current_version or 1) + 1
                    version = LatexDraftVersion(
                        draft_id=draft.id,
                        version_number=draft.current_version,
                        content=content,
                        change_source=data.get("change_source", "autosave"),
                        metadata_=metadata if isinstance(metadata, dict) else {},
                    )
                    session.add(version)

            await self._sync_latex_draft_attachments(session, draft.id, data.get("attachment_ids"))
            await session.flush()
            await session.refresh(draft)
            return draft.to_dict()

    async def get_latex_draft(self, draft_id: int) -> Optional[Dict[str, Any]]:
        """Get a LaTeX draft by ID."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(select(LatexDraft).where(LatexDraft.id == draft_id))
            draft = result.scalar_one_or_none()
            return draft.to_dict() if draft else None

    async def list_latex_drafts(self, user_id: str, user_role: str = "researcher") -> List[Dict[str, Any]]:
        """List LaTeX drafts for a researcher."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(LatexDraft)
                .where(and_(LatexDraft.user_id == user_id, LatexDraft.user_role == user_role))
                .order_by(LatexDraft.updated_at.desc())
            )
            return [item.to_dict() for item in result.scalars().all()]

    async def list_latex_draft_versions(self, draft_id: int) -> List[Dict[str, Any]]:
        """List versions for a LaTeX draft."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            result = await session.execute(
                select(LatexDraftVersion)
                .where(LatexDraftVersion.draft_id == draft_id)
                .order_by(LatexDraftVersion.version_number.desc())
            )
            return [item.to_dict() for item in result.scalars().all()]

    async def create_latex_compile_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a compile record for a LaTeX draft."""
        await self._ensure_research_workspace_tables()
        async with get_session() as session:
            record = LatexCompileRecord(
                draft_id=int(data.get("draft_id") or data.get("draftId")),
                version_id=data.get("version_id") or data.get("versionId"),
                status=data.get("status", "pending"),
                engine=data.get("engine", "xelatex"),
                log=data.get("log", ""),
                output_name=data.get("output_name", data.get("outputName", "")),
                metadata_=data.get("metadata", {}),
            )
            session.add(record)
            await session.flush()
            await session.refresh(record)
            return record.to_dict()

    async def _sync_latex_draft_attachments(
        self,
        session: AsyncSession,
        draft_id: int,
        attachment_ids: Any,
    ) -> None:
        if attachment_ids is None:
            return
        normalized = []
        for item in attachment_ids if isinstance(attachment_ids, list) else []:
            try:
                normalized.append(int(item))
            except (TypeError, ValueError):
                continue
        await session.execute(delete(LatexDraftAttachment).where(LatexDraftAttachment.draft_id == draft_id))
        for attachment_id in dict.fromkeys(normalized):
            session.add(LatexDraftAttachment(draft_id=draft_id, attachment_id=attachment_id))
