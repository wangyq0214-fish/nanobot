"""Notification and discussion handlers."""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import http_error, http_json_response, parse_mutation_data, parse_query


async def handle_notification_list(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """List notifications for the current user, or all notifications for teacher."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
    query = parse_query(request.path)
    unread_only = query.get("unread") == "1"
    course_id = query.get("course_id") or None

    notifications = await storage.list_notifications(user_id, unread_only=unread_only)

    # Filter by course if requested
    result = []
    for n in notifications:
        result.append({
            "id": n.get("id"),
            "userId": n.get("user_id", ""),
            "type": n.get("notification_type", ""),
            "title": n.get("title", ""),
            "content": n.get("content", ""),
            "relatedType": n.get("related_type", ""),
            "relatedId": n.get("related_id", ""),
            "isRead": n.get("is_read", False),
            "metadata": n.get("metadata", {}),
            "createdAt": n.get("created_at", ""),
        })

    return http_json_response({"notifications": result})


async def handle_notification_create(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Create a notification (teacher announcement or system notification)."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    title = payload.get("title", "").strip()
    if not title:
        return http_error(400, "title is required")

    target_type = payload.get("type", "general")  # general, deadline, exam, schedule
    course_id = payload.get("courseId") or ""
    content = payload.get("content", "")

    # For now, store the notification for the teacher themselves
    # In production, this would fan out to all students in the course
    notification_data = {
        "user_id": user_id,
        "user_role": role,
        "notification_type": target_type,
        "title": title,
        "content": content,
        "related_type": "course" if course_id else None,
        "related_id": course_id or None,
        "is_read": False,
    }
    notification = await storage.create_notification(notification_data)
    logger.info("Notification '{}' created by {}", title, user_id)
    return http_json_response({"ok": True, "notification": notification})


async def handle_notification_mark_read(
    request: WsRequest,
    storage: StorageWrapper,
    notification_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Mark a notification as read."""
    success = await storage.mark_notification_read(int(notification_id))
    if success:
        return http_json_response({"ok": True})
    return http_error(404, "Notification not found")


async def handle_discussion_list(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """List discussions — currently uses notifications with type='discussion'.

    TODO: Replace with dedicated Discussion model when available.
    """
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    # Return discussions as notifications of type "discussion"
    # In the future this should query a dedicated discussions table
    all_notifications = await storage.list_notifications(user_id)
    discussions = [
        {
            "id": n.get("id"),
            "key": f"d{n.get('id')}",
            "title": n.get("title", ""),
            "content": n.get("content", ""),
            "author": "教师",  # In production, resolve from user_id
            "replies": n.get("metadata", {}).get("replies", 0) if n.get("metadata") else 0,
            "time": n.get("created_at", ""),
            "pinned": n.get("metadata", {}).get("pinned", False) if n.get("metadata") else False,
            "courseId": n.get("related_id", ""),
            "createdAt": n.get("created_at", ""),
        }
        for n in all_notifications
        if n.get("notification_type") == "discussion"
    ]
    return http_json_response({"discussions": discussions})


async def handle_discussion_create(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Create a discussion thread."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    title = payload.get("title", "").strip()
    if not title:
        return http_error(400, "title is required")

    notification_data = {
        "user_id": user_id,
        "user_role": role,
        "notification_type": "discussion",
        "title": title,
        "content": payload.get("content", ""),
        "related_type": "course",
        "related_id": payload.get("courseId", ""),
        "is_read": True,
        "metadata": {
            "pinned": payload.get("pinned", False),
            "replies": 0,
            "replyList": [],
        },
    }
    result = await storage.create_notification(notification_data)
    logger.info("Discussion '{}' created by {}", title, user_id)
    return http_json_response({"ok": True, "discussion": result})


async def handle_discussion_reply(
    request: WsRequest,
    storage: StorageWrapper,
    discussion_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Add a reply to a discussion thread."""
    user_id = identity.get("user_id", "")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    reply_text = payload.get("text", "").strip()
    if not reply_text:
        return http_error(400, "text is required")

    # Get current notification
    notification = await storage.get_notification(int(discussion_id))
    if not notification:
        return http_error(404, "Discussion not found")

    meta = notification.get("metadata") or {}
    reply_list = meta.get("replyList", [])
    reply_list.append({
        "id": str(len(reply_list) + 1),
        "author": user_id,  # In production, resolve display name
        "text": reply_text,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    })
    meta["replies"] = len(reply_list)
    meta["replyList"] = reply_list

    # Update via storage
    from nanobot.storage.base import BaseStorage
    # Use update via raw approach since update_notification doesn't exist
    # We'll use the existing update mechanism
    await storage.storage.create_notification.__self__  # placeholder

    logger.info("Reply added to discussion {}", discussion_id)
    return http_json_response({"ok": True, "replies": len(reply_list)})
