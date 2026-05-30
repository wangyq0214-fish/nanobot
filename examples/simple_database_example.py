#!/usr/bin/env python3
"""Simple example of using database in nanobot."""

import asyncio
from pathlib import Path

from loguru import logger


async def main():
    """Main example function."""
    from nanobot.config.database import db_manager
    from nanobot.storage.database_storage import DatabaseStorage

    # Initialize database
    logger.info("Initializing database...")
    await db_manager.initialize()
    await db_manager.create_tables()

    # Get a session
    async for session in db_manager.get_session():
        storage = DatabaseStorage(session)

        # Example 1: Create a teacher
        logger.info("\n1. Creating teacher...")
        teacher = await storage.create_user("teacher", "teacher1", "张老师")
        logger.info("Created teacher: {}", teacher)

        # Example 2: Create a course
        logger.info("\n2. Creating course...")
        course_data = {
            "courseId": "course001",
            "courseName": "Python编程基础",
            "subject": "计算机科学",
            "grade": "大一",
            "teacherId": "teacher1",
            "teacherName": "张老师",
            "joinCode": "123456",
            "isPublic": True,
        }
        course = await storage.create_course(course_data)
        logger.info("Created course: {}", course)

        # Example 3: Create students
        logger.info("\n3. Creating students...")
        student1 = await storage.create_user("student", "student1", "李同学")
        student2 = await storage.create_user("student", "student2", "王同学")
        logger.info("Created students: {} and {}", student1.display_name, student2.display_name)

        # Example 4: Add students to course
        logger.info("\n4. Adding students to course...")
        member1 = await storage.add_member("course001", "student1", "李同学")
        member2 = await storage.add_member("course001", "student2", "王同学")
        logger.info("Added {} and {} to course", member1.display_name, member2.display_name)

        # Example 5: Create a lesson
        logger.info("\n5. Creating lesson...")
        lesson_data = {
            "lessonId": "lesson001",
            "title": "Python简介",
            "description": "Python语言的历史和特点",
            "order": 1,
        }
        lesson = await storage.create_lesson(lesson_data, "course001")
        logger.info("Created lesson: {}", lesson)

        # Example 6: Create homework
        logger.info("\n6. Creating homework...")
        homework_data = {
            "title": "Python基础作业",
            "description": "完成以下编程题目",
            "totalPoints": 100,
            "deadline": "2026-06-15T23:59:59Z",
            "createdBy": "teacher1",
            "questions": [
                {
                    "id": "q1",
                    "type": "short_answer",
                    "content": "Python是什么类型的编程语言？",
                    "points": 20,
                },
                {
                    "id": "q2",
                    "type": "code",
                    "content": "写一个Hello World程序",
                    "points": 80,
                },
            ],
        }
        homework = await storage.create_homework(homework_data, "course001")
        logger.info("Created homework: {}", homework)

        # Example 7: Submit homework
        logger.info("\n7. Submitting homework...")
        submission_data = {
            "hwId": homework.hw_id,
            "studentId": "student1",
            "answers": {
                "q1": "Python是解释型编程语言",
                "q2": "print('Hello World')",
            },
            "totalScore": 100,
        }
        submission = await storage.create_submission(submission_data, "course001")
        logger.info("Created submission: {}", submission)

        # Example 8: Grade submission
        logger.info("\n8. Grading submission...")
        graded = await storage.grade_submission(
            homework.hw_id,
            "student1",
            90,
            {"q1": "正确", "q2": "基本正确，但缺少注释"},
            "teacher1",
        )
        logger.info("Graded submission: score={}", graded.score)

        # Example 9: Query data
        logger.info("\n9. Querying data...")

        # Get all courses for teacher
        courses = await storage.list_courses(role="teacher", user_id="teacher1")
        logger.info("Teacher has {} courses", len(courses))

        # Get course members
        members = await storage.get_members("course001")
        logger.info("Course has {} members", len(members))

        # Get course lessons
        lessons = await storage.list_lessons("course001")
        logger.info("Course has {} lessons", len(lessons))

        # Get course homework
        homework_list = await storage.list_homework("course001")
        logger.info("Course has {} homework assignments", len(homework_list))

        # Get submission
        sub = await storage.get_submission(homework.hw_id, "student1")
        logger.info("Submission status: {}", sub.status if sub else "not found")

    # Close database
    await db_manager.close()
    logger.info("\n✓ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
