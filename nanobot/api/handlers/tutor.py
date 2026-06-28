"""Tutor profile HTTP handlers.

Provides REST API for fetching student tutor profiles (knowledge points,
error records, learning strategies).
"""

from __future__ import annotations

from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import (
    http_error,
    http_json_response,
)


async def handle_tutor_profile(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """GET /api/tutor/profile — fetch student's tutor profile."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    if role != "student":
        return http_error(403, "Only students can access tutor profile")
    if not user_id:
        return http_error(400, "Missing user_id")

    profile = await storage.get_tutor_profile(user_id)
    if not profile:
        return http_json_response({"profile": None})

    return http_json_response({"profile": profile})
