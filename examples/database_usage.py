#!/usr/bin/env python3
"""Example of using database storage in nanobot."""

import asyncio
from pathlib import Path

from loguru import logger


async def example_database_storage():
    """Example of using DatabaseStorage directly."""
    from nanobot.config.database import db_manager
    from nanobot.storage.database_storage import DatabaseStorage

    # Initialize database
    await db_manager.initialize()
    await db_manager.create_tables()

    # Get a session
    async for session in db_manager.get_session():
        storage = DatabaseStorage(session)

        # Create a user
        user = await storage.create_user("teacher", "teacher1", "张老师")
        logger.info("Created user: {}", user)

        # Create a course
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
        course = await storage.create_course(course_data)
        logger.info("Created course: {}", course)

        # Add a student to the course
        student = await storage.create_user("student", "student1", "李同学")
        member = await storage.add_member("course123", "student1", "李同学")
        logger.info("Added member: {}", member)

        # Create a lesson
        lesson_data = {
            "lessonId": "lesson1",
            "title": "Python简介",
            "description": "Python语言的历史和特点",
            "order": 1,
        }
        lesson = await storage.create_lesson(lesson_data, "course123")
        logger.info("Created lesson: {}", lesson)

        # Create homework
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
        homework = await storage.create_homework(homework_data, "course123")
        logger.info("Created homework: {}", homework)

        # Submit homework
        submission_data = {
            "hwId": homework.hw_id,
            "studentId": "student1",
            "answers": {
                "q1": "Python是解释型编程语言",
                "q2": "print('Hello World')",
            },
            "totalScore": 100,
        }
        submission = await storage.create_submission(submission_data, "course123")
        logger.info("Created submission: {}", submission)

        # Grade submission
        graded = await storage.grade_submission(
            homework.hw_id,
            "student1",
            90,
            {"q1": "正确", "q2": "基本正确，但缺少注释"},
            "teacher1",
        )
        logger.info("Graded submission: {}", graded)

    # Close database
    await db_manager.close()
    logger.info("Example completed!")


async def example_storage_wrapper():
    """Example of using StorageWrapper for gradual migration."""
    from nanobot.config.database import db_manager
    from nanobot.storage.storage_wrapper import StorageWrapper

    # Example 1: Use database storage
    logger.info("Example 1: Database storage")
    await db_manager.initialize()
    await db_manager.create_tables()

    async for session in db_manager.get_session():
        db_wrapper = StorageWrapper(session=session)

        # Create user using database
        user = await db_wrapper.create_user("teacher", "teacher2", "王老师")
        logger.info("Created user (database): {}", user)

        # Create course using database
        course_data = {
            "courseId": "course456",
            "courseName": "数据结构",
            "subject": "计算机科学",
            "grade": "大二",
            "teacherId": "teacher2",
            "teacherName": "王老师",
            "joinCode": "654321",
            "isPublic": True,
        }
        course = await db_wrapper.create_course(course_data)
        logger.info("Created course (database): {}", course)

    await db_manager.close()

    # Example 2: Use file-based storage
    logger.info("\nExample 2: File-based storage")
    file_wrapper = StorageWrapper(nanobot_dir=Path.home() / ".nanobot")

    # Create user using file storage
    user = await file_wrapper.create_user("teacher", "teacher3", "赵老师")
    logger.info("Created user (file): {}", user)

    # Create course using file storage
    course_data = {
        "courseId": "course789",
        "courseName": "算法设计",
        "subject": "计算机科学",
        "grade": "大三",
        "teacherId": "teacher3",
        "teacherName": "赵老师",
        "joinCode": "111222",
        "isPublic": False,
    }
    course = await file_wrapper.create_course(course_data)
    logger.info("Created course (file): {}", course)

    logger.info("\nStorage wrapper examples completed!")


async def main():
    """Run all examples."""
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")

    logger.info("=" * 60)
    logger.info("Database Storage Examples")
    logger.info("=" * 60)

    # Run examples
    logger.info("\n1. DatabaseStorage Example:")
    logger.info("-" * 40)
    await example_database_storage()

    logger.info("\n2. StorageWrapper Example:")
    logger.info("-" * 40)
    await example_storage_wrapper()

    logger.info("\n" + "=" * 60)
    logger.info("All examples completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
