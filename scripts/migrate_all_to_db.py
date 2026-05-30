#!/usr/bin/env python3
"""
Migrate all data from local files to PostgreSQL database.

Migrates:
- Users
- Courses (with members)
- Homework
- Submissions
- Lessons
- Resources

Usage:
    python scripts/migrate_all_to_db.py
"""

import asyncio
import hashlib
import json
import secrets
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_datetime(dt_str):
    """Parse datetime string to datetime object (timezone-naive)."""
    if not dt_str:
        return datetime.utcnow()
    try:
        # Try ISO format
        if 'T' in dt_str:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            # Remove timezone info for database compatibility
            return dt.replace(tzinfo=None)
        return datetime.fromisoformat(dt_str)
    except:
        return datetime.utcnow()


async def migrate_all():
    """Migrate all data from files to database."""
    from nanobot.storage.database_storage import DatabaseStorage
    from nanobot.config.database import init_database, DatabaseConfig

    base_path = Path.home() / ".nanobot"
    courses_path = base_path / "courses"

    # Initialize database
    try:
        db_config = DatabaseConfig()
        await init_database(db_config)
        storage = DatabaseStorage()
        print("[OK] Database connected")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return

    stats = {
        "users": {"migrated": 0, "skipped": 0, "errors": 0},
        "courses": {"migrated": 0, "skipped": 0, "errors": 0},
        "members": {"migrated": 0, "skipped": 0, "errors": 0},
        "lessons": {"migrated": 0, "skipped": 0, "errors": 0},
        "homework": {"migrated": 0, "skipped": 0, "errors": 0},
        "submissions": {"migrated": 0, "skipped": 0, "errors": 0},
        "resources": {"migrated": 0, "skipped": 0, "errors": 0},
    }

    # ===== 1. Migrate Users =====
    print("\n" + "=" * 50)
    print("Migrating Users")
    print("=" * 50)

    users_file = base_path / "users.json"
    if users_file.exists():
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)

        for key, user_data in users.items():
            try:
                parts = key.split(":", 1)
                if len(parts) != 2:
                    print(f"[WARN] Invalid key: {key}")
                    stats["users"]["errors"] += 1
                    continue

                role, user_id = parts

                # Check if exists
                existing = await storage.get_user(role, user_id)
                if existing:
                    stats["users"]["skipped"] += 1
                    continue

                # Prepare user data
                db_user = {
                    "role": role,
                    "user_id": user_id,
                    "display_name": user_data.get("displayName") or user_data.get("display_name", user_id),
                    "email": user_data.get("email", ""),
                    "password_hash": user_data.get("password_hash", ""),
                    "password_salt": user_data.get("password_salt", ""),
                    "profile": user_data.get("profile", {}),
                    "settings": user_data.get("settings", {}),
                }

                # Set default password if none
                if not db_user["password_hash"]:
                    salt = secrets.token_hex(16)
                    db_user["password_hash"] = hashlib.sha256(f"{salt}123456".encode()).hexdigest()
                    db_user["password_salt"] = salt

                await storage.create_user(db_user)
                print(f"[OK] User: {key}")
                stats["users"]["migrated"] += 1

            except Exception as e:
                print(f"[ERROR] User {key}: {e}")
                stats["users"]["errors"] += 1

    # ===== 2. Migrate Courses =====
    print("\n" + "=" * 50)
    print("Migrating Courses")
    print("=" * 50)

    if courses_path.exists():
        index_file = courses_path / "index.json"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)

            for course_id, index_data in index.items():
                try:
                    # Load full course data
                    course_file = courses_path / course_id / "course.json"
                    if not course_file.exists():
                        print(f"[WARN] Course file not found: {course_id}")
                        stats["courses"]["errors"] += 1
                        continue

                    with open(course_file, "r", encoding="utf-8") as f:
                        course_data = json.load(f)

                    # Check course_id length (max 12 chars)
                    if len(course_id) > 12:
                        print(f"[WARN] Course ID too long ({len(course_id)} chars): {course_id}, skipping")
                        stats["courses"]["errors"] += 1
                        continue

                    # Check if exists
                    existing = await storage.get_course(course_id)
                    if existing:
                        stats["courses"]["skipped"] += 1
                        # Still migrate members/homework/etc
                    else:
                        # Prepare course data for database
                        db_course = {
                            "course_id": course_id,
                            "course_name": course_data.get("courseName") or course_data.get("course_name") or course_data.get("name", ""),
                            "subject": course_data.get("subject", ""),
                            "grade": course_data.get("grade") or course_data.get("grade_level", ""),
                            "description": course_data.get("description", ""),
                            "teacher_id": course_data.get("teacherId") or course_data.get("teacher_id", ""),
                            "teacher_role": "teacher",
                            "teacher_name": course_data.get("teacherName") or course_data.get("teacher_name", ""),
                            "join_code": course_data.get("joinCode") or course_data.get("join_code", ""),
                            "is_public": course_data.get("isPublic", True),
                            "metadata_extra": {
                                "migrated_from": "file",
                                "original_data": course_data
                            },
                        }

                        await storage.create_course(db_course)
                        print(f"[OK] Course: {course_id} - {db_course['course_name']}")
                        stats["courses"]["migrated"] += 1

                    # ===== 2a. Migrate Members =====
                    members_file = courses_path / course_id / "members.json"
                    if members_file.exists():
                        with open(members_file, "r", encoding="utf-8") as f:
                            members = json.load(f)

                        for member in members:
                            try:
                                member_user_id = member.get("userId") or member.get("user_id", "")
                                member_role = member.get("role", "student")
                                display_name = member.get("displayName") or member.get("display_name", member_user_id)

                                # Check if already member
                                is_member = await storage.is_course_member(course_id, member_user_id)
                                if is_member:
                                    stats["members"]["skipped"] += 1
                                    continue

                                await storage.add_course_member(course_id, member_user_id, member_role, display_name)
                                print(f"[OK] Member: {member_user_id} -> {course_id}")
                                stats["members"]["migrated"] += 1

                            except Exception as e:
                                print(f"[ERROR] Member in {course_id}: {e}")
                                stats["members"]["errors"] += 1

                    # ===== 2b. Migrate Lessons =====
                    lessons_dir = courses_path / course_id / "lessons"
                    if lessons_dir.exists():
                        for lesson_dir in lessons_dir.iterdir():
                            if lesson_dir.is_dir():
                                lesson_file = lesson_dir / "lesson.json"
                                if lesson_file.exists():
                                    try:
                                        with open(lesson_file, "r", encoding="utf-8") as f:
                                            lesson_data = json.load(f)

                                        # Prepare lesson data
                                        db_lesson = {
                                            "course_id": course_id,
                                            "title": lesson_data.get("title", ""),
                                            "description": lesson_data.get("description", ""),
                                            "subject": lesson_data.get("subject", ""),
                                            "grade_level": lesson_data.get("grade_level") or lesson_data.get("grade", ""),
                                            "duration": lesson_data.get("duration", 45),
                                            "order": lesson_data.get("order_index", 0),
                                            "objectives": lesson_data.get("objectives", []),
                                            "content": lesson_data.get("content", {}),
                                            "metadata_extra": {
                                                "migrated_from": "file",
                                                "original_id": lesson_dir.name
                                            },
                                        }

                                        # Load plan content if exists
                                        plan_file = lesson_dir / "plan.md"
                                        if plan_file.exists():
                                            db_lesson["plan_content"] = plan_file.read_text(encoding="utf-8")

                                        await storage.create_lesson(db_lesson)
                                        print(f"[OK] Lesson: {lesson_data.get('title', lesson_dir.name)}")
                                        stats["lessons"]["migrated"] += 1

                                    except Exception as e:
                                        print(f"[ERROR] Lesson {lesson_dir.name}: {e}")
                                        stats["lessons"]["errors"] += 1

                    # ===== 2c. Migrate Homework =====
                    homework_dir = courses_path / course_id / "homework"
                    if homework_dir.exists():
                        for hw_file in homework_dir.glob("*.json"):
                            if hw_file.name == "index.json":
                                continue
                            try:
                                with open(hw_file, "r", encoding="utf-8") as f:
                                    hw_data = json.load(f)

                                hw_id = hw_data.get("hwId") or hw_data.get("hw_id") or hw_file.stem

                                # Prepare homework data (only fields supported by Homework model)
                                db_homework = {
                                    "hw_id": hw_id,
                                    "course_id": course_id,
                                    "title": hw_data.get("title", ""),
                                    "description": hw_data.get("description", ""),
                                    "total_points": hw_data.get("totalPoints") or hw_data.get("total_points", 0),
                                    "deadline": parse_datetime(hw_data.get("deadline")),
                                    "created_by": hw_data.get("createdBy") or hw_data.get("created_by", ""),
                                    "settings": {
                                        "migrated_from": "file",
                                        "questions": hw_data.get("questions", []),
                                    },
                                }

                                await storage.create_homework(db_homework)
                                print(f"[OK] Homework: {hw_id} - {db_homework['title']}")
                                stats["homework"]["migrated"] += 1

                                # ===== 2d. Migrate Submissions =====
                                submissions_dir = homework_dir / "submissions"
                                if submissions_dir.exists():
                                    for sub_file in submissions_dir.glob("*.json"):
                                        try:
                                            with open(sub_file, "r", encoding="utf-8") as f:
                                                sub_data = json.load(f)

                                            # Only migrate submissions for this homework
                                            sub_hw_id = sub_data.get("hwId") or sub_data.get("hw_id")
                                            if sub_hw_id != hw_id:
                                                continue

                                            student_id = sub_data.get("studentId") or sub_data.get("student_id", "")

                                            # Prepare submission data (only fields supported by Submission model)
                                            db_submission = {
                                                "hw_id": hw_id,
                                                "student_id": student_id,
                                                "student_role": "student",
                                                "course_id": course_id,
                                                "answers": sub_data.get("answers", {}),
                                                "score": sub_data.get("score", 0),
                                                "feedback": sub_data.get("feedback", {}),
                                                "status": sub_data.get("status", "submitted"),
                                                "graded_by": sub_data.get("gradedBy") or sub_data.get("graded_by"),
                                                "submitted_at": parse_datetime(sub_data.get("submittedAt") or sub_data.get("submitted_at")),
                                                "graded_at": parse_datetime(sub_data.get("gradedAt") or sub_data.get("graded_at")) if sub_data.get("gradedAt") or sub_data.get("graded_at") else None,
                                            }

                                            await storage.create_submission(db_submission)
                                            print(f"[OK] Submission: {student_id} for {hw_id}")
                                            stats["submissions"]["migrated"] += 1

                                        except Exception as e:
                                            print(f"[ERROR] Submission {sub_file.name}: {e}")
                                            stats["submissions"]["errors"] += 1

                            except Exception as e:
                                print(f"[ERROR] Homework {hw_file.name}: {e}")
                                stats["homework"]["errors"] += 1

                    # ===== 2e. Migrate Resources =====
                    resources_dir = courses_path / course_id / "resources"
                    if resources_dir.exists():
                        for res_file in resources_dir.glob("*.json"):
                            try:
                                with open(res_file, "r", encoding="utf-8") as f:
                                    res_data = json.load(f)

                                db_resource = {
                                    "course_id": course_id,
                                    "title": res_data.get("title", ""),
                                    "description": res_data.get("description", ""),
                                    "resource_type": res_data.get("type") or res_data.get("resource_type", "file"),
                                    "file_path": res_data.get("file_path", ""),
                                    "uploaded_by": res_data.get("uploaded_by", ""),
                                    "metadata_extra": {
                                        "migrated_from": "file",
                                        "original_data": res_data
                                    },
                                }

                                await storage.create_resource(db_resource)
                                print(f"[OK] Resource: {db_resource['title']}")
                                stats["resources"]["migrated"] += 1

                            except Exception as e:
                                print(f"[ERROR] Resource {res_file.name}: {e}")
                                stats["resources"]["errors"] += 1

                except Exception as e:
                    print(f"[ERROR] Course {course_id}: {e}")
                    stats["courses"]["errors"] += 1

    # ===== Print Summary =====
    print("\n" + "=" * 50)
    print("Migration Summary")
    print("=" * 50)

    total_migrated = 0
    total_errors = 0

    for category, counts in stats.items():
        m = counts["migrated"]
        s = counts["skipped"]
        e = counts["errors"]
        total_migrated += m
        total_errors += e
        status = "[OK]" if e == 0 else "[WARN]"
        print(f"{status} {category}: {m} migrated, {s} skipped, {e} errors")

    print("-" * 50)
    print(f"Total: {total_migrated} migrated, {total_errors} errors")

    if total_errors > 0:
        print("\n[WARN] Some items failed to migrate. Check errors above.")
    else:
        print("\n[OK] All data migrated successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_all())
