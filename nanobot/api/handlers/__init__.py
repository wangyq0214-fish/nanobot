"""API handlers for courses, lessons, homework, grading, question bank, papers and search."""

from .courses import (
    handle_course_detail,
    handle_course_members,
    handle_courses_create,
    handle_courses_join,
    handle_courses_list,
)
from .grading import (
    handle_ai_generate_questions,
    handle_ai_grade,
    handle_ai_grade_question,
    handle_homework_delete,
    handle_homework_grade,
    handle_homework_publish,
)
from .homework import (
    handle_homework_create,
    handle_homework_detail,
    handle_homework_list,
    handle_homework_submissions,
    handle_homework_submit,
    handle_submission_detail,
)
from .lessons import handle_lesson_detail, handle_lessons_list
from .papers import (
    handle_delete_paper,
    handle_get_paper,
    handle_list_papers,
    handle_toggle_favorite,
    handle_update_tags,
    handle_upload_paper,
)
from .question_bank import (
    handle_question_bank_add,
    handle_question_bank_batch_add,
    handle_question_bank_delete,
    handle_question_bank_list,
    handle_question_bank_update,
)
from .search import handle_import_paper, handle_search_papers
from .tutor import handle_tutor_profile

__all__ = [
    "handle_courses_list",
    "handle_courses_create",
    "handle_courses_join",
    "handle_course_detail",
    "handle_course_members",
    "handle_lessons_list",
    "handle_lesson_detail",
    "handle_homework_list",
    "handle_homework_create",
    "handle_homework_detail",
    "handle_homework_submit",
    "handle_homework_submissions",
    "handle_submission_detail",
    "handle_homework_grade",
    "handle_ai_grade",
    "handle_ai_grade_question",
    "handle_homework_publish",
    "handle_homework_delete",
    "handle_ai_generate_questions",
    "handle_question_bank_list",
    "handle_question_bank_add",
    "handle_question_bank_batch_add",
    "handle_question_bank_delete",
    "handle_question_bank_update",
    "handle_tutor_profile",
    "handle_list_papers",
    "handle_upload_paper",
    "handle_get_paper",
    "handle_delete_paper",
    "handle_toggle_favorite",
    "handle_update_tags",
    "handle_search_papers",
    "handle_import_paper",
]
