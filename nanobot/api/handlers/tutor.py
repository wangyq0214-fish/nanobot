"""Tutor profile HTTP handlers.

Provides REST API for fetching student tutor profiles (knowledge points,
error records, learning strategies).
"""

from __future__ import annotations

from typing import Callable

from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import (
    http_error,
    http_json_response,
    parse_query,
    query_first,
)


async def handle_tutor_profile(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    """GET /api/tutor/profile — fetch student's tutor profile."""
    if not check_token(request):
        return http_error(401, "Unauthorized")

    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""

    if role != "student":
        return http_error(403, "Only students can access tutor profile")
    if not user_id:
        return http_error(400, "Missing user_id")

    profile = await storage.get_tutor_profile(user_id)
    if profile is None:
        # Return empty profile instead of 404
        profile = {
            "studentId": user_id,
            "knowledgePoints": [],
            "errorRecords": [],
            "strategies": [],
            "totalSubmissions": 0,
            "lastActive": "",
            "recommendedQuestions": [],
            "recommendedAt": "",
        }

    return http_json_response(profile)
