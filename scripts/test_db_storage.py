#!/usr/bin/env python3
"""
Test database storage implementation.

Tests PostgreSQL storage with actual database operations.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanobot.storage import init_storage, get_storage
from nanobot.config.database import close_database


async def cleanup_test_data(storage):
    """Clean up test data from database."""
    print("Cleaning up test data...")
    try:
        # Delete test data in reverse order of dependencies
        await storage.delete_course("dbtc01")
        await storage.delete_user("db_test_user_001")
    except Exception:
        pass  # Ignore errors during cleanup


async def test_database_storage():
    """Test database storage with PostgreSQL."""
    print("\n" + "="*60)
    print("Testing Database Storage (PostgreSQL)")
    print("="*60)

    try:
        # Initialize database storage
        await init_storage("database")
        storage = get_storage()

        # Clean up any existing test data
        await cleanup_test_data(storage)

        # Test health check
        health = await storage.health_check()
        print(f"[OK] Health check: {health['status']}")
        if 'version' in health:
            print(f"     PostgreSQL version: {health['version']}")

        # Test user operations
        print("\n--- User Operations ---")
        user_data = {
            "user_id": "db_test_user_001",
            "role": "student",
            "password_hash": "$2b$12$hashed_password_here",
            "password_salt": "random_salt_value",
            "display_name": "DB Test User",
            "email": "dbtest@example.com",
        }

        # Create user
        user = await storage.create_user(user_data)
        print(f"[OK] Created user: {user['display_name']} ({user['user_id']})")

        # Get user
        retrieved_user = await storage.get_user("db_test_user_001")
        print(f"[OK] Retrieved user: {retrieved_user['display_name']}")

        # Update user
        updated_user = await storage.update_user("db_test_user_001", {"display_name": "Updated DB User"})
        print(f"[OK] Updated user display_name: {updated_user['display_name']}")

        # List users
        users = await storage.list_users()
        print(f"[OK] Listed users: {len(users)} found")

        # Test course operations
        print("\n--- Course Operations ---")
        course_data = {
            "course_id": "dbtc01",
            "course_name": "DB Test Course",
            "description": "A test course for database storage",
            "subject": "智慧农业",
            "grade": "大一",
            "teacher_id": "db_test_user_001",
            "teacher_role": "student",
            "teacher_name": "DB Test User",
            "join_code": "TEST01",
        }

        # Create course
        course = await storage.create_course(course_data)
        print(f"[OK] Created course: {course['course_name']} ({course['course_id']})")

        # Get course
        retrieved_course = await storage.get_course("dbtc01")
        print(f"[OK] Retrieved course: {retrieved_course['course_name']}")

        # Add course member
        member = await storage.add_course_member("dbtc01", "db_test_user_001", "student")
        print(f"[OK] Added member: {member['user_id']} as {member['user_role']}")

        # Check membership
        is_member = await storage.is_course_member("dbtc01", "db_test_user_001")
        print(f"[OK] Is member: {is_member}")

        # Get course members
        members = await storage.get_course_members("dbtc01")
        print(f"[OK] Course members: {len(members)}")

        # List courses for user
        user_courses = await storage.list_courses(user_id="db_test_user_001")
        print(f"[OK] User courses: {len(user_courses)}")

        # Test lesson operations
        print("\n--- Lesson Operations ---")
        lesson_data = {
            "course_id": "dbtc01",
            "title": "DB Test Lesson",
            "description": "A test lesson",
            "content_type": "markdown",
            "content": "# Test Lesson Content",
        }

        # Create lesson
        lesson = await storage.create_lesson(lesson_data)
        print(f"[OK] Created lesson: {lesson['title']} (ID: {lesson['id']})")

        # Get lesson
        retrieved_lesson = await storage.get_lesson(lesson['id'])
        print(f"[OK] Retrieved lesson: {retrieved_lesson['title']}")

        # List lessons
        lessons = await storage.list_lessons("dbtc01")
        print(f"[OK] Course lessons: {len(lessons)}")

        # Test teacher lesson library
        print("\n--- Teacher Lesson Library ---")
        teacher_lesson_data = {
            "lesson_id": "tl001",
            "teacher_id": "db_test_user_001",
            "teacher_role": "student",
            "title": "Teacher's Template Lesson",
            "description": "A reusable lesson template",
            "subject": "智慧农业",
            "grade": "大一",
        }

        # Create teacher lesson
        teacher_lesson = await storage.create_teacher_lesson(teacher_lesson_data)
        print(f"[OK] Created teacher lesson: {teacher_lesson['title']} (ID: {teacher_lesson['lesson_id']})")

        # List teacher lessons
        teacher_lessons = await storage.list_teacher_lessons("db_test_user_001")
        print(f"[OK] Teacher lessons: {len(teacher_lessons)}")

        # Test homework operations
        print("\n--- Homework Operations ---")
        from datetime import datetime, timedelta
        homework_data = {
            "hw_id": "hw001",
            "course_id": "dbtc01",
            "title": "DB Test Homework",
            "description": "A test homework assignment",
            "total_points": 100,
            "deadline": datetime.utcnow() + timedelta(days=7),
            "created_by": "db_test_user_001",
        }

        # Create homework
        homework = await storage.create_homework(homework_data)
        print(f"[OK] Created homework: {homework['title']} (ID: {homework['hw_id']})")

        # List homework
        homework_list = await storage.list_homework("dbtc01")
        print(f"[OK] Course homework: {len(homework_list)}")

        # Test submission operations
        print("\n--- Submission Operations ---")
        submission_data = {
            "hw_id": homework['hw_id'],
            "student_id": "db_test_user_001",
            "student_role": "student",
            "course_id": "dbtc01",
            "answers": {"q1": "My answer to question 1"},
        }

        # Create submission
        submission = await storage.create_submission(submission_data)
        print(f"[OK] Created submission: {submission['id']}")

        # List submissions
        submissions = await storage.list_submissions("hw001")
        print(f"[OK] Homework submissions: {len(submissions)}")

        # Test notification operations
        print("\n--- Notification Operations ---")
        notification_data = {
            "user_id": "db_test_user_001",
            "user_role": "student",
            "notification_type": "homework_deadline",
            "title": "Homework Due Soon",
            "content": "Your homework is due in 24 hours",
        }

        # Create notification
        notification = await storage.create_notification(notification_data)
        print(f"[OK] Created notification: {notification['id']}")

        # List notifications
        notifications = await storage.list_notifications("db_test_user_001")
        print(f"[OK] User notifications: {len(notifications)}")

        # Test audit log operations
        print("\n--- Audit Log Operations ---")
        log_data = {
            "table_name": "users",
            "record_id": "db_test_user_001",
            "action": "INSERT",
            "user_id": "db_test_user_001",
            "user_role": "student",
            "ip_address": "127.0.0.1",
        }

        # Create audit log
        log = await storage.create_audit_log(log_data)
        print(f"[OK] Created audit log: {log['id']}")

        # List audit logs
        logs = await storage.list_audit_logs(user_id="db_test_user_001")
        print(f"[OK] User audit logs: {len(logs)}")

        # Test resource operations
        print("\n--- Resource Operations ---")
        resource_data = {
            "course_id": "dbtc01",
            "title": "DB Test Resource",
            "description": "A test resource",
            "resource_type": "file",
            "file_path": "/path/to/file.pdf",
        }

        # Create resource
        resource = await storage.create_resource(resource_data)
        print(f"[OK] Created resource: {resource['id']}")

        # List resources
        resources = await storage.list_resources("dbtc01")
        print(f"[OK] Course resources: {len(resources)}")

        print("\n" + "="*60)
        print("[OK] All database storage tests passed!")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] Database test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database connection
        await close_database()


if __name__ == "__main__":
    asyncio.run(test_database_storage())
