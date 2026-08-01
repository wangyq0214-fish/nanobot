"""Researcher report artifact API handlers."""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.api.report_generator import (
    ReportGenerationError,
)
from nanobot.api.artifact_generators import (
    SUPPORTED_GENERATORS,
    generate_artifact,
    validate_artifact_content,
)
from nanobot.storage.database_storage import DatabaseStorage
from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import http_error, http_json_response, parse_request_mutation


ARTIFACT_TYPES = set(SUPPORTED_GENERATORS)
IMPLEMENTED_ARTIFACT_TYPES = SUPPORTED_GENERATORS
SOURCE_TYPES = {"attachment", "paper", "result", "project", "latex"}


def _database_only(storage: StorageWrapper) -> Response | None:
    if not isinstance(storage.storage, DatabaseStorage):
        return http_error(503, "Research artifacts require database storage")
    return None


def _researcher_only(identity: dict[str, str], action: str) -> Response | None:
    if identity.get("role") != "researcher":
        return http_error(403, f"Only researchers can {action} artifacts")
    return None


async def handle_list_research_artifacts(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    del request
    unavailable = _database_only(storage)
    if unavailable:
        return unavailable
    denied = _researcher_only(identity, "access")
    if denied:
        return denied
    artifacts = await storage.list_research_artifacts(identity.get("user_id", ""), "researcher")
    return http_json_response({"ok": True, "data": artifacts})


async def handle_get_research_artifact(
    request: WsRequest,
    storage: StorageWrapper,
    artifact_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    del request
    unavailable = _database_only(storage)
    if unavailable:
        return unavailable
    denied = _researcher_only(identity, "access")
    if denied:
        return denied
    artifact = await storage.get_research_artifact(int(artifact_id))
    if not _owns(artifact, identity.get("user_id", "")):
        return http_error(404, "Artifact not found")
    return http_json_response({"ok": True, "data": artifact})


async def handle_create_research_artifact(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    unavailable = _database_only(storage)
    if unavailable:
        return unavailable
    denied = _researcher_only(identity, "create")
    if denied:
        return denied
    payload = await parse_request_mutation(request)
    if isinstance(payload, Response):
        return payload
    artifact_type = str(payload.get("type", "")).strip()
    if artifact_type not in IMPLEMENTED_ARTIFACT_TYPES:
        return http_error(400, "This artifact type is not available in this release")
    source_refs = _normalize_source_refs(payload.get("sourceRefs", payload.get("source_refs", [])))
    if not source_refs:
        return http_error(400, "at least one source is required")

    title = str(payload.get("title") or "研究报告").strip()[:240]
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    user_id = identity.get("user_id", "")
    project_id = _optional_int(payload.get("projectId"))
    if project_id is not None and await storage.get_research_project(project_id, user_id, "researcher") is None:
        return http_error(403, "Project does not belong to the current researcher")
    artifact = await storage.create_research_artifact({
        "user_id": user_id,
        "user_role": "researcher",
        "project_id": project_id,
        "artifact_type": artifact_type,
        "title": title,
        "status": "generating",
        "source_refs": source_refs,
        "metadata": {"config": config, "generator": "pending", "schemaVersion": 1},
    })
    await _schedule_generation(storage, artifact, user_id, source_refs, config)
    return http_json_response({"ok": True, "data": artifact}, status=202)


async def handle_regenerate_research_artifact(
    request: WsRequest,
    storage: StorageWrapper,
    artifact_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    del request
    unavailable = _database_only(storage)
    if unavailable:
        return unavailable
    denied = _researcher_only(identity, "generate")
    if denied:
        return denied
    user_id = identity.get("user_id", "")
    artifact = await storage.get_research_artifact(int(artifact_id))
    if not _owns(artifact, user_id):
        return http_error(404, "Artifact not found")
    if artifact.get("type") not in IMPLEMENTED_ARTIFACT_TYPES:
        return http_error(400, "This artifact type is not available in this release")
    source_refs = _normalize_source_refs(artifact.get("sourceRefs", []))
    if not source_refs:
        return http_error(400, "artifact has no sources")
    metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
    config = metadata.get("config") if isinstance(metadata.get("config"), dict) else {}
    await storage.update_research_artifact(int(artifact_id), {"status": "generating", "error_message": ""})
    artifact = await storage.get_research_artifact(int(artifact_id)) or artifact
    await _schedule_generation(storage, artifact, user_id, source_refs, config)
    return http_json_response({"ok": True, "data": await storage.get_research_artifact(int(artifact_id))})


async def handle_update_research_artifact(
    request: WsRequest,
    storage: StorageWrapper,
    artifact_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    unavailable = _database_only(storage)
    if unavailable:
        return unavailable
    denied = _researcher_only(identity, "update")
    if denied:
        return denied
    artifact = await storage.get_research_artifact(int(artifact_id))
    if not _owns(artifact, identity.get("user_id", "")):
        return http_error(404, "Artifact not found")
    if artifact.get("type") not in IMPLEMENTED_ARTIFACT_TYPES:
        return http_error(400, "This artifact type cannot be edited in this release")
    payload = await parse_request_mutation(request)
    if isinstance(payload, Response):
        return payload
    content = payload.get("content")
    try:
        allowed_refs = _normalize_source_refs(artifact.get("sourceRefs", []))
        normalized = validate_artifact_content(artifact.get("type"), content, allowed_refs)
    except ReportGenerationError as exc:
        return http_error(400, str(exc))
    title = str(payload.get("title") or normalized.get("title") or artifact.get("title") or "研究报告").strip()[:240]
    metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
    metadata = {**metadata, "edited": True}
    await storage.update_research_artifact(int(artifact_id), {
        "title": title,
        "content": normalized,
        "status": "ready",
        "metadata": metadata,
        "error_message": "",
    })
    return http_json_response({"ok": True, "data": await storage.get_research_artifact(int(artifact_id))})


async def _schedule_generation(
    storage: StorageWrapper,
    artifact: dict[str, Any],
    user_id: str,
    source_refs: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    job = await storage.create_research_job({
        "user_id": user_id,
        "user_role": "researcher",
        "job_type": "artifact_generate",
        "status": "queued",
        "payload": {"artifactId": artifact["id"], "sourceRefs": source_refs, "config": config},
        "max_attempts": 3,
    })
    await storage.update_research_artifact(artifact["id"], {
        "metadata": {**(artifact.get("metadata") or {}), "jobId": job["id"]},
    })
    from nanobot.services.research_jobs import ensure_research_job_worker
    ensure_research_job_worker(storage)


async def handle_delete_research_artifact(
    request: WsRequest,
    storage: StorageWrapper,
    artifact_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    del request
    unavailable = _database_only(storage)
    if unavailable:
        return unavailable
    denied = _researcher_only(identity, "delete")
    if denied:
        return denied
    artifact = await storage.get_research_artifact(int(artifact_id))
    if not _owns(artifact, identity.get("user_id", "")):
        return http_error(404, "Artifact not found")
    deleted = await storage.delete_research_artifact(int(artifact_id))
    return http_json_response({"ok": bool(deleted)})


async def _generate_and_store(
    storage: StorageWrapper,
    artifact: dict[str, Any],
    user_id: str,
    source_refs: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    try:
        sources = await _load_sources(storage, user_id, source_refs)
        content, generator_metadata = await generate_artifact(artifact["type"], artifact["title"], sources, config)
        old_metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
        metadata = {**old_metadata, **generator_metadata, "config": config}
        await storage.update_research_artifact(artifact["id"], {
            "status": "ready",
            "content": content,
            "metadata": metadata,
            "error_message": "",
        })
    except Exception as exc:
        logger.exception("Failed to generate research artifact {}", artifact.get("id"))
        await storage.update_research_artifact(artifact["id"], {
            "status": "failed",
            "error_message": str(exc),
        })


def _normalize_source_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    refs = []
    seen = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        source_type = str(item.get("type", item.get("sourceType", item.get("source_type", "")))).strip()
        source_id = item.get("id", item.get("sourceId", item.get("source_id")))
        if source_type not in SOURCE_TYPES or source_id in (None, ""):
            continue
        source_id = int(source_id) if str(source_id).isdigit() else str(source_id)
        key = (source_type, str(source_id))
        if key not in seen:
            seen.add(key)
            refs.append({"type": source_type, "id": source_id, **({"title": item["title"]} if item.get("title") else {})})
    return refs


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def _load_sources(storage: StorageWrapper, user_id: str, refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projects = None
    loaded = []
    for ref in refs:
        source_type, source_id = ref["type"], ref["id"]
        item = None
        if source_type == "attachment":
            item = await storage.get_research_attachment(int(source_id))
            if item:
                item["_text"] = item.get("summary", "")
                chunks = await storage.get_research_attachment_chunks(int(source_id))
                item["_text"] += "\n" + "\n".join(chunk.get("content", "") for chunk in chunks)
        elif source_type == "paper":
            item = await storage.get_paper(int(source_id))
            if item:
                item["_text"] = "\n".join(filter(None, [item.get("abstract", ""), item.get("aiSummary", ""), item.get("fullText", "")]))
        elif source_type == "result":
            item = await storage.get_research_result(int(source_id))
            if item:
                item["_text"] = item.get("content", "")
        elif source_type == "project":
            projects = projects if projects is not None else await storage.list_research_projects(user_id, "researcher")
            item = next((project for project in projects if str(project.get("id")) == str(source_id)), None)
            if item:
                item["_text"] = item.get("description", "")
        elif source_type == "latex":
            item = await storage.get_latex_draft(int(source_id))
            if item:
                item["_text"] = item.get("content", "")
        if item and _owns_source(item, user_id):
            item["_sourceType"] = source_type
            item["_sourceId"] = source_id
            loaded.append(item)
    if not loaded:
        raise ValueError("none of the selected sources are available")
    return loaded


def _owns(value: dict[str, Any] | None, user_id: str, user_role: str = "researcher") -> bool:
    return bool(value) and (value.get("userId") or value.get("user_id")) == user_id and (value.get("userRole") or value.get("user_role") or "researcher") == user_role


def _owns_source(value: dict[str, Any], user_id: str) -> bool:
    return _owns(value, user_id)


__all__ = [
    "ARTIFACT_TYPES",
    "IMPLEMENTED_ARTIFACT_TYPES",
    "handle_create_research_artifact",
    "handle_delete_research_artifact",
    "handle_get_research_artifact",
    "handle_list_research_artifacts",
    "handle_regenerate_research_artifact",
    "handle_update_research_artifact",
]
