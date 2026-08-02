





"""WebSocket server channel: nanobot acts as a WebSocket server and serves connected clients."""

from __future__ import annotations

import os

# Increase websockets HTTP request line limit to support longer URLs
# (question bank data is passed as query parameters)
os.environ.setdefault("WEBSOCKETS_MAX_LINE_LENGTH", "65536")

import asyncio
import binascii
import hashlib
import hmac
import json
import mimetypes
import re
import secrets
import shutil
import ssl
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self
from aiohttp import web
from nanobot.config.paths import get_path_root
from urllib.parse import unquote

from loguru import logger
from pydantic import Field, field_validator, model_validator
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.api.auth import AuthManager
from nanobot.api.handlers import (
    handle_ai_generate_questions,
    handle_ai_grade,
    handle_ai_grade_question,
    handle_analytics_summary,
    handle_course_detail,
    handle_course_members,
    handle_courses_create,
    handle_courses_join,
    handle_courses_list,
    handle_create_latex_compile_record,
    handle_create_research_result,
    handle_create_research_artifact,
    handle_create_research_project,
    handle_delete_research_project,
    handle_export_research_artifact,
    handle_export_research_result,
    handle_paper_copilot,
    handle_get_research_job,
    handle_get_research_project_links,
    handle_migrate_research_project_links,
    handle_retry_research_job,
    handle_update_research_project,
    handle_update_research_project_links,
    handle_delete_paper,
    handle_delete_research_result,
    handle_delete_research_artifact,
    handle_delete_research_attachment,
    handle_get_paper,
    handle_get_paper_chunks,
    handle_get_paper_pdf,
    handle_get_latex_draft,
    handle_get_research_result,
    handle_get_research_artifact,
    handle_ai_grade_cropgpt,
    handle_ai_grade_general,
    handle_homework_create,
    handle_homework_delete,
    handle_homework_detail,
    handle_homework_grade,
    handle_homework_list,
    handle_homework_publish,
    handle_homework_submissions,
    handle_homework_submit,
    handle_import_paper,
    handle_lesson_detail,
    handle_lessons_list,
    handle_list_papers,
    handle_list_latex_draft_versions,
    handle_list_latex_drafts,
    handle_list_research_attachments,
    handle_list_research_artifacts,
    handle_list_research_projects,
    handle_list_research_results,
    handle_regenerate_research_artifact,
    handle_update_research_artifact,
    handle_question_bank_add,
    handle_question_bank_batch_add,
    handle_question_bank_delete,
    handle_question_bank_list,
    handle_question_bank_update,
    handle_save_latex_draft,
    handle_search_papers,
    handle_student_categories_list,
    handle_student_category_create,
    handle_student_category_delete,
    handle_student_category_update,
    handle_student_resource_categorize,
    handle_student_resource_create,
    handle_student_resource_delete,
    handle_student_resource_favorite,
    handle_student_resource_update,
    handle_student_resource_upload,
    handle_student_resources_list,
    handle_submission_detail,
    handle_toggle_favorite,
    handle_tutor_profile,
    handle_update_annotations,
    handle_update_research_result,
    handle_update_tags,
    # Resources & notifications
    handle_resource_list,
    handle_resource_create,
    handle_resource_delete,
    handle_notification_list,
    handle_notification_create,
    handle_notification_mark_read,
    handle_discussion_list,
    handle_discussion_create,
    handle_discussion_reply,
    handle_upload_paper,
    handle_upload_research_attachment,
)
from nanobot.api.handlers.research_workspace import _safe_tex_file_name
from nanobot.api.router import Router
from nanobot.api.utils import (
    b64url_decode,
    b64url_encode,
    http_error,
    http_json_response,
    http_response,
    normalize_path,
    parse_query,
    query_first,
)
from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.paths import get_media_dir
from nanobot.config.schema import Base
from nanobot.storage.storage_wrapper import StorageWrapper
from nanobot.utils.helpers import safe_filename
from nanobot.utils.media_decode import (
    FileSizeExceeded,
    save_base64_data_url,
)

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager


def _strip_trailing_slash(path: str) -> str:
    if len(path) > 1 and path.endswith("/"):
        return path.rstrip("/")
    return path or "/"


def _normalize_config_path(path: str) -> str:
    return _strip_trailing_slash(path)


class _RequestWithRawPath:
    """Proxy an aiohttp request while preserving its query string for legacy handlers."""

    def __init__(self, request: web.Request) -> None:
        self._request = request
        self.path = request.raw_path

    def __getattr__(self, name: str) -> Any:
        return getattr(self._request, name)


class WebSocketConfig(Base):
    """WebSocket server channel configuration.

    Clients connect with URLs like ``ws://{host}:{port}{path}?client_id=...&token=...``.
    - ``client_id``: Used for ``allow_from`` authorization; if omitted, a value is generated and logged.
    - ``token``: If non-empty, the ``token`` query param may match this static secret; short-lived tokens
      from ``token_issue_path`` are also accepted.
    - ``token_issue_path``: If non-empty, **GET** (HTTP/1.1) to this path returns JSON
      ``{"token": "...", "expires_in": <seconds>}``; use ``?token=...`` when opening the WebSocket.
      Must differ from ``path`` (the WS upgrade path). If the client runs in the **same process** as
      nanobot and shares the asyncio loop, use a thread or async HTTP client for GET—do not call
      blocking ``urllib`` or synchronous ``httpx`` from inside a coroutine.
    - ``token_issue_secret``: If non-empty, token requests must send ``Authorization: Bearer <secret>`` or
      ``X-Nanobot-Auth: <secret>``.
    - ``websocket_requires_token``: If True, the handshake must include a valid token (static or issued and not expired).
    - Each connection has its own session: a unique ``chat_id`` maps to the agent session internally.
    - ``media`` field in outbound messages contains local filesystem paths; remote clients need a
      shared filesystem or an HTTP file server to access these files.
    """

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8765
    http_port: int = 8767
    latex_http_port: int = 8766
    path: str = "/"
    token: str = ""
    token_issue_path: str = ""
    token_issue_secret: str = ""
    token_ttl_s: int = Field(default=300, ge=30, le=86_400)
    websocket_requires_token: bool = True
    allow_from: list[str] = Field(default_factory=lambda: ["*"])
    streaming: bool = True
    # Default 36 MB, upper 40 MB: supports up to 4 images at ~6 MB each after
    # client-side Worker normalization (see webui Composer). 4 × 6 MB × 1.37
    # (base64 overhead) + envelope framing stays under 36 MB; the 40 MB ceiling
    # leaves a small margin for sender slop without opening a DoS avenue.
    max_message_bytes: int = Field(default=37_748_736, ge=1024, le=41_943_040)
    ping_interval_s: float = Field(default=20.0, ge=5.0, le=300.0)
    ping_timeout_s: float = Field(default=20.0, ge=5.0, le=300.0)
    ssl_certfile: str = ""
    ssl_keyfile: str = ""

    @field_validator("path")
    @classmethod
    def path_must_start_with_slash(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError('path must start with "/"')
        return _normalize_config_path(value)

    @field_validator("token_issue_path")
    @classmethod
    def token_issue_path_format(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if not value.startswith("/"):
            raise ValueError('token_issue_path must start with "/"')
        return _normalize_config_path(value)

    @model_validator(mode="after")
    def token_issue_path_differs_from_ws_path(self) -> Self:
        if not self.token_issue_path:
            return self
        if _normalize_config_path(self.token_issue_path) == _normalize_config_path(self.path):
            raise ValueError("token_issue_path must differ from path (the WebSocket upgrade path)")
        return self



def _read_webui_model_name() -> str | None:
    """Return the configured default model for readonly webui display."""
    try:
        from nanobot.config.loader import load_config

        model = load_config().agents.defaults.model.strip()
        return model or None
    except Exception as e:
        logger.debug("webui bootstrap could not load model name: {}", e)
        return None



def _parse_inbound_payload(raw: str) -> str | None:
    """Parse a client frame into text; return None for empty or unrecognized content."""
    text = raw.strip()
    if not text:
        return None
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(data, dict):
            for key in ("content", "text", "message"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            return None
        return None
    return text


# Accept UUIDs and short scoped keys like "unified:default". Keeps the capability
# namespace small enough to rule out path traversal / quote injection tricks.
_CHAT_ID_RE = re.compile(r"^[A-Za-z0-9_:-]{1,64}$")


def _is_valid_chat_id(value: Any) -> bool:
    return isinstance(value, str) and _CHAT_ID_RE.match(value) is not None


def _parse_envelope(raw: str) -> dict[str, Any] | None:
    """Return a typed envelope dict if the frame is a new-style JSON envelope, else None.

    A frame qualifies when it parses as a JSON object with a string ``type`` field.
    Legacy frames (plain text, or ``{"content": ...}`` without ``type``) return None;
    callers should fall back to :func:`_parse_inbound_payload` for those.
    """
    text = raw.strip()
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    t = data.get("type")
    if not isinstance(t, str):
        return None
    return data


# Per-message media limits. The server-side guard is a touch looser than the
# client's ``Worker`` normalization target (6 MB) — tolerate client slop, but
# still cap total ingress at ``_MAX_IMAGES_PER_MESSAGE * _MAX_IMAGE_BYTES``
# which fits comfortably inside ``max_message_bytes``.
_MAX_IMAGES_PER_MESSAGE = 4
_MAX_IMAGE_BYTES = 8 * 1024 * 1024
_MAX_VIDEOS_PER_MESSAGE = 1
_MAX_VIDEO_BYTES = 20 * 1024 * 1024

# Image MIME whitelist — matches the Composer's ``accept`` list. SVG is
# explicitly excluded to avoid the XSS surface inside embedded scripts.
_IMAGE_MIME_ALLOWED: frozenset[str] = frozenset({
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
})

_VIDEO_MIME_ALLOWED: frozenset[str] = frozenset({
    "video/mp4",
    "video/webm",
    "video/quicktime",
})

_UPLOAD_MIME_ALLOWED: frozenset[str] = _IMAGE_MIME_ALLOWED | _VIDEO_MIME_ALLOWED

_DATA_URL_MIME_RE = re.compile(r"^data:([^;]+);base64,", re.DOTALL)


def _extract_data_url_mime(url: str) -> str | None:
    """Return the MIME type of a ``data:<mime>;base64,...`` URL, else ``None``."""
    if not isinstance(url, str):
        return None
    m = _DATA_URL_MIME_RE.match(url)
    if not m:
        return None
    return m.group(1).strip().lower() or None


# Matches the legacy chat-id pattern but allows file-system-safe stems too,
# so the API can address sessions whose keys came from non-WebSocket channels.
_API_KEY_RE = re.compile(r"^[A-Za-z0-9_:.-]{1,128}$")


def _decode_api_key(raw_key: str) -> str | None:
    """Decode a percent-encoded API path segment, then validate the result."""
    key = unquote(raw_key)
    if _API_KEY_RE.match(key) is None:
        return None
    return key


def _is_websocket_upgrade(request: WsRequest) -> bool:
    """Detect an actual WS upgrade; plain HTTP GETs to the same path should fall through."""
    upgrade = request.headers.get("Upgrade") or request.headers.get("upgrade")
    connection = request.headers.get("Connection") or request.headers.get("connection")
    if not upgrade or "websocket" not in upgrade.lower():
        return False
    if not connection or "upgrade" not in connection.lower():
        return False
    return True



# Allowed MIME types we actually serve from the media endpoint. Anything
# outside this set is degraded to ``application/octet-stream`` so an
# attacker who somehow gets a signed URL for an unexpected file type can't
# trick the browser into sniffing executable content.
_MEDIA_ALLOWED_MIMES: frozenset[str] = frozenset({
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "video/mp4",
    "video/webm",
    "video/quicktime",
})


class WebSocketChannel(BaseChannel):
    """Run a local WebSocket server; forward text/JSON messages to the message bus."""

    name = "websocket"
    display_name = "WebSocket"

    def __init__(
        self,
        config: Any,
        bus: MessageBus,
        *,
        session_manager: "SessionManager | None" = None,
        static_dist_path: Path | None = None,
        agent_manager: Any = None,
    ):
        if isinstance(config, dict):
            config = WebSocketConfig.model_validate(config)
        super().__init__(config, bus)
        self.config: WebSocketConfig = config
        self._agent_manager = agent_manager
        # chat_id -> connections subscribed to it (fan-out target).
        self._subs: dict[str, set[Any]] = {}
        # connection -> chat_ids it is subscribed to (O(1) cleanup on disconnect).
        self._conn_chats: dict[Any, set[str]] = {}
        # connection -> default chat_id for legacy frames that omit routing.
        self._conn_default: dict[Any, str] = {}
        self._stop_event: asyncio.Event | None = None
        self._server_task: asyncio.Task[None] | None = None
        self._session_manager = session_manager
        self._static_dist_path: Path | None = (
            static_dist_path.resolve() if static_dist_path is not None else None
        )
        # Process-local secret used to HMAC-sign media URLs. The signed URL is
        # the capability — anyone who holds a valid URL can fetch that one
        # file, nothing else. The secret regenerates on restart so links
        # become self-expiring (callers just refresh the session list).
        self._media_secret: bytes = secrets.token_bytes(32)
        # Storage wrapper for database operations (lazy initialized)
        self._storage: StorageWrapper | None = None
        # Auth manager for token and user management
        self._auth: AuthManager | None = None
        # Declarative HTTP route table (lazy initialized)
        self._router: Router | None = None
        self._api_http_runner: web.AppRunner | None = None
        self._latex_http_runner: web.AppRunner | None = None

    # -- Subscription bookkeeping -------------------------------------------

    @property
    def storage(self) -> StorageWrapper:
        """Lazy-initialized storage wrapper."""
        if self._storage is None:
            self._storage = StorageWrapper()
        return self._storage

    @property
    def auth(self) -> AuthManager:
        """Lazy-initialized auth manager."""
        if self._auth is None:
            self._auth = AuthManager(
                token=self.config.token,
                token_issue_secret=self.config.token_issue_secret,
                token_ttl_s=self.config.token_ttl_s,
                websocket_requires_token=self.config.websocket_requires_token,
                ws_path=self._expected_path(),
            )
        return self._auth

    @property
    def _router_instance(self) -> Router:
        """Lazy-initialized HTTP route table."""
        if self._router is None:
            self._router = self._build_router()
        return self._router

    async def _ensure_storage(self) -> StorageWrapper:
        """Ensure storage backend is initialized (async)."""
        from nanobot.storage.database_storage import DatabaseStorage
        from nanobot.storage.factory import auto_init_storage, get_storage, is_database_configured

        # Check if we need to initialize database
        if is_database_configured():
            # Check if storage is already initialized as a database backend
            try:
                storage = get_storage()
                storage_cls = storage.__class__.__name__
                # Both DatabaseStorage (PostgreSQL) and MySQLStorage are database backends
                if isinstance(storage, DatabaseStorage) or storage_cls == 'MySQLStorage':
                    pass  # Already initialized with a DB backend, skip re-init
                else:
                    # Need to switch from file storage to database storage
                    await auto_init_storage()
                    storage = get_storage()
                    self._storage = StorageWrapper(storage)
            except Exception:
                # Storage not initialized yet, initialize it
                await auto_init_storage()
                storage = get_storage()
                self._storage = StorageWrapper(storage)
        elif self._storage is None:
            # No database configured, initialize file storage
            from nanobot.storage.factory import init_storage
            await init_storage("file")
            storage = get_storage()
            self._storage = StorageWrapper(storage)
        if isinstance(self.storage.storage, DatabaseStorage):
            from nanobot.services.research_jobs import ensure_research_job_worker
            ensure_research_job_worker(self.storage)
        return self.storage

    def _attach(self, connection: Any, chat_id: str) -> None:
        """Idempotently subscribe *connection* to *chat_id*."""
        self._subs.setdefault(chat_id, set()).add(connection)
        self._conn_chats.setdefault(connection, set()).add(chat_id)

    def _cleanup_connection(self, connection: Any) -> None:
        """Remove *connection* from every subscription set; safe to call multiple times."""
        chat_ids = self._conn_chats.pop(connection, set())
        for cid in chat_ids:
            subs = self._subs.get(cid)
            if subs is None:
                continue
            subs.discard(connection)
            if not subs:
                self._subs.pop(cid, None)
        self._conn_default.pop(connection, None)
        if hasattr(self, '_conn_metadata'):
            self._conn_metadata.pop(connection, None)

    async def _send_event(self, connection: Any, event: str, **fields: Any) -> None:
        """Send a control event (attached, error, ...) to a single connection."""
        payload: dict[str, Any] = {"event": event}
        payload.update(fields)
        raw = json.dumps(payload, ensure_ascii=False)
        try:
            await connection.send(raw)
        except ConnectionClosed:
            self._cleanup_connection(connection)
        except Exception as e:
            logger.warning("websocket: failed to send {} event: {}", event, e)

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        return WebSocketConfig().model_dump(by_alias=True)

    def _expected_path(self) -> str:
        return _normalize_config_path(self.config.path)

    def _build_ssl_context(self) -> ssl.SSLContext | None:
        cert = self.config.ssl_certfile.strip()
        key = self.config.ssl_keyfile.strip()
        if not cert and not key:
            return None
        if not cert or not key:
            raise ValueError(
                "websocket: ssl_certfile and ssl_keyfile must both be set for WSS, or both left empty"
            )
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=cert, keyfile=key)
        return ctx

    # -- HTTP dispatch ------------------------------------------------------

    def _build_router(self) -> Router:
        """Build the declarative HTTP route table.

        Routes are tried in registration order — first match wins.
        Exact-match routes are registered before regex routes so that
        more-specific paths take precedence.
        """
        r = Router()

        # -- Global question bank --
        async def _qb_list(req, storage, *, identity=None):
            from nanobot.api.utils import http_json_response as j, parse_query as pq, query_first as qf
            qp = pq(req.path); qtype = qf(qp, "type") or None
            questions = await storage.list_question_bank(None, qtype)
            return j({"questions": questions})
        async def _qb_add(req, storage, *, identity=None):
            from nanobot.api.utils import http_json_response as j, parse_query as pq, parse_mutation_data
            qp = pq(req.path); payload = parse_mutation_data(qp)
            uid = (identity or {}).get("user_id","") if identity else qp.get("user_id","")
            # Batch mode
            if payload.get("type") == "batch" and payload.get("questions"):
                results = []
                for qd in payload["questions"]:
                    data = {"course_id":"","question_type":qd.get("type","essay"),"content":qd.get("content",""),"points":qd.get("points",10),"answer":qd.get("answer",""),"options":qd.get("options",[]),"tags":qd.get("tags",[]),"created_by":uid}
                    q = await storage.add_to_question_bank(data)
                    results.append(q)
                return j({"ok":True,"questions":results,"count":len(results)})
            # Single mode
            data = {"course_id":"","question_type":payload.get("type","short_answer"),"content":payload.get("content",""),"points":payload.get("points",10),"answer":payload.get("answer",""),"options":payload.get("options",[]),"tags":payload.get("tags",[]),"created_by":uid}
            q = await storage.add_to_question_bank(data)
            return j({"ok":True,"question":q})
        r.add("/api/question-bank", _qb_list, is_async=True, name="qb-global-list", auth_required=False)
        r.add("/api/question-bank/add", _qb_add, is_async=True, name="qb-global-add", auth_required=False)

        # -- Auth endpoints (sync, delegate to AuthManager) ----------------
        r.add("/webui/bootstrap", self.auth.handle_webui_bootstrap, name="webui-bootstrap", auth_required=False)
        r.add("/api/users/register", self.auth.handle_users_register, is_async=True, name="users-register", auth_required=False)
        r.add("/api/users/validate", self.auth.handle_users_validate, is_async=True, name="users-validate", auth_required=False)
        r.add("/api/auth/logout", self.auth.handle_logout, is_async=True, name="auth-logout")

        # -- Session management (sync, local methods) ----------------------
        r.add("/api/sessions", self._handle_sessions_list, name="sessions-list")
        r.add(r"/api/sessions/(?P<key>[^/]+)/messages", self._handle_session_messages, name="session-messages")
        r.add(r"/api/sessions/(?P<key>[^/]+)/delete", self._handle_session_delete, name="session-delete")

        # -- Agent management (sync, local methods) ------------------------
        r.add("/api/agents/current", self._handle_agents_current, name="agents-current")
        r.add("/api/agents/upsert", self._handle_agents_upsert, name="agents-upsert")
        r.add("/api/agents", self._handle_agents_list, name="agents-list")
        r.add(r"/api/agents/(?P<agent_name>[^/]+)/switch", self._handle_agents_switch, name="agents-switch")

        # -- Source file browsing (sync, local methods) --------------------
        r.add("/api/source", self._handle_source_list, name="source-list")
        r.add(r"/api/source/(?P<file_path>.+)", self._handle_source_file, name="source-file")

        # -- Course management (async, delegated to handlers) --------------
        r.add("/api/courses/create", handle_courses_create, is_async=True, name="courses-create")
        r.add("/api/courses/join", handle_courses_join, is_async=True, name="courses-join")
        r.add("/api/courses", handle_courses_list, is_async=True, name="courses-list")
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/members",
            handle_course_members, is_async=True, name="course-members",
        )

        # -- Lesson management ---------------------------------------------
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/lessons/(?P<lesson_id>[^/]+)",
            handle_lesson_detail, is_async=True, name="lesson-detail",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/lessons",
            handle_lessons_list, is_async=True, name="lessons-list",
        )

        # -- Homework management -------------------------------------------
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/create",
            handle_homework_create, is_async=True, name="homework-create",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/submit",
            handle_homework_submit, is_async=True, name="homework-submit",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/submissions/(?P<student_id>[^/]+)",
            handle_submission_detail, is_async=True, name="submission-detail",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/submissions",
            handle_homework_submissions, is_async=True, name="homework-submissions",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/grade",
            handle_homework_grade, is_async=True, name="homework-grade",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/ai-grade-question",
            handle_ai_grade_question, is_async=True, name="ai-grade-question",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/ai-grade",
            handle_ai_grade, is_async=True, name="ai-grade",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/ai-grade-cropgpt",
            handle_ai_grade_cropgpt, is_async=True, name="ai-grade-cropgpt",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/ai-grade-general",
            handle_ai_grade_general, is_async=True, name="ai-grade-general",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/publish",
            handle_homework_publish, is_async=True, name="homework-publish",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)/delete",
            handle_homework_delete, is_async=True, name="homework-delete",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework/(?P<hw_id>[^/]+)",
            handle_homework_detail, is_async=True, name="homework-detail",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/homework",
            handle_homework_list, is_async=True, name="homework-list",
        )

        # -- AI question generation ----------------------------------------
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/ai-generate-questions",
            handle_ai_generate_questions, is_async=True, name="ai-generate-questions",
        )

        # -- Question bank -------------------------------------------------
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/question-bank/batch-add",
            handle_question_bank_batch_add, is_async=True, name="qb-batch-add",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/question-bank/add",
            handle_question_bank_add, is_async=True, name="qb-add",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/question-bank/(?P<question_id>[^/]+)/update",
            handle_question_bank_update, is_async=True, name="qb-update",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/question-bank/(?P<question_id>[^/]+)/delete",
            handle_question_bank_delete, is_async=True, name="qb-delete",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/question-bank",
            handle_question_bank_list, is_async=True, name="qb-list",
        )

        # -- Exams --
        async def _list_exams(req, storage, course_id, *, identity=None):
            from nanobot.api.utils import http_json_response as jj
            exams = await storage.list_exams(course_id)
            return jj({"exams": exams})
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/exams",
            _list_exams, is_async=True, name="exam-list", auth_required=False,
        )

        # -- Course detail (must come after all /api/courses/xxx patterns) --
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)",
            handle_course_detail, is_async=True, name="course-detail",
        )

        # -- Tutor profile -------------------------------------------------
        r.add(
            "/api/tutor/profile",
            handle_tutor_profile, is_async=True, name="tutor-profile",
        )

        # -- Student resources ---------------------------------------------
        r.add(
            "/api/student/resources/create",
            handle_student_resource_create, is_async=True, name="student-resource-create",
        )
        r.add(
            "/api/student/resources/favorite",
            handle_student_resource_favorite, is_async=True, name="student-resource-favorite",
        )
        r.add(
            r"/api/student/resources/(?P<resource_id>\d+)/update",
            handle_student_resource_update, is_async=True, name="student-resource-update",
        )
        r.add(
            r"/api/student/resources/(?P<resource_id>\d+)/delete",
            handle_student_resource_delete, is_async=True, name="student-resource-delete",
        )
        r.add(
            "/api/student/resources/upload",
            handle_student_resource_upload, is_async=True, name="student-resource-upload",
        )
        r.add(
            "/api/student/resources",
            handle_student_resources_list, is_async=True, name="student-resources-list",
        )
        r.add(
            r"/api/student/resources/(?P<resource_id>\d+)/categorize",
            handle_student_resource_categorize, is_async=True, name="student-resource-categorize",
        )

        # -- Student categories --------------------------------------------
        r.add(
            "/api/student/categories/create",
            handle_student_category_create, is_async=True, name="student-category-create",
        )
        r.add(
            r"/api/student/categories/(?P<category_id>\d+)/update",
            handle_student_category_update, is_async=True, name="student-category-update",
        )
        r.add(
            r"/api/student/categories/(?P<category_id>\d+)/delete",
            handle_student_category_delete, is_async=True, name="student-category-delete",
        )
        r.add(
            "/api/student/categories",
            handle_student_categories_list, is_async=True, name="student-categories-list",
        )

        # -- Analytics -----------------------------------------------------
        r.add(
            "/api/analytics/summary",
            handle_analytics_summary, is_async=True, name="analytics-summary",
        )

        # -- Researcher: Paper management ----------------------------------
        r.add(
            r"/api/researcher/papers/upload",
            handle_upload_paper, is_async=True, name="paper-upload",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/copilot",
            handle_paper_copilot, is_async=True, name="paper-copilot",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/favorite",
            handle_toggle_favorite, is_async=True, name="paper-favorite",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/tags",
            handle_update_tags, is_async=True, name="paper-tags",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/annotations",
            handle_update_annotations, is_async=True, name="paper-annotations",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/delete",
            handle_delete_paper, is_async=True, name="paper-delete",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/chunks",
            handle_get_paper_chunks, is_async=True, name="paper-chunks",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)/pdf",
            handle_get_paper_pdf, is_async=True, name="paper-pdf",
        )
        r.add(
            r"/api/researcher/papers/(?P<paper_id>\d+)",
            handle_get_paper, is_async=True, name="paper-detail",
        )
        r.add(
            r"/api/researcher/papers",
            handle_list_papers, is_async=True, name="paper-list",
        )

        # -- Researcher: Paper search --------------------------------------
        r.add(
            r"/api/researcher/search/import",
            handle_import_paper, is_async=True, name="search-import",
        )
        r.add(
            r"/api/researcher/search",
            handle_search_papers, is_async=True, name="search-papers",
        )

        # -- Researcher: Research results ----------------------------------
        r.add(
            r"/api/researcher/results/(?P<result_id>\d+)/export",
            handle_export_research_result, is_async=True, name="result-export",
        )
        r.add(
            r"/api/researcher/results/create",
            handle_create_research_result, is_async=True, name="result-create",
        )
        r.add(
            r"/api/researcher/results/(?P<result_id>\d+)/delete",
            handle_delete_research_result, is_async=True, name="result-delete",
        )
        r.add(
            r"/api/researcher/results/(?P<result_id>\d+)/update",
            handle_update_research_result, is_async=True, name="result-update",
        )
        r.add(
            r"/api/researcher/results/(?P<result_id>\d+)",
            handle_get_research_result, is_async=True, name="result-detail",
        )
        r.add(
            r"/api/researcher/results",
            handle_list_research_results, is_async=True, name="result-list",
        )

        # -- Researcher: generated artifacts -------------------------------
        r.add(
            r"/api/researcher/artifacts/(?P<artifact_id>\d+)/export",
            handle_export_research_artifact, is_async=True, name="artifact-export",
        )
        r.add(
            r"/api/researcher/artifacts/create",
            handle_create_research_artifact, is_async=True, name="artifact-create",
        )
        r.add(
            r"/api/researcher/artifacts/(?P<artifact_id>\d+)/generate",
            handle_regenerate_research_artifact, is_async=True, name="artifact-generate",
        )
        r.add(
            r"/api/researcher/artifacts/(?P<artifact_id>\d+)/update",
            handle_update_research_artifact, is_async=True, name="artifact-update",
        )
        r.add(
            r"/api/researcher/artifacts/(?P<artifact_id>\d+)/delete",
            handle_delete_research_artifact, is_async=True, name="artifact-delete",
        )
        r.add(
            r"/api/researcher/artifacts/(?P<artifact_id>\d+)",
            handle_get_research_artifact, is_async=True, name="artifact-detail",
        )
        r.add(
            r"/api/researcher/artifacts",
            handle_list_research_artifacts, is_async=True, name="artifact-list",
        )

        # -- Researcher: workspace projects and uploaded context ------------
        r.add(
            r"/api/researcher/projects/links/migrate",
            handle_migrate_research_project_links, is_async=True, name="research-project-links-migrate",
        )
        r.add(
            r"/api/researcher/projects/(?P<project_id>\d+)/links",
            handle_get_research_project_links, is_async=True, name="research-project-links-get",
        )
        r.add(
            r"/api/researcher/projects/(?P<project_id>\d+)",
            handle_update_research_project, is_async=True, name="research-project-update",
        )
        r.add(
            r"/api/researcher/projects/(?P<project_id>\d+)/delete",
            handle_delete_research_project, is_async=True, name="research-project-delete",
        )
        r.add(
            r"/api/researcher/projects/create",
            handle_create_research_project, is_async=True, name="research-project-create",
        )
        r.add(
            r"/api/researcher/projects",
            handle_list_research_projects, is_async=True, name="research-project-list",
        )
        r.add(
            r"/api/researcher/latex-drafts/save",
            handle_save_latex_draft, is_async=True, name="latex-draft-save",
        )
        r.add(
            r"/api/researcher/latex-drafts/compile-records/create",
            handle_create_latex_compile_record, is_async=True, name="latex-compile-record-create",
        )
        r.add(
            r"/api/researcher/latex-drafts/(?P<draft_id>\d+)/versions",
            handle_list_latex_draft_versions, is_async=True, name="latex-draft-versions",
        )
        r.add(
            r"/api/researcher/latex-drafts/(?P<draft_id>\d+)",
            handle_get_latex_draft, is_async=True, name="latex-draft-detail",
        )
        r.add(
            r"/api/researcher/latex-drafts",
            handle_list_latex_drafts, is_async=True, name="latex-draft-list",
        )
        r.add(
            r"/api/researcher/jobs/(?P<job_id>\d+)/retry",
            handle_retry_research_job, is_async=True, name="research-job-retry",
        )
        r.add(
            r"/api/researcher/jobs/(?P<job_id>\d+)",
            handle_get_research_job, is_async=True, name="research-job-detail",
        )
        r.add(
            r"/api/researcher/attachments/upload",
            handle_upload_research_attachment, is_async=True, name="research-attachment-upload",
        )
        r.add(
            r"/api/researcher/attachments",
            handle_list_research_attachments, is_async=True, name="research-attachment-list",
        )
        r.add(
            r"/api/researcher/attachments/(?P<attachment_id>\d+)/delete",
            handle_delete_research_attachment, is_async=True, name="research-attachment-delete",
        )

        # -- Course resources ----------------------------------------------
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/resources/create",
            handle_resource_create, is_async=True, name="resource-create",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/resources/(?P<resource_id>\d+)/delete",
            handle_resource_delete, is_async=True, name="resource-delete",
        )
        r.add(
            r"/api/courses/(?P<course_id>[^/]+)/resources",
            handle_resource_list, is_async=True, name="resource-list",
        )

        # -- Notifications & discussions -----------------------------------
        r.add(
            r"/api/notifications/create",
            handle_notification_create, is_async=True, name="notification-create",
        )
        r.add(
            r"/api/notifications/(?P<notification_id>\d+)/read",
            handle_notification_mark_read, is_async=True, name="notification-read",
        )
        r.add(
            r"/api/notifications",
            handle_notification_list, is_async=True, name="notification-list",
        )
        r.add(
            r"/api/discussions/create",
            handle_discussion_create, is_async=True, name="discussion-create",
        )
        r.add(
            r"/api/discussions/(?P<discussion_id>\d+)/reply",
            handle_discussion_reply, is_async=True, name="discussion-reply",
        )
        r.add(
            r"/api/discussions",
            handle_discussion_list, is_async=True, name="discussion-list",
        )

        # -- Media fetch (sync, HMAC-signed URLs, self-authenticating) ------
        r.add(
            r"/api/media/(?P<sig>[A-Za-z0-9_-]+)/(?P<payload>[A-Za-z0-9_-]+)",
            self._handle_media_fetch, name="media-fetch", takes_request=False, auth_required=False,
        )

        return r

    async def _dispatch_http(self, connection: Any, request: WsRequest) -> Any:
        """Route an inbound HTTP request to a handler or to the WS upgrade path."""
        # Ensure storage is initialized for API requests
        await self._ensure_storage()

        got = normalize_path(request.path)
        query = parse_query(request.path)
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization") or ""
        logger.info(
            "[dispatch_http] path={!r} normalized={!r} query_keys={} has_auth={}",
            request.path, got, list(query.keys()), bool(auth_header),
        )

        # 1. Token issue endpoint (legacy, optional, gated by configured secret).
        #    Dynamic path from config — not suitable for the static route table.
        if self.config.token_issue_path:
            issue_expected = _normalize_config_path(self.config.token_issue_path)
            if got == issue_expected:
                return self.auth.handle_token_issue_http(connection, request)

        # 2. Declarative route table for all API endpoints.
        resp = await self._router_instance.dispatch(
            request, got,
            context={
                "storage": self.storage,
                "check_token": self.auth.check_api_token,
                "check_identity": self.auth.check_api_token_with_identity,
                "model_name": _read_webui_model_name(),
            },
        )
        if resp is not None:
            return resp

        # API requests should never fall through to the SPA history fallback.
        # Returning index.html for a missing API route makes the browser try to
        # parse HTML as JSON and hides the real routing/authentication problem.
        if got == "/api" or got.startswith("/api/"):
            return http_error(404, "API endpoint not found")

        # 3. WebSocket upgrade (the channel's primary purpose). Only run the
        # handshake gate on requests that actually ask to upgrade; otherwise
        # a bare ``GET /`` from the browser would be rejected as an
        # unauthorized WS handshake instead of serving the SPA's index.html.
        expected_ws = self._expected_path()
        if got == expected_ws and _is_websocket_upgrade(request):
            client_id = query_first(query, "client_id") or ""
            if len(client_id) > 128:
                client_id = client_id[:128]
            if not self.is_allowed(client_id):
                return connection.respond(403, "Forbidden")
            return self._authorize_websocket_handshake(connection, query, request.headers)

        # 4. Static SPA serving (only if a build directory was wired in).
        if self._static_dist_path is not None:
            response = self._serve_static(got)
            if response is not None:
                return response

        return connection.respond(404, "Not Found")

    # -- Source file HTTP handlers -------------------------------------------

    def _resolve_source_dir(self, identity: dict[str, str]) -> Path | Response:
        """Resolve the source directory for a user, or return an error response."""
        role = identity.get("role", "")
        user_id = identity.get("user_id", "")
        logger.debug("[source] _resolve_source_dir: identity={}", identity)
        if not role or not user_id:
            logger.warning("[source] _resolve_source_dir: missing role or user_id, identity={}", identity)
            return http_error(400, "role and user_id are required")
        source_dir = get_path_root() / "users" / role / user_id / "source"
        if not source_dir.is_dir():
            return http_error(404, "Source directory not found")
        return source_dir

    def _handle_source_list(self, request: WsRequest, *, identity: dict[str, str]) -> Response:
        result = self._resolve_source_dir(identity)
        if isinstance(result, Response):
            return result
        source_dir = result

        files = []
        for f in sorted(source_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(source_dir)
                files.append({
                    "category": str(rel.parent) if str(rel.parent) != "." else "",
                    "name": f.name,
                    "path": str(rel).replace("\\", "/"),
                })
        return http_json_response({"files": files})

    def _handle_source_file(self, request: WsRequest, file_path: str, *, identity: dict[str, str]) -> Response:
        file_path = unquote(file_path)
        # Security: reject path traversal
        if ".." in file_path:
            return http_error(400, "Invalid path")

        result = self._resolve_source_dir(identity)
        if isinstance(result, Response):
            return result
        source_dir = result

        target = (source_dir / file_path).resolve()
        # Ensure resolved path is still under source_dir
        if not str(target).startswith(str(source_dir.resolve())):
            return http_error(403, "Access denied")
        if not target.is_file():
            return http_error(404, "File not found")

        content = target.read_text(encoding="utf-8")
        return http_json_response({"content": content})

    def _handle_sessions_list(self, request: WsRequest, *, identity: dict[str, str]) -> Response:
        # Parse role/user_id from query for per-user session lookup
        role = identity.get("role", "")
        user_id = identity.get("user_id", "")

        # Determine sessions directory: user workspace or global
        if role and user_id:
            sessions_dir = get_path_root() / "users" / role / user_id / "sessions"
            user_prefix = f"{role}_{user_id}_"
        elif self._session_manager is not None:
            sessions_dir = self._session_manager.workspace / "sessions"
            user_prefix = ""
        else:
            return http_error(503, "session manager unavailable")

        if not sessions_dir.is_dir():
            return http_json_response({"sessions": []})

        # Scan JSONL session files
        sessions = []
        for f in sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
            stem = f.stem  # filename without .jsonl
            # Convert underscores back to colons to get original key
            key = stem.replace("_", ":")
            # Only show websocket sessions
            if "websocket:" not in key:
                continue
            # Strip user prefix for frontend display
            if user_prefix and key.startswith(user_prefix.replace("_", ":")):
                display_key = key[len(user_prefix.replace("_", ":")):]
            else:
                display_key = key

            # Read metadata and last user message for preview
            created_at = None
            updated_at = None
            preview = ""
            try:
                with open(f, encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        entry = json.loads(line)
                        if entry.get("_type") == "metadata":
                            created_at = entry.get("created_at")
                            updated_at = entry.get("updated_at")
                        elif entry.get("role") == "user":
                            content = entry.get("content", "")
                            if isinstance(content, str) and content.strip():
                                preview = content.strip()[:80]
            except Exception:
                pass

            sessions.append({
                "key": display_key,
                "created_at": created_at,
                "updated_at": updated_at or f.stat().st_mtime,
                "preview": preview,
            })

        return http_json_response({"sessions": sessions})

    @staticmethod
    def _is_webui_session_key(key: str) -> bool:
        """Return True when *key* belongs to the webui's websocket-only surface."""
        return key.startswith("websocket:")

    def _handle_session_messages(self, request: WsRequest, key: str, *, identity: dict[str, str]) -> Response:
        if self._session_manager is None:
            return http_error(503, "session manager unavailable")
        decoded_key = _decode_api_key(key)
        if decoded_key is None:
            return http_error(400, "invalid session key")
        # The embedded webui only understands websocket-channel sessions. Keep
        # its read surface aligned with ``/api/sessions`` instead of letting a
        # caller probe arbitrary CLI / Slack / Lark history by handcrafted URL.
        if not self._is_webui_session_key(decoded_key):
            return http_error(404, "session not found")

        # Parse role/user_id to find user workspace
        role = identity.get("role", "")
        user_id = identity.get("user_id", "")

        if role and user_id:
            # Reconstruct full key with user prefix for user workspace
            full_key = f"{role}:{user_id}:{decoded_key}"
            user_sessions_dir = get_path_root() / "users" / role / user_id / "sessions"
            # Use safe_key to match file naming convention (colons -> underscores)
            from nanobot.session.manager import SessionManager
            safe_key = SessionManager.safe_key(full_key)
            session_file = user_sessions_dir / f"{safe_key}.jsonl"
            if not session_file.exists():
                # New session without messages yet — return empty list
                return http_json_response({
                    "key": full_key,
                    "created_at": None,
                    "updated_at": None,
                    "messages": [],
                })
            # Read JSONL file directly
            try:
                messages = []
                created_at = updated_at = None
                with open(session_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        entry = json.loads(line)
                        if entry.get("_type") == "metadata":
                            created_at = entry.get("created_at")
                            updated_at = entry.get("updated_at")
                        else:
                            messages.append(entry)
                data = {
                    "key": full_key,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "messages": messages,
                }
            except Exception as e:
                logger.warning("Failed to read user session {}: {}", full_key, e)
                return http_error(500, "Failed to read session")
        else:
            data = self._session_manager.read_session_file(decoded_key)
            if data is None:
                return http_error(404, "session not found")
        # Decorate persisted user messages with signed media URLs so the
        # client can render previews. The raw on-disk ``media`` paths are
        # stripped on the way out — they leak server filesystem layout and
        # the client never needs them once it has the signed fetch URL.
        self._augment_media_urls(data)
        return http_json_response(data)

    def _augment_media_urls(self, payload: dict[str, Any]) -> None:
        """Mutate *payload* in place: each message's ``media`` path list is
        replaced by a parallel ``media_urls`` list of signed fetch URLs.

        Messages without media or with non-string path entries are left
        untouched. Paths that no longer live inside ``media_dir`` (e.g. the
        file was deleted, or the dir was relocated) are silently skipped;
        the client falls back to the historical-replay placeholder tile.
        """
        messages = payload.get("messages")
        if not isinstance(messages, list):
            return
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            media = msg.get("media")
            if not isinstance(media, list) or not media:
                continue
            urls: list[dict[str, str]] = []
            for entry in media:
                if not isinstance(entry, str) or not entry:
                    continue
                signed = self._sign_media_path(Path(entry))
                if signed is None:
                    continue
                urls.append({"url": signed, "name": Path(entry).name})
            if urls:
                msg["media_urls"] = urls
            # Always drop the raw paths from the wire payload.
            msg.pop("media", None)

    def _sign_media_path(self, abs_path: Path) -> str | None:
        """Return a ``/api/media/<sig>/<payload>`` URL for *abs_path*, or
        ``None`` when the path does not resolve inside the media root.

        The URL is self-authenticating: the signature binds the payload to
        this process's ``_media_secret``, so only paths we chose to sign can
        be fetched. The returned path is relative to the server origin; the
        client joins it against the existing webui base.
        """
        try:
            media_root = get_media_dir().resolve()
            rel = abs_path.resolve().relative_to(media_root)
        except (OSError, ValueError):
            return None
        payload = b64url_encode(rel.as_posix().encode("utf-8"))
        mac = hmac.new(
            self._media_secret, payload.encode("ascii"), hashlib.sha256
        ).digest()[:16]
        return f"/api/media/{b64url_encode(mac)}/{payload}"

    def _sign_or_stage_media_path(self, path: Path) -> dict[str, str] | None:
        """Return a signed media URL payload for *path*.

        Persisted inbound media already lives under ``get_media_dir`` and can
        be signed directly. Outbound bot-generated files may live anywhere on
        disk; copy those into the websocket media bucket first so the browser
        can fetch them through the existing signed media route without
        exposing arbitrary filesystem paths.
        """
        signed = self._sign_media_path(path)
        if signed is not None:
            return {"url": signed, "name": path.name}
        try:
            if not path.is_file():
                return None
            media_dir = get_media_dir("websocket")
            safe_name = safe_filename(path.name) or "attachment"
            staged = media_dir / f"{uuid.uuid4().hex[:12]}-{safe_name}"
            shutil.copyfile(path, staged)
        except OSError as exc:
            logger.warning("websocket: failed to stage outbound media {}: {}", path, exc)
            return None
        signed = self._sign_media_path(staged)
        if signed is None:
            return None
        return {"url": signed, "name": path.name}

    def _handle_media_fetch(self, sig: str, payload: str) -> Response:
        """Serve a single media file previously signed via
        :meth:`_sign_media_path`. Validates the signature, decodes the
        payload to a relative path, and streams the file bytes with a
        long-lived immutable cache header (the URL already encodes the
        file identity, so caches can be aggressive)."""
        try:
            provided_mac = b64url_decode(sig)
        except (ValueError, binascii.Error):
            return http_error(401, "invalid signature")
        expected_mac = hmac.new(
            self._media_secret, payload.encode("ascii"), hashlib.sha256
        ).digest()[:16]
        if not hmac.compare_digest(expected_mac, provided_mac):
            return http_error(401, "invalid signature")
        try:
            rel_bytes = b64url_decode(payload)
            rel_str = rel_bytes.decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError):
            return http_error(400, "invalid payload")
        # An attacker who somehow bypassed the HMAC check would still need
        # the resolved path to escape the media root; guard defensively.
        try:
            media_root = get_media_dir().resolve()
            candidate = (media_root / rel_str).resolve()
            candidate.relative_to(media_root)
        except (OSError, ValueError):
            return http_error(404, "not found")
        if not candidate.is_file():
            return http_error(404, "not found")
        try:
            body = candidate.read_bytes()
        except OSError:
            return http_error(500, "read error")
        mime, _ = mimetypes.guess_type(candidate.name)
        if mime not in _MEDIA_ALLOWED_MIMES:
            mime = "application/octet-stream"
        return http_response(
            body,
            content_type=mime,
            extra_headers=[
                ("Cache-Control", "private, max-age=31536000, immutable"),
                # Paired with the MIME whitelist above: prevents browsers from
                # MIME-sniffing an octet-stream fallback into executable HTML.
                ("X-Content-Type-Options", "nosniff"),
            ],
        )

    def _handle_session_delete(self, request: WsRequest, key: str, *, identity: dict[str, str]) -> Response:
        logger.debug("[session-delete] called with key={}, identity={}", key, identity)
        if self._session_manager is None:
            return http_error(503, "session manager unavailable")
        decoded_key = _decode_api_key(key)
        if decoded_key is None:
            return http_error(400, "invalid session key")
        # Same boundary as ``_handle_session_messages``: the webui may only
        # mutate websocket sessions, and deletion really does unlink the local
        # JSONL, so keep the blast radius narrow and explicit.
        if not self._is_webui_session_key(decoded_key):
            return http_error(404, "session not found")

        # Parse role/user_id to find user workspace
        role = identity.get("role", "")
        user_id = identity.get("user_id", "")
        logger.debug("[session-delete] role={}, user_id={}", role, user_id)

        try:
            if role and user_id:
                # Reconstruct full key with user prefix for user workspace
                full_key = f"{role}:{user_id}:{decoded_key}"
                user_sessions_dir = get_path_root() / "users" / role / user_id / "sessions"
                # Use safe_key to match file naming convention (colons -> underscores)
                from nanobot.session.manager import SessionManager
                safe_key = SessionManager.safe_key(full_key)
                session_file = user_sessions_dir / f"{safe_key}.jsonl"
                logger.debug("[session-delete] full_key={}, safe_key={}, session_file={}", full_key, safe_key, session_file)
                if not session_file.exists():
                    logger.debug("[session-delete] file does not exist: {}", session_file)
                    return http_json_response({"deleted": False})
                try:
                    session_file.unlink()
                    return http_json_response({"deleted": True})
                except OSError as e:
                    logger.warning("Failed to delete user session {}: {}", full_key, e)
                    return http_error(500, "Failed to delete session")
            else:
                deleted = self._session_manager.delete_session(decoded_key)
                return http_json_response({"deleted": bool(deleted)})
        except Exception as e:
            logger.error("[session-delete] unexpected error: {}", e, exc_info=True)
            return http_error(500, f"Internal error: {e}")

    def _get_agent_manager(self, *, refresh: bool = False) -> Any:
        manager = getattr(self, "_agent_manager", None)
        if manager is not None and not refresh:
            return manager
        try:
            from nanobot.agent.manager import SimpleAgentManager, manager_config_from_defaults
            from nanobot.config.loader import load_config

            defaults = load_config().agents.defaults
            if not defaults.agents:
                return None
            manager = SimpleAgentManager(manager_config_from_defaults(defaults))
            self._agent_manager = manager
            return manager
        except Exception as e:
            logger.warning("[agents] failed to load default agent config: {}", e)
            return None

    def _read_json_body(self, request: WsRequest) -> dict[str, Any]:
        query = parse_query(request.path)
        raw_data = query_first(query, "data")
        if raw_data:
            data = json.loads(unquote(raw_data))
            if not isinstance(data, dict):
                raise ValueError("JSON data must be an object")
            return data

        raw = getattr(request, "body", b"") or b""
        if isinstance(raw, str):
            text = raw
        else:
            text = raw.decode("utf-8", errors="replace")
        if not text.strip():
            return {}
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _handle_agents_list(self, request: WsRequest, *, identity: dict[str, str]) -> Response:
        """List all available agents."""
        manager = self._get_agent_manager()
        if manager is None:
            return http_json_response({"agents": [], "has_multi_agent": False})
        role = identity.get("role") or ""
        agents = manager.list_agents(role or None)
        if role and not agents:
            manager = self._get_agent_manager(refresh=True)
            agents = manager.list_agents(role or None) if manager is not None else []
        return http_json_response({"agents": agents, "has_multi_agent": True, "role": role})

    def _handle_agents_current(self, request: WsRequest, *, identity: dict[str, str]) -> Response:
        """Get the current active agent."""
        manager = self._get_agent_manager()
        if manager is None:
            return http_json_response({"agent": None, "has_multi_agent": False})
        role = identity.get("role") or ""
        active_agent = manager.get_active_agent(role or None)
        if role and (
            active_agent is None
            or not manager.is_agent_allowed_for_role(active_agent.name, role)
        ):
            manager = self._get_agent_manager(refresh=True)
            active_agent = manager.get_active_agent(role or None) if manager is not None else None
        if active_agent:
            return http_json_response({"agent": active_agent.to_dict(), "has_multi_agent": True, "role": role})
        return http_json_response({"agent": None, "has_multi_agent": True, "role": role})

    def _handle_agents_switch(self, request: WsRequest, agent_name: str, *, identity: dict[str, str]) -> Response:
        """Switch to a different agent."""
        manager = self._get_agent_manager()
        if manager is None:
            return http_error(503, "multi-agent system not configured")
        role = identity.get("role") or ""
        success = manager.switch_agent(agent_name, role=role or None)
        if success:
            return http_json_response({"success": True, "agent": agent_name, "role": role})
        return http_error(404, "agent not found")

    def _handle_agents_upsert(self, request: WsRequest, *, identity: dict[str, str]) -> Response:
        """Create or update an agent profile for the current role."""
        manager = self._get_agent_manager()
        if manager is None:
            return http_error(503, "multi-agent system not configured")
        try:
            body = self._read_json_body(request)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
            return http_error(400, f"invalid JSON body: {e}")

        raw_name = str(body.get("name") or "").strip()
        display_name = str(body.get("display_name") or body.get("displayName") or raw_name).strip()
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_name).strip("_").lower()
        if not name:
            base = re.sub(r"[^A-Za-z0-9_-]+", "_", display_name).strip("_").lower()
            name = base or f"agent_{uuid.uuid4().hex[:8]}"
        role_text = str(body.get("role") or "").strip()
        description = str(body.get("description") or "").strip()
        prompt = body.get("system_prompt_override", body.get("systemPromptOverride"))
        if prompt is not None:
            prompt = str(prompt)
        temperature = body.get("temperature")

        if len(name) < 2:
            name = f"agent_{name}"
        if len(name) > 64:
            name = name[:64].strip("_-") or f"agent_{uuid.uuid4().hex[:8]}"
        if not display_name:
            return http_error(400, "display_name is required")
        if not prompt or not str(prompt).strip():
            return http_error(400, "system_prompt_override is required")

        config: dict[str, Any] = {
            "name": name,
            "displayName": display_name,
            "role": role_text,
            "description": description,
            "systemPromptOverride": str(prompt).strip(),
            "enabled": True,
        }
        if temperature is not None and temperature != "":
            try:
                config["temperature"] = float(temperature)
            except (TypeError, ValueError):
                return http_error(400, "temperature must be a number")

        role = identity.get("role") or ""
        agent = manager.upsert_agent(config, role=role or None)
        try:
            from nanobot.config.loader import load_config, save_config

            cfg = load_config()
            data = cfg.model_dump(mode="json", by_alias=True)
            defaults = data.setdefault("agents", {}).setdefault("defaults", {})
            profiles = defaults.setdefault("agents", [])
            profiles = [p for p in profiles if p.get("name") != agent.name]
            profiles.append(config)
            defaults["agents"] = profiles

            if role:
                role_agents = defaults.setdefault("roleAgents", {})
                role_cfg = role_agents.setdefault(role, {
                    "defaultAgent": agent.name,
                    "availableAgents": [],
                    "traversalFlow": [],
                })
                role_cfg.setdefault("defaultAgent", agent.name)
                role_cfg.setdefault("availableAgents", [])
                role_cfg.setdefault("traversalFlow", [])
                if agent.name not in role_cfg["availableAgents"]:
                    role_cfg["availableAgents"].append(agent.name)
                if agent.name not in role_cfg["traversalFlow"]:
                    role_cfg["traversalFlow"].append(agent.name)

            from nanobot.config.schema import Config

            save_config(Config.model_validate(data))
        except Exception as e:
            logger.warning("[agents] saved runtime agent but failed to persist config: {}", e)

        return http_json_response({
            "success": True,
            "agent": agent.to_dict(),
            "role": role,
        })

    def _serve_static(self, request_path: str) -> Response | None:
        """Resolve *request_path* against the built SPA directory; SPA fallback to index.html."""
        assert self._static_dist_path is not None
        rel = request_path.lstrip("/")
        if not rel:
            rel = "index.html"
        # Reject path-traversal attempts and absolute targets.
        if ".." in rel.split("/") or rel.startswith("/"):
            return http_error(403, "Forbidden")
        candidate = (self._static_dist_path / rel).resolve()
        try:
            candidate.relative_to(self._static_dist_path)
        except ValueError:
            return http_error(403, "Forbidden")
        if not candidate.is_file():
            # SPA history-mode fallback: unknown routes serve index.html so the
            # client-side router can render them.
            index = self._static_dist_path / "index.html"
            if index.is_file():
                candidate = index
            else:
                return None
        try:
            body = candidate.read_bytes()
        except OSError as e:
            logger.warning("websocket static: failed to read {}: {}", candidate, e)
            return http_error(500, "Internal Server Error")
        ctype, _ = mimetypes.guess_type(candidate.name)
        if ctype is None:
            ctype = "application/octet-stream"
        if ctype.startswith("text/") or ctype in {"application/javascript", "application/json"}:
            ctype = f"{ctype}; charset=utf-8"
        # Hash-named build assets are cache-friendly; index.html must stay fresh.
        if candidate.name == "index.html":
            cache = "no-cache"
        else:
            cache = "public, max-age=31536000, immutable"
        return http_response(
            body,
            status=200,
            content_type=ctype,
            extra_headers=[("Cache-Control", cache)],
        )

    def _authorize_websocket_handshake(self, connection: Any, query: dict[str, list[str]], headers: Any = None) -> Any:
        return self.auth.authorize_websocket_handshake(connection, query, headers)

    async def start(self) -> None:
        self._running = True
        self._stop_event = asyncio.Event()

        ssl_context = self._build_ssl_context()
        scheme = "wss" if ssl_context else "ws"

        async def process_request(
            connection: ServerConnection,
            request: WsRequest,
        ) -> Any:
            return await self._dispatch_http(connection, request)

        async def handler(connection: ServerConnection) -> None:
            await self._connection_loop(connection)

        logger.info(
            "WebSocket server listening on {}://{}:{}{}",
            scheme,
            self.config.host,
            self.config.port,
            self.config.path,
        )
        if self.config.token_issue_path:
            logger.info(
                "WebSocket token issue route: {}://{}:{}{}",
                scheme,
                self.config.host,
                self.config.port,
                _normalize_config_path(self.config.token_issue_path),
            )

        async def runner() -> None:
            async with serve(
                handler,
                self.config.host,
                self.config.port,
                process_request=process_request,
                max_size=self.config.max_message_bytes,
                ping_interval=self.config.ping_interval_s,
                ping_timeout=self.config.ping_timeout_s,
                ssl=ssl_context,
            ):
                assert self._stop_event is not None
                await self._stop_event.wait()

        def aiohttp_response(response: Response) -> web.Response:
            headers = {key: value for key, value in response.headers.raw_items()}
            headers.pop("Connection", None)
            headers.pop("Content-Length", None)
            return web.Response(status=response.status_code, body=response.body, headers=headers)

        @web.middleware
        async def api_cors_middleware(request: web.Request, handler: Any) -> web.Response:
            origin = request.headers.get("Origin", "")
            if request.method == "OPTIONS":
                response = web.Response(status=204)
            else:
                response = await handler(request)
            if origin in {"http://localhost:5173", "http://127.0.0.1:5173"}:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                response.headers["Vary"] = "Origin"
            return response

        async def dispatch_api_http(request: web.Request) -> web.Response:
            await self._ensure_storage()
            # aiohttp's ``request.path`` excludes the query string, while the
            # shared legacy handlers read query parameters from ``request.path``.
            # Keep the route match path clean but pass handlers the raw path.
            handler_request = _RequestWithRawPath(request) if request.query_string else request
            response = await self._router_instance.dispatch(
                handler_request,
                normalize_path(request.path),
                context={
                    "storage": self.storage,
                    "check_token": self.auth.check_api_token,
                    "check_identity": self.auth.check_api_token_with_identity,
                    "model_name": _read_webui_model_name(),
                },
            )
            if response is None:
                response = http_error(404, "API endpoint not found")
            return aiohttp_response(response)

        api_app = web.Application(middlewares=[api_cors_middleware], client_max_size=self.config.max_message_bytes)
        api_app.router.add_route("*", "/api/{tail:.*}", dispatch_api_http)
        api_app.router.add_route("*", "/webui/{tail:.*}", dispatch_api_http)
        self._api_http_runner = web.AppRunner(api_app)
        await self._api_http_runner.setup()
        api_site = web.TCPSite(self._api_http_runner, self.config.host, self.config.http_port)
        await api_site.start()
        logger.info("aiohttp API server listening on http://{}:{}", self.config.host, self.config.http_port)

        async def save_latex_http(request: web.Request) -> web.Response:
            token = (request.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
            identity = self.auth.get_token_metadata(token) if token else {}
            if identity.get("role") != "researcher":
                return web.json_response({"error": "Only researchers can save LaTeX drafts"}, status=403)
            try:
                payload = await request.json()
            except Exception:
                return web.json_response({"error": "invalid JSON body"}, status=400)
            if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
                return web.json_response({"error": "content is required"}, status=400)
            file_name = _safe_tex_file_name(str(payload.get("fileName") or "document.tex"))
            try:
                draft = await self.storage.save_latex_draft({
                    "id": payload.get("draftId") or payload.get("id"),
                    "user_id": identity.get("user_id", ""),
                    "user_role": "researcher",
                    "project_id": payload.get("projectId"),
                    "chat_id": str(payload.get("chatId", "")),
                    "title": str(payload.get("title") or file_name.removesuffix(".tex")).strip(),
                    "file_name": file_name,
                    "content": payload["content"],
                    "status": payload.get("status", "draft"),
                    "tags": payload.get("tags", []),
                    "metadata": payload.get("metadata", {}),
                    "attachment_ids": payload.get("attachmentIds"),
                    "change_source": payload.get("changeSource", "manual"),
                })
            except Exception as exc:
                logger.exception("Failed to save LaTeX draft over HTTP")
                return web.json_response({"error": str(exc)}, status=500)
            return web.json_response({"ok": True, "data": draft})

        @web.middleware
        async def latex_cors_middleware(request: web.Request, handler: Any) -> web.Response:
            origin = request.headers.get("Origin", "")
            allowed_origins = {"http://localhost:5173", "http://127.0.0.1:5173"}
            if request.method == "OPTIONS":
                response = web.Response(status=204)
            else:
                response = await handler(request)
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
                response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
                response.headers["Vary"] = "Origin"
            return response

        latex_app = web.Application(middlewares=[latex_cors_middleware])
        latex_app.router.add_options("/{path:.*}", lambda request: web.Response(status=204))
        latex_app.router.add_post("/api/researcher/latex-drafts/save", save_latex_http)
        self._latex_http_runner = web.AppRunner(latex_app)
        await self._latex_http_runner.setup()
        latex_site = web.TCPSite(self._latex_http_runner, self.config.host, self.config.latex_http_port)
        await latex_site.start()
        logger.info("LaTeX HTTP server listening on http://{}:{}", self.config.host, self.config.latex_http_port)

        self._server_task = asyncio.create_task(runner())
        await self._server_task

    async def _connection_loop(self, connection: Any) -> None:
        request = connection.request
        path_part = request.path if request else "/"
        query = parse_query(path_part)
        client_id_raw = query_first(query, "client_id")
        client_id = client_id_raw.strip() if client_id_raw else ""
        if not client_id:
            client_id = f"anon-{uuid.uuid4().hex[:12]}"
        elif len(client_id) > 128:
            logger.warning("websocket: client_id too long ({} chars), truncating", len(client_id))
            client_id = client_id[:128]

        # Extract role/user_id from token metadata.
        # Priority 1: metadata stored during handshake (most reliable)
        # Priority 2: re-extract from query params (fallback)
        conn_meta: dict[str, str] = {}
        # Check for metadata stored during handshake authorization
        handshake_meta = getattr(connection, '_handshake_meta', None)
        if handshake_meta:
            conn_meta = handshake_meta
            logger.info(
                "websocket: using handshake metadata for role={}, user_id={}",
                conn_meta.get("role"), conn_meta.get("user_id"),
            )
        else:
            # Fallback: extract from query parameters
            token = query_first(query, "token") or ""
            if token:
                conn_meta = self.auth.get_token_metadata(token)
                logger.info(
                    "websocket: token={}, metadata={}, all_metadata_keys={}",
                    token[:20] + "..." if len(token) > 20 else token,
                    conn_meta,
                    list(self.auth._token_metadata.keys())[:5],
                )
                if conn_meta:
                    logger.info("websocket: token metadata loaded for role={}, user_id={}", conn_meta.get("role"), conn_meta.get("user_id"))
                else:
                    logger.warning("websocket: no metadata found for token")
            else:
                logger.warning("websocket: no token in WS URL")
        # Store per-connection metadata for use in _dispatch_envelope
        self._conn_metadata: dict[Any, dict[str, str]] = getattr(self, '_conn_metadata', {})
        self._conn_metadata[connection] = conn_meta

        default_chat_id = str(uuid.uuid4())

        try:
            await connection.send(
                json.dumps(
                    {
                        "event": "ready",
                        "chat_id": default_chat_id,
                        "client_id": client_id,
                    },
                    ensure_ascii=False,
                )
            )
            # Register only after ready is successfully sent to avoid out-of-order sends
            self._conn_default[connection] = default_chat_id
            self._attach(connection, default_chat_id)

            async for raw in connection:
                if isinstance(raw, bytes):
                    try:
                        raw = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        logger.warning("websocket: ignoring non-utf8 binary frame")
                        continue

                envelope = _parse_envelope(raw)
                if envelope is not None:
                    asyncio.create_task(self._dispatch_envelope(connection, client_id, envelope))
                    continue

                content = _parse_inbound_payload(raw)
                if content is None:
                    continue
                msg_meta = {
                    "remote": getattr(connection, "remote_address", None),
                }
                msg_meta.update(conn_meta)
                await self._handle_message(
                    sender_id=client_id,
                    chat_id=default_chat_id,
                    content=content,
                    metadata=msg_meta,
                )
        except Exception as e:
            logger.debug("websocket connection ended: {}", e)
        finally:
            self._cleanup_connection(connection)

    @staticmethod
    def _save_envelope_media(
        media: list[Any],
    ) -> tuple[list[str], str | None]:
        """Decode and persist ``media`` items from a ``message`` envelope.

        Returns ``(paths, None)`` on success or ``([], reason)`` on the first
        failure — the caller is expected to surface ``reason`` to the client
        and skip publishing so no half-formed message ever reaches the agent.
        On failure, any files already written to disk earlier in the same
        call are unlinked so partial ingress doesn't leak orphan files.
        ``reason`` is a short, stable token suitable for UI localization.

        Shape: ``list[{"data_url": str, "name"?: str | None}]``.
        """
        image_count = 0
        video_count = 0
        for item in media:
            mime = _extract_data_url_mime(item.get("data_url", "")) if isinstance(item, dict) else None
            if mime in _VIDEO_MIME_ALLOWED:
                video_count += 1
            elif mime in _IMAGE_MIME_ALLOWED:
                image_count += 1
        if image_count > _MAX_IMAGES_PER_MESSAGE:
            return [], "too_many_images"
        if video_count > _MAX_VIDEOS_PER_MESSAGE:
            return [], "too_many_videos"

        media_dir = get_media_dir("websocket")
        paths: list[str] = []

        def _abort(reason: str) -> tuple[list[str], str]:
            for p in paths:
                try:
                    Path(p).unlink(missing_ok=True)
                except OSError as exc:
                    logger.warning(
                        "websocket: failed to unlink partial media {}: {}", p, exc
                    )
            return [], reason

        for item in media:
            if not isinstance(item, dict):
                return _abort("malformed")
            data_url = item.get("data_url")
            if not isinstance(data_url, str) or not data_url:
                return _abort("malformed")
            mime = _extract_data_url_mime(data_url)
            if mime is None:
                return _abort("decode")
            if mime not in _UPLOAD_MIME_ALLOWED:
                return _abort("mime")
            is_video = mime in _VIDEO_MIME_ALLOWED
            max_bytes = _MAX_VIDEO_BYTES if is_video else _MAX_IMAGE_BYTES
            try:
                saved = save_base64_data_url(
                    data_url, media_dir, max_bytes=max_bytes,
                )
            except FileSizeExceeded:
                return _abort("size")
            except Exception as exc:
                logger.warning("websocket: media decode failed: {}", exc)
                return _abort("decode")
            if saved is None:
                return _abort("decode")
            paths.append(saved)
        return paths, None

    async def _dispatch_envelope(
        self,
        connection: Any,
        client_id: str,
        envelope: dict[str, Any],
    ) -> None:
        """Route one typed inbound envelope (``new_chat`` / ``attach`` / ``message``)."""
        from nanobot.api.ws_handlers import dispatch_envelope

        await dispatch_envelope(self, connection, client_id, envelope)

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._stop_event:
            self._stop_event.set()
        if self._server_task:
            try:
                await self._server_task
            except Exception as e:
                logger.warning("websocket: server task error during shutdown: {}", e)
            self._server_task = None
        if self._latex_http_runner:
            await self._latex_http_runner.cleanup()
            self._latex_http_runner = None
        if self._api_http_runner:
            await self._api_http_runner.cleanup()
            self._api_http_runner = None
        self._subs.clear()
        self._conn_chats.clear()
        self._conn_default.clear()
        self._auth = None
        self._router = None

    async def _safe_send_to(self, connection: Any, raw: str, *, label: str = "") -> None:
        """Send a raw frame to one connection, cleaning up on ConnectionClosed."""
        try:
            await connection.send(raw)
        except ConnectionClosed:
            self._cleanup_connection(connection)
            logger.warning("websocket{}connection gone", label)
        except Exception as e:
            logger.error("websocket{}send failed: {}", label, e)
            raise

    async def send(self, msg: OutboundMessage) -> None:
        # Snapshot the subscriber set so ConnectionClosed cleanups mid-iteration are safe.
        conns = list(self._subs.get(msg.chat_id, ()))
        if not conns:
            logger.warning("websocket: no active subscribers for chat_id={}", msg.chat_id)
            return
        payload: dict[str, Any] = {
            "event": "message",
            "chat_id": msg.chat_id,
            "text": msg.content,
        }
        if msg.media:
            payload["media"] = msg.media
            urls: list[dict[str, str]] = []
            for entry in msg.media:
                signed = self._sign_or_stage_media_path(Path(entry))
                if signed is not None:
                    urls.append(signed)
            if urls:
                payload["media_urls"] = urls
        if msg.reply_to:
            payload["reply_to"] = msg.reply_to
        # Mark intermediate agent breadcrumbs (tool-call hints, generic
        # progress strings) so WS clients can render them as subordinate
        # trace rows rather than conversational replies.
        if msg.metadata.get("_trace_message"):
            payload["kind"] = "trace"
            if msg.metadata.get("trace_role"):
                payload["role"] = msg.metadata.get("trace_role")
            if msg.metadata.get("trace_name"):
                payload["name"] = msg.metadata.get("trace_name")
            if msg.metadata.get("trace_reasoning") is not None:
                payload["reasoning"] = bool(msg.metadata.get("trace_reasoning"))
        elif msg.metadata.get("_tool_hint"):
            payload["kind"] = "tool_hint"
        elif msg.metadata.get("_progress"):
            payload["kind"] = "progress"
        raw = json.dumps(payload, ensure_ascii=False)
        for connection in conns:
            await self._safe_send_to(connection, raw, label=" ")

    async def send_delta(
        self,
        chat_id: str,
        delta: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        conns = list(self._subs.get(chat_id, ()))
        if not conns:
            logger.debug("[stream] No subscribers for chat_id={}", chat_id)
            return
        meta = metadata or {}
        if meta.get("_stream_end"):
            body: dict[str, Any] = {"event": "stream_end", "chat_id": chat_id}
        else:
            body = {
                "event": "delta",
                "chat_id": chat_id,
                "text": delta,
            }
        if meta.get("_stream_id") is not None:
            body["stream_id"] = meta["_stream_id"]
        raw = json.dumps(body, ensure_ascii=False)
        if meta.get("_stream_end"):
            logger.debug("[stream] Sending to {} connections: {}", len(conns), body.get("event"))
        for connection in conns:
            await self._safe_send_to(connection, raw, label=" stream ")
