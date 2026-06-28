"""Analytics handlers for teacher dashboard."""

from __future__ import annotations

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import http_json_response


async def handle_analytics_summary(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Get analytics summary for teacher dashboard."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "teacher":
        return http_json_response({"error": "Only teachers can access analytics"}, status=403)

    try:
        # Get all courses for this teacher
        courses = await storage.list_courses(user_id=user_id)
        if not courses:
            courses = await storage.list_courses()

        # Filter courses taught by this teacher
        teacher_courses = [c for c in courses if c.get("teacher_id") == user_id]
        if not teacher_courses:
            teacher_courses = courses[:5] if courses else []

        total_students = 0
        total_submissions = 0
        graded_submissions = 0
        total_score = 0
        pass_count = 0
        excellent_count = 0
        weak_points = []
        class_stats = []

        for course in teacher_courses:
            course_id = course.get("course_id", "")
            course_name = course.get("course_name", "")

            # Get members
            members = await storage.get_course_members(course_id)
            students = [m for m in members if m.get("user_role") == "student"]
            total_students += len(students)

            # Get homework
            homework_list = await storage.list_homework(course_id)

            for hw in homework_list:
                hw_id = hw.get("hw_id", "")
                submissions = await storage.list_submissions(hw_id)

                for sub in submissions:
                    total_submissions += 1
                    if sub.get("status") == "graded":
                        graded_submissions += 1
                        score = sub.get("score", 0)
                        total_score += score
                        if score >= 60:
                            pass_count += 1
                        if score >= 90:
                            excellent_count += 1

                        # Analyze weak points from feedback
                        feedback = sub.get("feedback", {})
                        if isinstance(feedback, dict):
                            questions = feedback.get("questions", [])
                            for q in questions:
                                if isinstance(q, dict):
                                    q_score = q.get("studentScore", 0)
                                    q_max = q.get("maxScore", 0)
                                    if q_max > 0 and q_score / q_max < 0.6:
                                        comment = q.get("comment", "")
                                        if comment and "错误" in comment:
                                            weak_points.append(comment[:20])

            # Class-level stats
            if students:
                class_submissions = []
                for hw in homework_list:
                    subs = await storage.list_submissions(hw.get("hw_id", ""))
                    class_submissions.extend([s for s in subs if s.get("status") == "graded"])

                if class_submissions:
                    avg_score = sum(s.get("score", 0) for s in class_submissions) / len(class_submissions)
                    pass_rate = sum(1 for s in class_submissions if s.get("score", 0) >= 60) / len(class_submissions) * 100
                    class_stats.append({
                        "name": course_name or course_id,
                        "avgScore": round(avg_score, 1),
                        "passRate": round(pass_rate, 1),
                        "studentCount": len(students),
                        "submissionCount": len(class_submissions),
                    })

        # Calculate overall stats
        avg_score = round(total_score / max(graded_submissions, 1), 1)
        pass_rate = round(pass_count / max(graded_submissions, 1) * 100, 1)
        excellent_rate = round(excellent_count / max(graded_submissions, 1) * 100, 1)

        # Count weak points
        from collections import Counter
        weak_counter = Counter(weak_points)
        top_weak_points = [{"name": k, "count": v} for k, v in weak_counter.most_common(5)]

        return http_json_response({
            "ok": True,
            "analytics": {
                "overview": {
                    "avgScore": avg_score,
                    "passRate": pass_rate,
                    "excellentRate": excellent_rate,
                    "totalStudents": total_students,
                    "totalSubmissions": total_submissions,
                    "gradedSubmissions": graded_submissions,
                    "weakPointCount": len(weak_points),
                },
                "classStats": class_stats[:10],
                "weakPoints": top_weak_points,
            }
        })

    except Exception as e:
        logger.error("Analytics error: {}", e)
        return http_json_response({"error": str(e)}, status=500)
