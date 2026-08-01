"""Small PostgreSQL-backed worker for researcher jobs."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.storage.storage_wrapper import StorageWrapper

_worker_tasks: set[asyncio.Task[Any]] = set()


def ensure_research_job_worker(storage: StorageWrapper) -> None:
    """Start one worker for this event loop and recover interrupted jobs."""
    loop = asyncio.get_running_loop()
    if any(not task.done() for task in _worker_tasks):
        return
    task = loop.create_task(_worker_loop(storage))
    _worker_tasks.add(task)
    task.add_done_callback(_worker_tasks.discard)


async def _worker_loop(storage: StorageWrapper) -> None:
    await storage.recover_research_jobs()
    while True:
        try:
            job = await storage.claim_research_job()
            if not job:
                await asyncio.sleep(1)
                continue
            try:
                if job["jobType"] == "attachment_parse":
                    await _parse_attachment_job(storage, job)
                elif job["jobType"] == "artifact_generate":
                    await _generate_artifact_job(storage, job)
                else:
                    raise RuntimeError(f"Unsupported research job type: {job['jobType']}")
                await storage.update_research_job(job["id"], {
                    "status": "succeeded", "progress": 100, "finished_at": datetime.utcnow(),
                })
            except Exception as exc:
                logger.exception("Research job {} failed", job.get("id"))
                failed = job.get("attempts", 1) >= job.get("maxAttempts", 3)
                if job.get("jobType") == "attachment_parse":
                    attachment_id = (job.get("payload") or {}).get("attachmentId")
                    if attachment_id:
                        await storage.update_research_attachment(int(attachment_id), {
                            "parse_status": "failed" if failed else "queued",
                            "summary": str(exc),
                        })
                await storage.update_research_job(job["id"], {
                    "status": "failed" if failed else "queued",
                    "error_message": str(exc),
                    "finished_at": datetime.utcnow() if failed else None,
                })
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Research job worker loop failed")
            await asyncio.sleep(1)


async def _parse_attachment_job(storage: StorageWrapper, job: dict[str, Any]) -> None:
    from nanobot.api.handlers.research_workspace import _parse_attachment

    payload = job.get("payload", {})
    attachment_id = int(payload["attachmentId"])
    attachment = await storage.get_research_attachment(attachment_id)
    if not attachment:
        raise RuntimeError("Attachment no longer exists")
    await storage.update_research_attachment(attachment_id, {"parse_status": "running"})
    parsed = _parse_attachment(Path(payload["filePath"]), str(payload.get("fileType", "txt")))
    if parsed["chunks"]:
        await storage.create_research_attachment_chunks(attachment_id, parsed["chunks"])
    await storage.update_research_attachment(attachment_id, {
        "parse_status": "ready", "summary": parsed["summary"], "metadata": parsed.get("metadata", {}),
    })


async def _generate_artifact_job(storage: StorageWrapper, job: dict[str, Any]) -> None:
    from nanobot.api.artifact_generators import generate_artifact
    from nanobot.api.handlers.research_artifacts import _load_sources

    payload = job.get("payload", {})
    artifact_id = int(payload["artifactId"])
    artifact = await storage.get_research_artifact(artifact_id)
    if not artifact:
        raise RuntimeError("Artifact no longer exists")
    sources = await _load_sources(storage, job["userId"], payload.get("sourceRefs", []))
    content, metadata = await generate_artifact(artifact["type"], artifact["title"], sources, payload.get("config", {}))
    old = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
    await storage.update_research_artifact(artifact_id, {
        "status": "ready", "content": content, "metadata": {**old, **metadata}, "error_message": "",
    })
