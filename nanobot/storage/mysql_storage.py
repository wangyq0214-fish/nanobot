"""
MySQL database storage implementation.

Implements BaseStorage interface using MySQL with SQLAlchemy.
Mirrors database_storage.py but uses MySQL-compatible models and session.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_

from .base import BaseStorage
from ..config.mysql_database import get_mysql_engine, get_mysql_session
from ..models.mysql import (
    User, Course, CourseMember, CourseLesson, TeacherLesson,
    Homework, Question, Submission, CourseResource,
    StudentCategory, StudentResource, LearningProgress,
    Notification, AuditLog, QuestionBank, TutorProfile,
    Paper, PaperChunk, ResearchResult,
    ResearchProject, ResearchAttachment, ResearchAttachmentChunk,
    LatexDraft, LatexDraftVersion, LatexCompileRecord, LatexDraftAttachment,
)
from ..models.mysql.base import Base

logger = logging.getLogger(__name__)


class MySQLStorage(BaseStorage):
    """MySQL database storage implementation."""

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            user = User(**user_data)
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user.to_dict()

    async def get_user(self, role: str, user_id: str) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(
                select(User).where(and_(User.role == role, User.user_id == user_id))
            )
            user = result.scalar_one_or_none()
            return user.to_dict() if user else None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(User).where(User.display_name == username))
            user = result.scalar_one_or_none()
            return user.to_dict() if user else None

    async def update_user(self, role: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(
                update(User).where(and_(User.role == role, User.user_id == user_id)).values(**data)
            )
            await session.commit()
            return await self.get_user(role, user_id)

    async def delete_user(self, role: str, user_id: str) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(
                delete(User).where(and_(User.role == role, User.user_id == user_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            if role:
                result = await session.execute(select(User).where(User.role == role))
            else:
                result = await session.execute(select(User))
            return [u.to_dict() for u in result.scalars()]

    # --- Course ---
    async def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            course = Course(**course_data)
            session.add(course)
            await session.flush()
            await session.refresh(course)
            return course.to_dict()

    async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Course).where(Course.course_id == course_id))
            c = result.scalar_one_or_none()
            return c.to_dict() if c else None

    async def update_course(self, course_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(Course).where(Course.course_id == course_id).values(**data))
            await session.commit()
            return await self.get_course(course_id)

    async def delete_course(self, course_id: str) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(delete(Course).where(Course.course_id == course_id))
            await session.commit()
            return result.rowcount > 0

    async def list_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Course))
            return [c.to_dict() for c in result.scalars()]

    async def get_teacher_courses(self, teacher_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Course).where(Course.teacher_id == teacher_id))
            return [c.to_dict() for c in result.scalars()]

    async def get_student_courses(self, user_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(
                select(Course).join(CourseMember).where(CourseMember.user_id == user_id)
            )
            return [c.to_dict() for c in result.scalars()]

    async def get_course_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Course).where(Course.join_code == join_code))
            c = result.scalar_one_or_none()
            return c.to_dict() if c else None

    # --- Course member ---
    async def add_course_member(self, course_id: str, user_id: str, role: str = "student", display_name: str = "") -> Dict[str, Any]:
        async with get_mysql_session() as session:
            member = CourseMember(course_id=course_id, user_id=user_id, user_role=role, display_name=display_name)
            session.add(member)
            await session.flush()
            await session.refresh(member)
            return member.to_dict()

    async def remove_course_member(self, course_id: str, user_id: str) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(
                delete(CourseMember).where(and_(CourseMember.course_id == course_id, CourseMember.user_id == user_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def get_course_members(self, course_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(CourseMember).where(CourseMember.course_id == course_id))
            return [m.to_dict() for m in result.scalars()]

    async def is_course_member(self, course_id: str, user_id: str) -> bool:
        async with get_mysql_session() as session:
            result = await session.execute(
                select(CourseMember).where(and_(CourseMember.course_id == course_id, CourseMember.user_id == user_id))
            )
            return result.scalar_one_or_none() is not None

    # --- Lessons ---
    async def create_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            lesson = CourseLesson(**lesson_data)
            session.add(lesson)
            await session.flush()
            await session.refresh(lesson)
            return lesson.to_dict()

    async def get_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(CourseLesson).where(CourseLesson.lesson_id == lesson_id))
            l = result.scalar_one_or_none()
            return l.to_dict() if l else None

    async def update_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(CourseLesson).where(CourseLesson.lesson_id == lesson_id).values(**data))
            await session.commit()
            return await self.get_lesson(lesson_id)

    async def delete_lesson(self, lesson_id: int) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(delete(CourseLesson).where(CourseLesson.lesson_id == lesson_id))
            await session.commit()
            return result.rowcount > 0

    async def list_lessons(self, course_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(CourseLesson).where(CourseLesson.course_id == course_id))
            return [l.to_dict() for l in result.scalars()]

    # --- Homework ---
    async def create_homework(self, homework_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            hw = Homework(**homework_data)
            session.add(hw)
            await session.flush()
            await session.refresh(hw)
            return hw.to_dict()

    async def get_homework(self, hw_id: str) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Homework).where(Homework.hw_id == hw_id))
            h = result.scalar_one_or_none()
            return h.to_dict() if h else None

    async def update_homework(self, hw_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(Homework).where(Homework.hw_id == hw_id).values(**data))
            await session.commit()
            return await self.get_homework(hw_id)

    async def delete_homework(self, hw_id: str) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(delete(Homework).where(Homework.hw_id == hw_id))
            await session.commit()
            return result.rowcount > 0

    async def list_homework(self, course_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Homework).where(Homework.course_id == course_id))
            return [h.to_dict() for h in result.scalars()]

    # --- Submission ---
    async def create_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            sub = Submission(**submission_data)
            session.add(sub)
            await session.flush()
            await session.refresh(sub)
            return sub.to_dict()

    async def get_submission(self, hw_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(
                select(Submission).where(and_(Submission.hw_id == hw_id, Submission.student_id == student_id))
            )
            s = result.scalar_one_or_none()
            return s.to_dict() if s else None

    async def update_submission(self, submission_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(Submission).where(Submission.id == submission_id).values(**data))
            await session.commit()
            result = await session.execute(select(Submission).where(Submission.id == submission_id))
            return result.scalar_one().to_dict()

    async def list_submissions(self, hw_id: str, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            if student_id:
                result = await session.execute(
                    select(Submission).where(and_(Submission.hw_id == hw_id, Submission.student_id == student_id))
                )
            else:
                result = await session.execute(select(Submission).where(Submission.hw_id == hw_id))
            return [s.to_dict() for s in result.scalars()]

    # --- Teacher lesson ---
    async def create_teacher_lesson(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            tl = TeacherLesson(**lesson_data)
            session.add(tl)
            await session.flush()
            await session.refresh(tl)
            return tl.to_dict()

    async def get_teacher_lesson(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(TeacherLesson).where(TeacherLesson.lesson_id == lesson_id))
            l = result.scalar_one_or_none()
            return l.to_dict() if l else None

    async def update_teacher_lesson(self, lesson_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(TeacherLesson).where(TeacherLesson.lesson_id == lesson_id).values(**data))
            await session.commit()
            return await self.get_teacher_lesson(lesson_id)

    async def delete_teacher_lesson(self, lesson_id: int) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(delete(TeacherLesson).where(TeacherLesson.lesson_id == lesson_id))
            await session.commit()
            return result.rowcount > 0

    async def list_teacher_lessons(self, teacher_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(TeacherLesson).where(TeacherLesson.teacher_id == teacher_id))
            return [l.to_dict() for l in result.scalars()]

    # --- Notification ---
    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            n = Notification(**notification_data)
            session.add(n)
            await session.flush()
            await session.refresh(n)
            return n.to_dict()

    async def get_notification(self, notification_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(Notification).where(Notification.id == notification_id))
            n = result.scalar_one_or_none()
            return n.to_dict() if n else None

    async def mark_notification_read(self, notification_id: int) -> bool:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(Notification).where(Notification.id == notification_id).values(is_read=True))
            await session.commit()
            return True

    async def update_notification(self, notification_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(Notification).where(Notification.id == notification_id).values(**data))
            await session.commit()
            result = await session.execute(select(Notification).where(Notification.id == notification_id))
            n = result.scalar_one_or_none()
            return n.to_dict() if n else None

    async def list_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            if unread_only:
                result = await session.execute(
                    select(Notification).where(and_(Notification.user_id == user_id, Notification.is_read == False))
                )
            else:
                result = await session.execute(select(Notification).where(Notification.user_id == user_id))
            return [n.to_dict() for n in result.scalars()]

    # --- Progress ---
    async def update_learning_progress(self, user_id: str, lesson_id: int, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            result = await session.execute(
                select(LearningProgress).where(and_(LearningProgress.user_id == user_id, LearningProgress.lesson_id == lesson_id))
            )
            existing = result.scalar_one_or_none()
            if existing:
                await session.execute(
                    update(LearningProgress).where(LearningProgress.id == existing.id).values(**progress_data)
                )
            else:
                lp = LearningProgress(user_id=user_id, lesson_id=lesson_id, **progress_data)
                session.add(lp)
            await session.commit()
            return await self.get_learning_progress(user_id, lesson_id)

    async def get_learning_progress(self, user_id: str, lesson_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(
                select(LearningProgress).where(and_(LearningProgress.user_id == user_id, LearningProgress.lesson_id == lesson_id))
            )
            lp = result.scalar_one_or_none()
            return lp.to_dict() if lp else None

    async def get_user_progress(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(
                select(LearningProgress).where(and_(LearningProgress.user_id == user_id, LearningProgress.course_id == course_id))
            )
            return [p.to_dict() for p in result.scalars()]

    # --- Audit ---
    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            al = AuditLog(**log_data)
            session.add(al)
            await session.flush()
            await session.refresh(al)
            return al.to_dict()

    async def list_audit_logs(self, user_id: Optional[str] = None, action: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            q = select(AuditLog)
            if user_id:
                q = q.where(AuditLog.user_id == user_id)
            if action:
                q = q.where(AuditLog.action == action)
            q = q.order_by(AuditLog.created_at.desc()).limit(limit)
            result = await session.execute(q)
            return [a.to_dict() for a in result.scalars()]

    # --- Resource ---
    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            r = CourseResource(**resource_data)
            session.add(r)
            await session.flush()
            await session.refresh(r)
            return r.to_dict()

    async def get_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(CourseResource).where(CourseResource.id == resource_id))
            r = result.scalar_one_or_none()
            return r.to_dict() if r else None

    async def delete_resource(self, resource_id: int) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(delete(CourseResource).where(CourseResource.id == resource_id))
            await session.commit()
            return result.rowcount > 0

    async def list_resources(self, course_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            q = select(CourseResource).where(CourseResource.course_id == course_id)
            if resource_type:
                q = q.where(CourseResource.resource_type == resource_type)
            result = await session.execute(q)
            return [r.to_dict() for r in result.scalars()]

    # --- Student resource ---
    async def create_student_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            sr = StudentResource(**resource_data)
            session.add(sr)
            await session.flush()
            await session.refresh(sr)
            return sr.to_dict()

    async def get_student_resource(self, resource_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(StudentResource).where(StudentResource.id == resource_id))
            r = result.scalar_one_or_none()
            return r.to_dict() if r else None

    async def delete_student_resource(self, resource_id: int, student_id: str) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(
                delete(StudentResource).where(and_(StudentResource.id == resource_id, StudentResource.student_id == student_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def list_student_resources(self, student_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            q = select(StudentResource).where(StudentResource.student_id == student_id)
            if resource_type:
                q = q.where(StudentResource.resource_type == resource_type)
            result = await session.execute(q)
            return [r.to_dict() for r in result.scalars()]

    async def update_student_resource(self, resource_id: int, student_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(
                update(StudentResource).where(and_(StudentResource.id == resource_id, StudentResource.student_id == student_id)).values(**update_data)
            )
            await session.commit()
            return await self.get_student_resource(resource_id)

    # --- Student category ---
    async def create_student_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            sc = StudentCategory(**category_data)
            session.add(sc)
            await session.flush()
            await session.refresh(sc)
            return sc.to_dict()

    async def get_student_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(StudentCategory).where(StudentCategory.id == category_id))
            c = result.scalar_one_or_none()
            return c.to_dict() if c else None

    async def delete_student_category(self, category_id: int, student_id: str) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            result = await session.execute(
                delete(StudentCategory).where(and_(StudentCategory.id == category_id, StudentCategory.student_id == student_id))
            )
            await session.commit()
            return result.rowcount > 0

    async def list_student_categories(self, student_id: str) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            result = await session.execute(select(StudentCategory).where(StudentCategory.student_id == student_id))
            return [c.to_dict() for c in result.scalars()]

    async def update_student_category(self, category_id: int, student_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(
                update(StudentCategory).where(and_(StudentCategory.id == category_id, StudentCategory.student_id == student_id)).values(**update_data)
            )
            await session.commit()
            return await self.get_student_category(category_id)

    async def update_category_question_count(self, category_id: int) -> None:
        async with get_mysql_session() as session:
            result = await session.execute(select(StudentCategory).where(StudentCategory.id == category_id))
            cat = result.scalar_one_or_none()
            if cat:
                cat.question_count = (cat.question_count or 0) + 1
                await session.commit()

    # --- Question Bank ---
    async def list_question_bank(self, course_id: str = None, question_type: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_mysql_session() as session:
            q = select(QuestionBank)
            if course_id: q = q.where(QuestionBank.course_id == course_id)
            if question_type: q = q.where(QuestionBank.question_type == question_type)
            result = await session.execute(q)
            return [r.to_dict() for r in result.scalars()]

    async def add_to_question_bank(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_mysql_session() as session:
            import uuid
            data.setdefault("question_id", f"q{uuid.uuid4().hex[:10]}")
            qb = QuestionBank(**data)
            session.add(qb)
            await session.flush(); await session.refresh(qb)
            return qb.to_dict()

    async def batch_add_to_question_bank(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for q in questions: results.append(await self.add_to_question_bank(q))
        return results

    async def delete_from_question_bank(self, qid: int) -> bool:
        from sqlalchemy import delete
        async with get_mysql_session() as session:
            r = await session.execute(delete(QuestionBank).where(QuestionBank.id == qid))
            await session.commit()
            return r.rowcount > 0

    async def update_question_bank(self, qid: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from sqlalchemy import update
        async with get_mysql_session() as session:
            await session.execute(update(QuestionBank).where(QuestionBank.id == qid).values(**data))
            await session.commit()
            r = await session.execute(select(QuestionBank).where(QuestionBank.id == qid))
            qb = r.scalar_one_or_none()
            return qb.to_dict() if qb else None

    async def get_question_bank(self, qid: int) -> Optional[Dict[str, Any]]:
        async with get_mysql_session() as session:
            r = await session.execute(select(QuestionBank).where(QuestionBank.id == qid))
            qb = r.scalar_one_or_none()
            return qb.to_dict() if qb else None

    # --- Exam ---
    async def list_exams(self, course_id: str) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        engine = get_mysql_engine()
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT * FROM exams WHERE course_id=:c"), {"c": course_id})
            cols = r.keys()
            results = []
            for row in r.fetchall():
                d = dict(zip(cols, row))
                for k, v in d.items():
                    if hasattr(v, 'isoformat'): d[k] = v.isoformat()
                results.append(d)
            return results

    async def create_exam(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        engine = get_mysql_engine()
        async with engine.begin() as conn:
            await conn.execute(text(
                "INSERT INTO exams (exam_id,course_id,title,description,start_time,end_time,duration,total_points,status,created_by,created_at,updated_at) VALUES (:e,:c,:t,:d,:s,:en,:dur,:p,:st,:cb,NOW(),NOW())"
            ), data)
        return data

    # --- Health ---
    async def health_check(self) -> Dict[str, Any]:
        try:
            from sqlalchemy import text
            engine = get_mysql_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                pool = engine.pool
                return {
                    "status": "healthy",
                    "version": version,
                    "pool": {"size": pool.size(), "checked_in": pool.checkedin(), "overflow": pool.overflow()},
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
