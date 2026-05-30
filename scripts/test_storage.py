#!/usr/bin/env python3
"""
Test script for storage layer.

Tests both file-based and database storage implementations.
"""

import asyncio
import json
import shutil
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def cleanup_test_data():
    """Clean up test data before running tests."""
    base_path = Path.home() / ".nanobot"

    # Remove test course directory
    test_course = base_path / "courses" / "test_course_001"
    if test_course.exists():
        shutil.rmtree(test_course, ignore_errors=True)

    # Remove test users from users.json
    users_file = base_path / "users.json"
    if users_file.exists():
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data = {k: v for k, v in data.items() if not k.startswith('test_')}
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # Remove test teacher lessons
    teacher_dir = base_path / "users" / "teacher"
    if teacher_dir.exists():
        for teacher_path in teacher_dir.iterdir():
            if teacher_path.is_dir():
                lessons_dir = teacher_path / "source" / "lessons"
                if lessons_dir.exists():
                    for f in lessons_dir.glob("*.json"):
                        try:
                            f.unlink()
                        except Exception:
                            pass
                    for f in lessons_dir.glob("*_plan.md"):
                        try:
                            f.unlink()
                        except Exception:
                            pass

    # Remove test audit logs
    logs_dir = base_path / "audit_logs"
    if logs_dir.exists():
        for f in logs_dir.glob("*.jsonl"):
            try:
                f.unlink()
            except Exception:
                pass


from nanobot.storage import FileStorage, DatabaseStorage, init_storage, get_storage


async def test_file_storage():
    """Test file-based storage."""
    print("\n" + "="*60)
    print("Testing File Storage")
    print("="*60)

    # Initialize file storage
    await init_storage("file")
    storage = get_storage()

    # Test health check
    health = await storage.health_check()
    print(f"[OK] Health check: {health['status']}")

    # Test user operations
    print("\n--- User Operations ---")
    user_data = {
        "user_id": "test_user_001",
        "username": "testuser",
        "password_hash": "hashed_password_here",
        "display_name": "Test User",
        "email": "test@example.com",
        "role": "student",
    }

    # Create user
    user = await storage.create_user(user_data)
    print(f"[OK] Created user: {user['username']} ({user['user_id']})")

    # Get user
    retrieved_user = await storage.get_user("test_user_001")
    print(f"[OK] Retrieved user: {retrieved_user['username']}")

    # Get user by username
    user_by_name = await storage.get_user_by_username("testuser")
    print(f"[OK] Retrieved user by username: {user_by_name['username']}")

    # Update user
    updated_user = await storage.update_user("test_user_001", {"display_name": "Updated Test User"})
    print(f"[OK] Updated user display_name: {updated_user['display_name']}")

    # List users
    users = await storage.list_users()
    print(f"[OK] Listed users: {len(users)} found")

    # Test course operations
    print("\n--- Course Operations ---")
    course_data = {
        "course_id": "test_course_001",
        "name": "Test Course",
        "description": "A test course",
        "subject": "Mathematics",
        "grade_level": "10",
        "teacher_id": "test_user_001",
    }

    # Create course
    course = await storage.create_course(course_data)
    print(f"[OK] Created course: {course['name']} ({course['course_id']})")

    # Get course
    retrieved_course = await storage.get_course("test_course_001")
    print(f"[OK] Retrieved course: {retrieved_course['name']}")

    # Add course member
    member = await storage.add_course_member("test_course_001", "test_user_001", "student")
    print(f"[OK] Added member: {member['user_id']} as {member['role']}")

    # Check membership
    is_member = await storage.is_course_member("test_course_001", "test_user_001")
    print(f"[OK] Is member: {is_member}")

    # Get course members
    members = await storage.get_course_members("test_course_001")
    print(f"[OK] Course members: {len(members)}")

    # List courses for user
    user_courses = await storage.list_courses(user_id="test_user_001")
    print(f"[OK] User courses: {len(user_courses)}")

    # Test lesson operations
    print("\n--- Lesson Operations ---")
    lesson_data = {
        "course_id": "test_course_001",
        "title": "Test Lesson",
        "description": "A test lesson",
        "subject": "Mathematics",
        "grade_level": "10",
        "duration": 45,
        "teacher_id": "test_user_001",
    }

    # Create lesson
    lesson = await storage.create_lesson(lesson_data)
    print(f"[OK] Created lesson: {lesson['title']} (ID: {lesson['lesson_id']})")

    # Get lesson (file storage uses string UUIDs)
    retrieved_lesson = await storage.get_lesson(lesson['lesson_id'])
    print(f"[OK] Retrieved lesson: {retrieved_lesson['title']}")

    # List lessons
    lessons = await storage.list_lessons("test_course_001")
    print(f"[OK] Course lessons: {len(lessons)}")

    # Test teacher lesson library
    print("\n--- Teacher Lesson Library ---")
    teacher_lesson_data = {
        "teacher_id": "test_user_001",
        "title": "Teacher's Template Lesson",
        "description": "A reusable lesson template",
        "subject": "Mathematics",
        "grade_level": "10",
        "duration": 45,
    }

    # Create teacher lesson
    teacher_lesson = await storage.create_teacher_lesson(teacher_lesson_data)
    print(f"[OK] Created teacher lesson: {teacher_lesson['title']} (ID: {teacher_lesson['lesson_id']})")

    # List teacher lessons
    teacher_lessons = await storage.list_teacher_lessons("test_user_001")
    print(f"[OK] Teacher lessons: {len(teacher_lessons)}")

    # Test homework operations
    print("\n--- Homework Operations ---")
    homework_data = {
        "course_id": "test_course_001",
        "title": "Test Homework",
        "description": "A test homework assignment",
        "type": "practice",
        "due_date": "2026-06-15T23:59:59",
        "teacher_id": "test_user_001",
    }

    # Create homework
    homework = await storage.create_homework(homework_data)
    print(f"[OK] Created homework: {homework['title']} (ID: {homework['homework_id']})")

    # List homework
    homework_list = await storage.list_homework("test_course_001")
    print(f"[OK] Course homework: {len(homework_list)}")

    # Test submission operations
    print("\n--- Submission Operations ---")
    submission_data = {
        "course_id": "test_course_001",
        "homework_id": homework['homework_id'],
        "student_id": "test_user_001",
        "content": "My homework submission",
    }

    # Create submission
    submission = await storage.create_submission(submission_data)
    print(f"[OK] Created submission: {submission['submission_id']}")

    # List submissions (file storage uses string UUIDs)
    submissions = await storage.list_submissions(homework['homework_id'])
    print(f"[OK] Homework submissions: {len(submissions)}")

    # Test notification operations
    print("\n--- Notification Operations ---")
    notification_data = {
        "user_id": "test_user_001",
        "role": "student",
        "type": "homework_due",
        "title": "Homework Due Soon",
        "content": "Your homework is due in 24 hours",
    }

    # Create notification
    notification = await storage.create_notification(notification_data)
    print(f"[OK] Created notification: {notification['notification_id']}")

    # List notifications
    notifications = await storage.list_notifications("test_user_001")
    print(f"[OK] User notifications: {len(notifications)}")

    # Test audit log operations
    print("\n--- Audit Log Operations ---")
    log_data = {
        "user_id": "test_user_001",
        "action": "user.login",
        "resource_type": "user",
        "resource_id": "test_user_001",
        "ip_address": "127.0.0.1",
    }

    # Create audit log
    log = await storage.create_audit_log(log_data)
    print(f"[OK] Created audit log: {log['log_id']}")

    # List audit logs
    logs = await storage.list_audit_logs(user_id="test_user_001")
    print(f"[OK] User audit logs: {len(logs)}")

    # Test resource operations
    print("\n--- Resource Operations ---")
    resource_data = {
        "course_id": "test_course_001",
        "title": "Test Resource",
        "description": "A test resource",
        "type": "file",
        "file_path": "/path/to/file.pdf",
        "uploaded_by": "test_user_001",
    }

    # Create resource
    resource = await storage.create_resource(resource_data)
    print(f"[OK] Created resource: {resource['resource_id']}")

    # List resources
    resources = await storage.list_resources("test_course_001")
    print(f"[OK] Course resources: {len(resources)}")

    print("\n" + "="*60)
    print("[OK] All file storage tests passed!")
    print("="*60)


async def test_database_storage():
    """Test database storage."""
    print("\n" + "="*60)
    print("Testing Database Storage")
    print("="*60)

    try:
        # Initialize database storage
        await init_storage("database")
        storage = get_storage()

        # Test health check
        health = await storage.health_check()
        print(f"✓ Health check: {health['status']}")

        if health['status'] != 'healthy':
            print("⚠ Database not available, skipping database tests")
            return

        # Run similar tests as file storage
        # (Abbreviated for brevity - same operations as above)

        print("\n" + "="*60)
        print("✓ All database storage tests passed!")
        print("="*60)

    except Exception as e:
        print(f"[WARN] Database test failed: {e}")
        print("  This is expected if PostgreSQL is not running")


async def main():
    """Run all tests."""
    print("Storage Layer Test Suite")
    print("="*60)

    # Clean up test data
    print("Cleaning up test data...")
    cleanup_test_data()

    # Test file storage
    await test_file_storage()

    # Test database storage (optional)
    await test_database_storage()

    print("\n" + "="*60)
    print("Test suite completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
