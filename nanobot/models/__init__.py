"""
Database models for nanobot.

SQLAlchemy ORM models for PostgreSQL storage.
"""

from .audit import AuditLog
from .base import Base
from .course import Course, CourseMember
from .homework import Homework, Question, Submission
from .lesson import CourseLesson, TeacherLesson
from .notification import Notification
from .paper import Paper, PaperChunk
from .progress import LearningProgress
from .question_bank import QuestionBank
from .research_result import ResearchResult
from .research_artifact import ResearchArtifact
from .research_stability import ResearchJob, ResearchProjectPaper, ResearchProjectResult
from .research_workspace import (
    LatexCompileRecord,
    LatexDraft,
    LatexDraftAttachment,
    LatexDraftVersion,
    ResearchAttachment,
    ResearchAttachmentChunk,
    ResearchProject,
)
from .resource import CourseResource
from .student_category import StudentCategory
from .student_resource import StudentResource
from .tutor_profile import TutorProfile
from .user import User

__all__ = [
    "Base",
    "User",
    "Course",
    "CourseMember",
    "CourseLesson",
    "TeacherLesson",
    "Homework",
    "Question",
    "Submission",
    "CourseResource",
    "StudentCategory",
    "StudentResource",
    "LearningProgress",
    "Notification",
    "AuditLog",
    "QuestionBank",
    "TutorProfile",
    "Paper",
    "PaperChunk",
    "ResearchResult",
    "ResearchArtifact",
    "ResearchJob",
    "ResearchProjectPaper",
    "ResearchProjectResult",
    "ResearchProject",
    "ResearchAttachment",
    "ResearchAttachmentChunk",
    "LatexDraft",
    "LatexDraftVersion",
    "LatexCompileRecord",
    "LatexDraftAttachment",
]
