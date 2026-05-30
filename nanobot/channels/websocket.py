"""WebSocket server channel: nanobot acts as a WebSocket server and serves connected clients."""

from __future__ import annotations

import asyncio
import base64
import binascii
import email.utils
import hashlib
import hmac
import http
import json
import mimetypes
import re
import secrets
import shutil
import ssl
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self
from urllib.parse import parse_qs, unquote, urlparse

from loguru import logger
from pydantic import Field, field_validator, model_validator
from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.paths import get_media_dir
from nanobot.config.schema import Base
from nanobot.storage.storage_wrapper import StorageWrapper
from nanobot.storage.factory import auto_init_storage
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


def _http_json_response(data: dict[str, Any], *, status: int = 200) -> Response:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = Headers(
        [
            ("Date", email.utils.formatdate(usegmt=True)),
            ("Connection", "close"),
            ("Content-Length", str(len(body))),
            ("Content-Type", "application/json; charset=utf-8"),
        ]
    )
    reason = http.HTTPStatus(status).phrase
    return Response(status, reason, headers, body)




def _read_webui_model_name() -> str | None:
    """Return the configured default model for readonly webui display."""
    try:
        from nanobot.config.loader import load_config

        model = load_config().agents.defaults.model.strip()
        return model or None
    except Exception as e:
        logger.debug("webui bootstrap could not load model name: {}", e)
        return None


def _parse_request_path(path_with_query: str) -> tuple[str, dict[str, list[str]]]:
    """Parse normalized path and query parameters in one pass."""
    parsed = urlparse("ws://x" + path_with_query)
    path = _strip_trailing_slash(parsed.path or "/")
    return path, parse_qs(parsed.query)


def _normalize_http_path(path_with_query: str) -> str:
    """Return the path component (no query string), with trailing slash normalized (root stays ``/``)."""
    return _parse_request_path(path_with_query)[0]


def _parse_query(path_with_query: str) -> dict[str, list[str]]:
    return _parse_request_path(path_with_query)[1]


def _query_first(query: dict[str, list[str]], key: str) -> str | None:
    """Return the first value for *key*, or None."""
    values = query.get(key)
    return values[0] if values else None


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


_LOCALHOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

# Matches the legacy chat-id pattern but allows file-system-safe stems too,
# so the API can address sessions whose keys came from non-WebSocket channels.
_API_KEY_RE = re.compile(r"^[A-Za-z0-9_:.-]{1,128}$")


def _decode_api_key(raw_key: str) -> str | None:
    """Decode a percent-encoded API path segment, then validate the result."""
    key = unquote(raw_key)
    if _API_KEY_RE.match(key) is None:
        return None
    return key


def _is_localhost(connection: Any) -> bool:
    """Return True if *connection* originated from the loopback interface."""
    addr = getattr(connection, "remote_address", None)
    if not addr:
        return False
    host = addr[0] if isinstance(addr, tuple) else addr
    if not isinstance(host, str):
        return False
    # ``::ffff:127.0.0.1`` is loopback in IPv6-mapped form.
    if host.startswith("::ffff:"):
        host = host[7:]
    return host in _LOCALHOSTS


def _http_response(
    body: bytes,
    *,
    status: int = 200,
    content_type: str = "text/plain; charset=utf-8",
    extra_headers: list[tuple[str, str]] | None = None,
) -> Response:
    headers = [
        ("Date", email.utils.formatdate(usegmt=True)),
        ("Connection", "close"),
        ("Content-Length", str(len(body))),
        ("Content-Type", content_type),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    reason = http.HTTPStatus(status).phrase
    return Response(status, reason, Headers(headers), body)


def _http_error(status: int, message: str | None = None) -> Response:
    body = (message or http.HTTPStatus(status).phrase).encode("utf-8")
    return _http_response(body, status=status)


def _bearer_token(headers: Any) -> str | None:
    """Pull a Bearer token out of standard or query-style headers."""
    auth = headers.get("Authorization") or headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def _is_websocket_upgrade(request: WsRequest) -> bool:
    """Detect an actual WS upgrade; plain HTTP GETs to the same path should fall through."""
    upgrade = request.headers.get("Upgrade") or request.headers.get("upgrade")
    connection = request.headers.get("Connection") or request.headers.get("connection")
    if not upgrade or "websocket" not in upgrade.lower():
        return False
    if not connection or "upgrade" not in connection.lower():
        return False
    return True


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 without padding — compact + friendly in URL paths."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Reverse of :func:`_b64url_encode`; caller handles ``ValueError``."""
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


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


def _issue_route_secret_matches(headers: Any, configured_secret: str) -> bool:
    """Return True if the token-issue HTTP request carries credentials matching ``token_issue_secret``."""
    if not configured_secret:
        return True
    authorization = headers.get("Authorization") or headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
        return hmac.compare_digest(supplied, configured_secret)
    header_token = headers.get("X-Nanobot-Auth") or headers.get("x-nanobot-auth")
    if not header_token:
        return False
    return hmac.compare_digest(header_token.strip(), configured_secret)


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
        # Single-use tokens consumed at WebSocket handshake.
        self._issued_tokens: dict[str, float] = {}
        # Multi-use tokens for the embedded webui's REST surface; checked but not consumed.
        self._api_tokens: dict[str, float] = {}
        # Token metadata: role, user_id associated with each token
        self._token_metadata: dict[str, dict[str, str]] = {}
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

    # -- Subscription bookkeeping -------------------------------------------

    @property
    def storage(self) -> StorageWrapper:
        """Lazy-initialized storage wrapper."""
        if self._storage is None:
            self._storage = StorageWrapper()
        return self._storage

    async def _ensure_storage(self) -> StorageWrapper:
        """Ensure storage backend is initialized (async)."""
        from nanobot.storage.factory import get_storage, is_database_configured
        from nanobot.storage.database_storage import DatabaseStorage

        # Check if we need to initialize database
        if is_database_configured():
            storage = get_storage()
            if not isinstance(storage, DatabaseStorage):
                # Need to switch to database storage
                await auto_init_storage()
                self._storage = StorageWrapper()  # Reset wrapper
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

    _MAX_ISSUED_TOKENS = 10_000

    def _purge_expired_issued_tokens(self) -> None:
        now = time.monotonic()
        for token_key, expiry in list(self._issued_tokens.items()):
            if now > expiry:
                self._issued_tokens.pop(token_key, None)

    def _take_issued_token_if_valid(self, token_value: str | None) -> bool:
        """Validate and consume one issued token (single use per connection attempt).

        Uses single-step pop to minimize the window between lookup and removal;
        safe under asyncio's single-threaded cooperative model.
        """
        if not token_value:
            return False
        self._purge_expired_issued_tokens()
        expiry = self._issued_tokens.pop(token_value, None)
        if expiry is None:
            return False
        if time.monotonic() > expiry:
            return False
        return True

    def _handle_token_issue_http(self, connection: Any, request: Any) -> Any:
        secret = self.config.token_issue_secret.strip()
        if secret:
            if not _issue_route_secret_matches(request.headers, secret):
                return connection.respond(401, "Unauthorized")
        else:
            logger.warning(
                "websocket: token_issue_path is set but token_issue_secret is empty; "
                "any client can obtain connection tokens — set token_issue_secret for production."
            )
        self._purge_expired_issued_tokens()
        if len(self._issued_tokens) >= self._MAX_ISSUED_TOKENS:
            logger.error(
                "websocket: too many outstanding issued tokens ({}), rejecting issuance",
                len(self._issued_tokens),
            )
            return _http_json_response({"error": "too many outstanding tokens"}, status=429)
        token_value = f"nbwt_{secrets.token_urlsafe(32)}"
        self._issued_tokens[token_value] = time.monotonic() + float(self.config.token_ttl_s)

        return _http_json_response(
            {"token": token_value, "expires_in": self.config.token_ttl_s}
        )

    # -- HTTP dispatch ------------------------------------------------------

    async def _dispatch_http(self, connection: Any, request: WsRequest) -> Any:
        """Route an inbound HTTP request to a handler or to the WS upgrade path."""
        # Ensure storage is initialized for API requests
        await self._ensure_storage()

        got, query = _parse_request_path(request.path)

        # 1. Token issue endpoint (legacy, optional, gated by configured secret).
        if self.config.token_issue_path:
            issue_expected = _normalize_config_path(self.config.token_issue_path)
            if got == issue_expected:
                return self._handle_token_issue_http(connection, request)

        # 2. WebUI bootstrap: localhost-only, mints tokens for the embedded UI.
        if got == "/webui/bootstrap":
            return self._handle_webui_bootstrap(connection, request)

        # 3. REST surface for the embedded UI.
        if got == "/api/users/register":
            return await self._handle_users_register(request)

        if got == "/api/users/validate":
            return await self._handle_users_validate(request)

        if got == "/api/sessions":
            return self._handle_sessions_list(request)

        m = re.match(r"^/api/sessions/([^/]+)/messages$", got)
        if m:
            return self._handle_session_messages(request, m.group(1))

        # NOTE: websockets' HTTP parser only accepts GET, so we cannot expose a
        # true ``DELETE`` verb. The action is folded into the path instead.
        m = re.match(r"^/api/sessions/([^/]+)/delete$", got)
        if m:
            return self._handle_session_delete(request, m.group(1))

        # Agent management endpoints
        if got == "/api/agents":
            return self._handle_agents_list(request)

        if got == "/api/agents/current":
            return self._handle_agents_current(request)

        m = re.match(r"^/api/agents/([^/]+)/switch$", got)
        if m:
            return self._handle_agents_switch(request, m.group(1))

        # Source file endpoints (user workspace source directory)
        if got == "/api/source":
            return self._handle_source_list(request)

        m = re.match(r"^/api/source/(.+)$", got)
        if m:
            return self._handle_source_file(request, m.group(1))

        # Course endpoints
        if got == "/api/courses":
            return await self._handle_courses_list(request)
        if got == "/api/courses/create":
            return await self._handle_courses_create(request)
        if got == "/api/courses/join":
            return await self._handle_courses_join(request)
        m = re.match(r"^/api/courses/([^/]+)/members$", got)
        if m:
            return await self._handle_course_members(request, m.group(1))
        m = re.match(r"^/api/courses/([^/]+)/lessons/([^/]+)$", got)
        if m:
            return await self._handle_lesson_detail(request, m.group(1), m.group(2))
        m = re.match(r"^/api/courses/([^/]+)/lessons$", got)
        if m:
            return await self._handle_lessons_list(request, m.group(1))
        m = re.match(r"^/api/courses/([^/]+)/homework/create$", got)
        if m:
            return await self._handle_homework_create(request, m.group(1))
        m = re.match(r"^/api/courses/([^/]+)/homework/([^/]+)/submit$", got)
        if m:
            return await self._handle_homework_submit(request, m.group(1), m.group(2))
        m = re.match(r"^/api/courses/([^/]+)/homework/([^/]+)/submissions/([^/]+)$", got)
        if m:
            return await self._handle_submission_detail(request, m.group(1), m.group(2), m.group(3))
        m = re.match(r"^/api/courses/([^/]+)/homework/([^/]+)/submissions$", got)
        if m:
            return await self._handle_homework_submissions(request, m.group(1), m.group(2))
        m = re.match(r"^/api/courses/([^/]+)/homework/([^/]+)/grade$", got)
        if m:
            return await self._handle_homework_grade(request, m.group(1), m.group(2))
        m = re.match(r"^/api/courses/([^/]+)/homework/([^/]+)$", got)
        if m:
            return await self._handle_homework_detail(request, m.group(1), m.group(2))
        m = re.match(r"^/api/courses/([^/]+)/homework$", got)
        if m:
            return await self._handle_homework_list(request, m.group(1))
        m = re.match(r"^/api/courses/([^/]+)$", got)
        if m:
            return await self._handle_course_detail(request, m.group(1))

        # Signed media fetch: ``<sig>`` is an HMAC over ``<payload>``; the
        # payload decodes to a path inside :func:`get_media_dir`. See
        # :meth:`_sign_media_path` for the inverse direction used to build
        # these URLs when replaying a session.
        m = re.match(r"^/api/media/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)$", got)
        if m:
            return self._handle_media_fetch(m.group(1), m.group(2))

        # 4. WebSocket upgrade (the channel's primary purpose). Only run the
        # handshake gate on requests that actually ask to upgrade; otherwise
        # a bare ``GET /`` from the browser would be rejected as an
        # unauthorized WS handshake instead of serving the SPA's index.html.
        expected_ws = self._expected_path()
        if got == expected_ws and _is_websocket_upgrade(request):
            client_id = _query_first(query, "client_id") or ""
            if len(client_id) > 128:
                client_id = client_id[:128]
            if not self.is_allowed(client_id):
                return connection.respond(403, "Forbidden")
            return self._authorize_websocket_handshake(connection, query)

        # 5. Static SPA serving (only if a build directory was wired in).
        if self._static_dist_path is not None:
            response = self._serve_static(got)
            if response is not None:
                return response

        return connection.respond(404, "Not Found")

    # -- HTTP route handlers ------------------------------------------------

    def _check_api_token(self, request: WsRequest) -> bool:
        """Validate a request against the API token pool (multi-use, TTL-bound)."""
        self._purge_expired_api_tokens()
        token = _bearer_token(request.headers) or _query_first(
            _parse_query(request.path), "token"
        )
        if not token:
            return False
        expiry = self._api_tokens.get(token)
        if expiry is None or time.monotonic() > expiry:
            self._api_tokens.pop(token, None)
            return False
        return True

    def _purge_expired_api_tokens(self) -> None:
        now = time.monotonic()
        for token_key, expiry in list(self._api_tokens.items()):
            if now > expiry:
                self._api_tokens.pop(token_key, None)

    def _handle_webui_bootstrap(self, connection: Any, request: WsRequest | None = None) -> Response:
        # Cap outstanding tokens to avoid runaway growth from a misbehaving client.
        self._purge_expired_issued_tokens()
        self._purge_expired_api_tokens()
        if (
            len(self._issued_tokens) >= self._MAX_ISSUED_TOKENS
            or len(self._api_tokens) >= self._MAX_ISSUED_TOKENS
        ):
            return _http_response(
                json.dumps({"error": "too many outstanding tokens"}).encode("utf-8"),
                status=429,
                content_type="application/json; charset=utf-8",
            )

        # Parse role and user_id from query parameters
        role = ""
        user_id = ""
        if request:
            query = _parse_query(request.path)
            role = _query_first(query, "role") or ""
            user_id = _query_first(query, "user_id") or ""

        token = f"nbwt_{secrets.token_urlsafe(32)}"
        expiry = time.monotonic() + float(self.config.token_ttl_s)
        # Same string registered in both pools: the WS handshake consumes one copy
        # while the REST surface keeps validating the other until TTL expiry.
        self._issued_tokens[token] = expiry
        self._api_tokens[token] = expiry

        # Store user metadata associated with this token
        if role or user_id:
            self._token_metadata[token] = {
                "role": role,
                "user_id": user_id,
            }

        resp: dict[str, Any] = {
            "token": token,
            "ws_path": self._expected_path(),
            "expires_in": self.config.token_ttl_s,
            "model_name": _read_webui_model_name(),
        }
        if role:
            resp["role"] = role
        if user_id:
            resp["user_id"] = user_id
        return _http_json_response(resp)

    # -- User management helpers ----------------------------------------------

    @property
    def _users_file(self) -> Path:
        return Path.home() / ".nanobot" / "users.json"

    def _load_users(self) -> dict[str, Any]:
        path = self._users_file
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_users(self, data: dict[str, Any]) -> None:
        path = self._users_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _create_user_workspace(self, role: str, user_id: str) -> None:
        """Create user workspace with USER.md and directory structure.

        AGENTS.md / SOUL.md / TOOLS.md are read directly from the role
        template directory by ContextBuilder, so we do NOT copy them into
        per-user workspaces.
        """
        templates_dir = Path.home() / ".nanobot" / "templates" / role
        if not templates_dir.is_dir():
            logger.warning("Template directory not found: {}", templates_dir)
            return

        users_dir = Path.home() / ".nanobot" / "users" / role / user_id
        if users_dir.exists():
            return

        users_dir.mkdir(parents=True, exist_ok=True)
        # Only copy USER.md (per-user profile); the other bootstrap files
        # (AGENTS.md, SOUL.md, TOOLS.md) stay in the role template dir.
        user_md = templates_dir / "USER.md"
        if user_md.is_file():
            shutil.copy2(user_md, users_dir / "USER.md")
        # Ensure required subdirectories exist
        (users_dir / "sessions").mkdir(exist_ok=True)
        (users_dir / "source").mkdir(exist_ok=True)
        (users_dir / "memory").mkdir(exist_ok=True)
        logger.info("Created workspace for user: {} (role={})", user_id, role)

    # -- Course storage helpers ------------------------------------------------

    @property
    def _courses_dir(self) -> Path:
        return Path.home() / ".nanobot" / "courses"

    @property
    def _courses_index_file(self) -> Path:
        return self._courses_dir / "index.json"

    def _load_courses_index(self) -> dict[str, Any]:
        path = self._courses_index_file
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_courses_index(self, data: dict[str, Any]) -> None:
        path = self._courses_index_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_course(self, course_id: str) -> dict[str, Any] | None:
        path = self._courses_dir / course_id / "course.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _save_course(self, course_id: str, data: dict[str, Any]) -> None:
        path = self._courses_dir / course_id / "course.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_members(self, course_id: str) -> list[dict[str, Any]]:
        path = self._courses_dir / course_id / "members.json"
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save_members(self, course_id: str, members: list[dict[str, Any]]) -> None:
        path = self._courses_dir / course_id / "members.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(members, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_homework(self, course_id: str, hw_id: str) -> dict[str, Any] | None:
        path = self._courses_dir / course_id / "homework" / f"{hw_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _list_homework(self, course_id: str) -> list[dict[str, Any]]:
        hw_dir = self._courses_dir / course_id / "homework"
        if not hw_dir.is_dir():
            return []
        result = []
        for f in sorted(hw_dir.glob("*.json")):
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return result

    def _save_homework(self, course_id: str, hw_id: str, data: dict[str, Any]) -> None:
        path = self._courses_dir / course_id / "homework" / f"{hw_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_submission(self, course_id: str, hw_id: str, student_id: str) -> dict[str, Any] | None:
        path = self._courses_dir / course_id / "homework" / "submissions" / f"{student_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("hwId") == hw_id:
                return data
            return None
        except (json.JSONDecodeError, OSError):
            return None

    def _save_submission(self, course_id: str, hw_id: str, student_id: str, data: dict[str, Any]) -> None:
        path = self._courses_dir / course_id / "homework" / "submissions" / f"{student_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _list_submissions(self, course_id: str, hw_id: str) -> list[dict[str, Any]]:
        sub_dir = self._courses_dir / course_id / "homework" / "submissions"
        if not sub_dir.is_dir():
            return []
        result = []
        for f in sorted(sub_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("hwId") == hw_id:
                    result.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return result

    def _load_lessons(self, course_id: str) -> list[dict[str, Any]]:
        lessons_dir = self._courses_dir / course_id / "lessons"
        if not lessons_dir.is_dir():
            return []
        result = []
        for d in sorted(lessons_dir.iterdir()):
            if d.is_dir():
                lesson_file = d / "lesson.json"
                if lesson_file.exists():
                    try:
                        result.append(json.loads(lesson_file.read_text(encoding="utf-8")))
                    except (json.JSONDecodeError, OSError):
                        continue
        return result

    def _save_lesson(self, course_id: str, lesson_id: str, data: dict[str, Any]) -> None:
        path = self._courses_dir / course_id / "lessons" / lesson_id / "lesson.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_lesson_plan(self, course_id: str, lesson_id: str, content: str) -> None:
        path = self._courses_dir / course_id / "lessons" / lesson_id / "plan.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _generate_join_code(self) -> str:
        index = self._load_courses_index()
        existing = {c.get("joinCode") for c in index.values()}
        while True:
            code = f"{secrets.randbelow(1_000_000):06d}"
            if code not in existing:
                return code

    def _generate_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def _parse_mutation_data(self, query: dict[str, list[str]]) -> dict[str, Any] | Response:
        raw = _query_first(query, "data")
        if not raw:
            return _http_error(400, "missing data parameter")
        try:
            payload = json.loads(unquote(raw))
        except (json.JSONDecodeError, TypeError):
            return _http_error(400, "invalid JSON in data parameter")
        if not isinstance(payload, dict):
            return _http_error(400, "data must be a JSON object")
        return payload

    # -- User management HTTP handlers ----------------------------------------

    async def _handle_users_register(self, request: WsRequest) -> Response:
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        display_name = _query_first(query, "display_name") or user_id
        password = _query_first(query, "password") or ""

        if not role or not user_id:
            return _http_error(400, "role and user_id are required")
        if role not in ("student", "teacher", "researcher"):
            return _http_error(400, "Invalid role")
        if len(user_id) > 64:
            return _http_error(400, "user_id too long (max 64)")
        if not password:
            return _http_error(400, "password is required")

        # Check if user already exists
        existing = await self.storage.get_user(role, user_id)
        if existing:
            return _http_error(409, "User already exists")

        # Hash password
        import hashlib
        import secrets as secrets_mod
        salt = secrets_mod.token_hex(16)
        password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

        user_data = {
            "role": role,
            "user_id": user_id,
            "display_name": display_name,
            "password_hash": password_hash,
            "password_salt": salt,
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        user = await self.storage.create_user(user_data)

        # Create user workspace from templates
        self._create_user_workspace(role, user_id)

        logger.info("Registered user: {} (role={})", user_id, role)
        return _http_json_response({"ok": True, "user": user})

    async def _handle_users_validate(self, request: WsRequest) -> Response:
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        password = _query_first(query, "password") or ""

        if not role or not user_id:
            return _http_error(400, "role and user_id are required")

        user = await self.storage.get_user(role, user_id)
        if not user:
            return _http_error(404, "User not found")

        # Validate password if provided
        if password and user.get("password_hash"):
            import hashlib
            salt = user.get("password_salt", "")
            expected_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            if expected_hash != user.get("password_hash"):
                return _http_error(401, "Invalid password")

        return _http_json_response({"ok": True, "user": user})

    # -- Source file HTTP handlers -------------------------------------------

    def _resolve_source_dir(self, request: WsRequest) -> Path | Response:
        """Resolve the source directory for a user, or return an error response."""
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        if not role or not user_id:
            return _http_error(400, "role and user_id are required")
        source_dir = Path.home() / ".nanobot" / "users" / role / user_id / "source"
        if not source_dir.is_dir():
            return _http_error(404, "Source directory not found")
        return source_dir

    def _handle_source_list(self, request: WsRequest) -> Response:
        result = self._resolve_source_dir(request)
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
        return _http_json_response({"files": files})

    def _handle_source_file(self, request: WsRequest, file_path: str) -> Response:
        file_path = unquote(file_path)
        # Security: reject path traversal
        if ".." in file_path:
            return _http_error(400, "Invalid path")
        result = self._resolve_source_dir(request)
        if isinstance(result, Response):
            return result
        source_dir = result

        target = (source_dir / file_path).resolve()
        # Ensure resolved path is still under source_dir
        if not str(target).startswith(str(source_dir.resolve())):
            return _http_error(403, "Access denied")
        if not target.is_file():
            return _http_error(404, "File not found")

        content = target.read_text(encoding="utf-8")
        return _http_json_response({"content": content})

    def _handle_sessions_list(self, request: WsRequest) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")

        # Parse role/user_id from query for per-user session lookup
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""

        # Determine sessions directory: user workspace or global
        if role and user_id:
            sessions_dir = Path.home() / ".nanobot" / "users" / role / user_id / "sessions"
            user_prefix = f"{role}_{user_id}_"
        elif self._session_manager is not None:
            sessions_dir = self._session_manager.workspace / "sessions"
            user_prefix = ""
        else:
            return _http_error(503, "session manager unavailable")

        if not sessions_dir.is_dir():
            return _http_json_response({"sessions": []})

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
            sessions.append({
                "key": display_key,
                "created_at": None,
                "updated_at": None,
                "preview": "",
            })

        return _http_json_response({"sessions": sessions})

    @staticmethod
    def _is_webui_session_key(key: str) -> bool:
        """Return True when *key* belongs to the webui's websocket-only surface."""
        return key.startswith("websocket:")

    def _handle_session_messages(self, request: WsRequest, key: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        if self._session_manager is None:
            return _http_error(503, "session manager unavailable")
        decoded_key = _decode_api_key(key)
        if decoded_key is None:
            return _http_error(400, "invalid session key")
        # The embedded webui only understands websocket-channel sessions. Keep
        # its read surface aligned with ``/api/sessions`` instead of letting a
        # caller probe arbitrary CLI / Slack / Lark history by handcrafted URL.
        if not self._is_webui_session_key(decoded_key):
            return _http_error(404, "session not found")

        # Parse role/user_id to find user workspace
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""

        if role and user_id:
            # Reconstruct full key with user prefix for user workspace
            full_key = f"{role}:{user_id}:{decoded_key}"
            user_sessions_dir = Path.home() / ".nanobot" / "users" / role / user_id / "sessions"
            # Use safe_key to match file naming convention (colons -> underscores)
            from nanobot.session.manager import SessionManager
            safe_key = SessionManager.safe_key(full_key)
            session_file = user_sessions_dir / f"{safe_key}.jsonl"
            if not session_file.exists():
                return _http_error(404, "session not found")
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
                return _http_error(500, "Failed to read session")
        else:
            data = self._session_manager.read_session_file(decoded_key)
            if data is None:
                return _http_error(404, "session not found")
        # Decorate persisted user messages with signed media URLs so the
        # client can render previews. The raw on-disk ``media`` paths are
        # stripped on the way out — they leak server filesystem layout and
        # the client never needs them once it has the signed fetch URL.
        self._augment_media_urls(data)
        return _http_json_response(data)

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
        payload = _b64url_encode(rel.as_posix().encode("utf-8"))
        mac = hmac.new(
            self._media_secret, payload.encode("ascii"), hashlib.sha256
        ).digest()[:16]
        return f"/api/media/{_b64url_encode(mac)}/{payload}"

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
            provided_mac = _b64url_decode(sig)
        except (ValueError, binascii.Error):
            return _http_error(401, "invalid signature")
        expected_mac = hmac.new(
            self._media_secret, payload.encode("ascii"), hashlib.sha256
        ).digest()[:16]
        if not hmac.compare_digest(expected_mac, provided_mac):
            return _http_error(401, "invalid signature")
        try:
            rel_bytes = _b64url_decode(payload)
            rel_str = rel_bytes.decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError):
            return _http_error(400, "invalid payload")
        # An attacker who somehow bypassed the HMAC check would still need
        # the resolved path to escape the media root; guard defensively.
        try:
            media_root = get_media_dir().resolve()
            candidate = (media_root / rel_str).resolve()
            candidate.relative_to(media_root)
        except (OSError, ValueError):
            return _http_error(404, "not found")
        if not candidate.is_file():
            return _http_error(404, "not found")
        try:
            body = candidate.read_bytes()
        except OSError:
            return _http_error(500, "read error")
        mime, _ = mimetypes.guess_type(candidate.name)
        if mime not in _MEDIA_ALLOWED_MIMES:
            mime = "application/octet-stream"
        return _http_response(
            body,
            content_type=mime,
            extra_headers=[
                ("Cache-Control", "private, max-age=31536000, immutable"),
                # Paired with the MIME whitelist above: prevents browsers from
                # MIME-sniffing an octet-stream fallback into executable HTML.
                ("X-Content-Type-Options", "nosniff"),
            ],
        )

    def _handle_session_delete(self, request: WsRequest, key: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        if self._session_manager is None:
            return _http_error(503, "session manager unavailable")
        decoded_key = _decode_api_key(key)
        if decoded_key is None:
            return _http_error(400, "invalid session key")
        # Same boundary as ``_handle_session_messages``: the webui may only
        # mutate websocket sessions, and deletion really does unlink the local
        # JSONL, so keep the blast radius narrow and explicit.
        if not self._is_webui_session_key(decoded_key):
            return _http_error(404, "session not found")

        # Parse role/user_id to find user workspace
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""

        if role and user_id:
            # Reconstruct full key with user prefix for user workspace
            full_key = f"{role}:{user_id}:{decoded_key}"
            user_sessions_dir = Path.home() / ".nanobot" / "users" / role / user_id / "sessions"
            # Use safe_key to match file naming convention (colons -> underscores)
            from nanobot.session.manager import SessionManager
            safe_key = SessionManager.safe_key(full_key)
            session_file = user_sessions_dir / f"{safe_key}.jsonl"
            if not session_file.exists():
                return _http_json_response({"deleted": False})
            try:
                session_file.unlink()
                return _http_json_response({"deleted": True})
            except OSError as e:
                logger.warning("Failed to delete user session {}: {}", full_key, e)
                return _http_error(500, "Failed to delete session")
        else:
            deleted = self._session_manager.delete_session(decoded_key)
            return _http_json_response({"deleted": bool(deleted)})

    def _handle_agents_list(self, request: WsRequest) -> Response:
        """List all available agents."""
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        if not hasattr(self, '_agent_manager') or self._agent_manager is None:
            return _http_json_response({"agents": [], "has_multi_agent": False})
        agents = self._agent_manager.list_agents()
        return _http_json_response({"agents": agents, "has_multi_agent": True})

    def _handle_agents_current(self, request: WsRequest) -> Response:
        """Get the current active agent."""
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        if not hasattr(self, '_agent_manager') or self._agent_manager is None:
            return _http_json_response({"agent": None, "has_multi_agent": False})
        active_agent = self._agent_manager.get_active_agent()
        if active_agent:
            return _http_json_response({"agent": active_agent.to_dict(), "has_multi_agent": True})
        return _http_json_response({"agent": None, "has_multi_agent": True})

    def _handle_agents_switch(self, request: WsRequest, agent_name: str) -> Response:
        """Switch to a different agent."""
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        if not hasattr(self, '_agent_manager') or self._agent_manager is None:
            return _http_error(503, "multi-agent system not configured")
        success = self._agent_manager.switch_agent(agent_name)
        if success:
            return _http_json_response({"success": True, "agent": agent_name})
        return _http_error(404, "agent not found")

    def _serve_static(self, request_path: str) -> Response | None:
        """Resolve *request_path* against the built SPA directory; SPA fallback to index.html."""
        assert self._static_dist_path is not None
        rel = request_path.lstrip("/")
        if not rel:
            rel = "index.html"
        # Reject path-traversal attempts and absolute targets.
        if ".." in rel.split("/") or rel.startswith("/"):
            return _http_error(403, "Forbidden")
        candidate = (self._static_dist_path / rel).resolve()
        try:
            candidate.relative_to(self._static_dist_path)
        except ValueError:
            return _http_error(403, "Forbidden")
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
            return _http_error(500, "Internal Server Error")
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
        return _http_response(
            body,
            status=200,
            content_type=ctype,
            extra_headers=[("Cache-Control", cache)],
        )

    # -- Course HTTP handlers -------------------------------------------------

    async def _handle_courses_list(self, request: WsRequest) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""

        if role == "teacher":
            courses = await self.storage.get_teacher_courses(user_id)
        elif role == "student":
            courses = await self.storage.get_student_courses(user_id)
        else:
            # Public courses only
            all_courses = await self.storage.list_courses()
            courses = [c for c in all_courses if c.get("is_public")]
        return _http_json_response({"courses": courses})

    async def _handle_courses_create(self, request: WsRequest) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        logger.info("[courses_create] role={!r} user_id={!r}", role, user_id)
        if role != "teacher":
            return _http_error(403, "Only teachers can create courses")
        payload = self._parse_mutation_data(query)
        if isinstance(payload, Response):
            return payload
        course_name = payload.get("courseName", "").strip()
        subject = payload.get("subject", "").strip()
        grade = payload.get("grade", "").strip()
        if not course_name:
            return _http_error(400, "courseName is required")

        # Check course limit per teacher
        teacher_courses = await self.storage.get_teacher_courses(user_id)
        if len(teacher_courses) >= 100:
            return _http_error(400, "Course limit reached (max 100)")

        course_id = self._generate_id()
        join_code = self._generate_join_code()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        display_name = payload.get("teacherName") or user_id

        course_data = {
            "course_id": course_id,
            "course_name": course_name,
            "subject": subject,
            "grade": grade,
            "description": payload.get("description", ""),
            "teacher_id": user_id,
            "teacher_role": "teacher",
            "teacher_name": display_name,
            "join_code": join_code,
            "is_public": payload.get("isPublic", True),
            "max_members": payload.get("maxMembers", 50),
            "created_at": now,
            "updated_at": now,
        }
        course = await self.storage.create_course(course_data)

        # Add teacher as course member automatically
        await self.storage.add_course_member(course_id, user_id, "teacher", display_name)

        logger.info("Course created: {} ({}) by {}", course_name, course_id, user_id)
        return _http_json_response({"ok": True, "course": course})

    async def _handle_courses_join(self, request: WsRequest) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        if role != "student":
            return _http_error(403, "Only students can join courses")
        payload = self._parse_mutation_data(query)
        if isinstance(payload, Response):
            return payload
        join_code = payload.get("joinCode", "").strip()
        if not join_code:
            return _http_error(400, "joinCode is required")

        # Find course by join code
        course = await self.storage.get_course_by_join_code(join_code)
        if not course:
            return _http_error(404, "Invalid join code")

        course_id = course["course_id"]

        # Check if already a member
        if await self.storage.is_course_member(course_id, user_id):
            return _http_json_response({"ok": True, "course": course, "message": "Already a member"})

        # Check member limit
        members_count = await self.storage.get_course_members_count(course_id)
        max_members = course.get("max_members", 50)
        if members_count >= max_members:
            return _http_error(400, "Course is full")

        display_name = payload.get("displayName") or user_id
        await self.storage.add_course_member(course_id, user_id, "student", display_name)

        logger.info("Student {} joined course {} ({})", user_id, course.get("course_name"), course_id)
        return _http_json_response({"ok": True, "course": course})

    async def _handle_course_detail(self, request: WsRequest, course_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        return _http_json_response({"course": course})

    async def _handle_course_members(self, request: WsRequest, course_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        members = await self.storage.get_course_members(course_id)
        return _http_json_response({"members": members})

    async def _handle_lessons_list(self, request: WsRequest, course_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        lessons = await self.storage.get_course_lessons(course_id)
        return _http_json_response({"lessons": lessons})

    async def _handle_lesson_detail(self, request: WsRequest, course_id: str, lesson_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")

        # Try to find lesson by ID (as integer) or by lesson_id string
        try:
            lesson_id_int = int(lesson_id)
            lesson = await self.storage.get_lesson(lesson_id_int)
        except ValueError:
            return _http_error(400, "Invalid lesson ID")

        if not lesson:
            return _http_error(404, "Lesson not found")
        return _http_json_response({"lesson": lesson})

    async def _handle_homework_list(self, request: WsRequest, course_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        homework = await self.storage.get_course_homework(course_id)
        return _http_json_response({"homework": homework})

    async def _handle_homework_create(self, request: WsRequest, course_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        logger.info("[homework_create] role={!r} user_id={!r} course_id={!r}", role, user_id, course_id)
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        logger.info("[homework_create] course.teacher_id={!r}", course.get("teacher_id"))
        if course.get("teacher_id") != user_id:
            return _http_error(403, "Only the course owner can create homework")
        payload = self._parse_mutation_data(query)
        if isinstance(payload, Response):
            return payload
        title = payload.get("title", "").strip()
        if not title:
            return _http_error(400, "title is required")

        hw_id = f"hw{self._generate_id()}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        hw_data = {
            "hw_id": hw_id,
            "course_id": course_id,
            "title": title,
            "description": payload.get("description", ""),
            "questions": payload.get("questions", []),
            "total_points": payload.get("totalPoints", 0),
            "deadline": payload.get("deadline", ""),
            "created_at": now,
            "created_by": user_id,
            "created_by_role": "teacher",
        }
        homework = await self.storage.create_homework(hw_data)
        logger.info("Homework created: {} in course {} by {}", title, course_id, user_id)
        return _http_json_response({"ok": True, "homework": homework})

    async def _handle_homework_detail(self, request: WsRequest, course_id: str, hw_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        hw = await self.storage.get_homework(hw_id)
        if not hw:
            return _http_error(404, "Homework not found")
        return _http_json_response({"homework": hw})

    async def _handle_homework_submit(self, request: WsRequest, course_id: str, hw_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        role = _query_first(query, "role") or ""
        user_id = _query_first(query, "user_id") or ""
        if role != "student":
            return _http_error(403, "Only students can submit homework")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        hw = await self.storage.get_homework(hw_id)
        if not hw:
            return _http_error(404, "Homework not found")
        payload = self._parse_mutation_data(query)
        if isinstance(payload, Response):
            return payload
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        submission_data = {
            "hw_id": hw_id,
            "student_id": user_id,
            "student_role": "student",
            "answers": payload.get("answers", {}),
            "submitted_at": now,
            "status": "submitted",
            "score": 0,
            "feedback": {},
            "total_score": hw.get("total_points", 0),
            "graded_at": None,
            "graded_by": None,
        }
        await self.storage.create_submission(submission_data)
        logger.info("Homework {} submitted by student {} in course {}", hw_id, user_id, course_id)
        return _http_json_response({"ok": True})

    async def _handle_homework_submissions(self, request: WsRequest, course_id: str, hw_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        submissions = await self.storage.get_homework_submissions(hw_id)
        return _http_json_response({"submissions": submissions})

    async def _handle_submission_detail(self, request: WsRequest, course_id: str, hw_id: str, student_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        submission = await self.storage.get_submission(hw_id, student_id)
        if not submission:
            return _http_error(404, "Submission not found")
        return _http_json_response({"submission": submission})

    async def _handle_homework_grade(self, request: WsRequest, course_id: str, hw_id: str) -> Response:
        if not self._check_api_token(request):
            return _http_error(401, "Unauthorized")
        query = _parse_query(request.path)
        user_id = _query_first(query, "user_id") or ""
        course = await self.storage.get_course(course_id)
        if not course:
            return _http_error(404, "Course not found")
        if course.get("teacher_id") != user_id:
            return _http_error(403, "Only the course owner can grade")
        payload = self._parse_mutation_data(query)
        if isinstance(payload, Response):
            return payload
        student_id = payload.get("studentId", "").strip()
        if not student_id:
            return _http_error(400, "studentId is required")
        submission = await self.storage.get_submission(hw_id, student_id)
        if not submission:
            return _http_error(404, "Submission not found")

        submission_update = {
            "status": "graded",
            "score": payload.get("score", 0),
            "feedback": payload.get("feedback", {}),
            "graded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "graded_by": user_id,
            "graded_by_role": "teacher",
        }
        updated = await self.storage.update_submission(submission["id"], submission_update)
        logger.info("Homework {} graded for student {} in course {}", hw_id, student_id, course_id)
        return _http_json_response({"ok": True, "submission": updated})

    def _authorize_websocket_handshake(self, connection: Any, query: dict[str, list[str]]) -> Any:
        supplied = _query_first(query, "token")
        static_token = self.config.token.strip()

        if static_token:
            if supplied and hmac.compare_digest(supplied, static_token):
                return None
            if supplied and self._take_issued_token_if_valid(supplied):
                return None
            return connection.respond(401, "Unauthorized")

        if self.config.websocket_requires_token:
            if supplied and self._take_issued_token_if_valid(supplied):
                return None
            return connection.respond(401, "Unauthorized")

        if supplied:
            self._take_issued_token_if_valid(supplied)
        return None

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

        self._server_task = asyncio.create_task(runner())
        await self._server_task

    async def _connection_loop(self, connection: Any) -> None:
        request = connection.request
        path_part = request.path if request else "/"
        _, query = _parse_request_path(path_part)
        client_id_raw = _query_first(query, "client_id")
        client_id = client_id_raw.strip() if client_id_raw else ""
        if not client_id:
            client_id = f"anon-{uuid.uuid4().hex[:12]}"
        elif len(client_id) > 128:
            logger.warning("websocket: client_id too long ({} chars), truncating", len(client_id))
            client_id = client_id[:128]

        # Extract role/user_id from token metadata
        token = _query_first(query, "token") or ""
        conn_meta: dict[str, str] = {}
        if token and token in self._token_metadata:
            conn_meta = self._token_metadata.pop(token, {})
            logger.info("websocket: token metadata loaded for role={}, user_id={}", conn_meta.get("role"), conn_meta.get("user_id"))
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
                    await self._dispatch_envelope(connection, client_id, envelope)
                    continue

                content = _parse_inbound_payload(raw)
                if content is None:
                    continue
                msg_meta = {"remote": getattr(connection, "remote_address", None)}
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
        t = envelope.get("type")
        if t == "new_chat":
            new_id = str(uuid.uuid4())
            self._attach(connection, new_id)
            await self._send_event(connection, "attached", chat_id=new_id)
            return
        if t == "attach":
            cid = envelope.get("chat_id")
            if not _is_valid_chat_id(cid):
                await self._send_event(connection, "error", detail="invalid chat_id")
                return
            self._attach(connection, cid)
            await self._send_event(connection, "attached", chat_id=cid)
            return
        if t == "message":
            cid = envelope.get("chat_id")
            content = envelope.get("content")
            if not _is_valid_chat_id(cid):
                await self._send_event(connection, "error", detail="invalid chat_id")
                return
            if not isinstance(content, str):
                await self._send_event(connection, "error", detail="missing content")
                return

            raw_media = envelope.get("media")
            media_paths: list[str] = []
            if raw_media is not None:
                if not isinstance(raw_media, list):
                    await self._send_event(
                        connection, "error",
                        detail="image_rejected", reason="malformed",
                    )
                    return
                media_paths, reason = self._save_envelope_media(raw_media)
                if reason is not None:
                    await self._send_event(
                        connection, "error",
                        detail="image_rejected", reason=reason,
                    )
                    return

            # Allow image-only turns (content may be empty when media is attached).
            if not content.strip() and not media_paths:
                await self._send_event(connection, "error", detail="missing content")
                return

            # Auto-attach on first use so clients can one-shot without a separate attach.
            self._attach(connection, cid)
            msg_meta = {"remote": getattr(connection, "remote_address", None)}
            conn_meta = getattr(self, '_conn_metadata', {}).get(connection, {})
            msg_meta.update(conn_meta)
            logger.debug("WS message: conn_meta={}, msg_meta={}", conn_meta, msg_meta)
            await self._handle_message(
                sender_id=client_id,
                chat_id=cid,
                content=content,
                media=media_paths or None,
                metadata=msg_meta,
            )
            return
        if t == "save_source":
            path = envelope.get("path")
            content = envelope.get("content")
            if not path or not isinstance(path, str):
                await self._send_event(connection, "error", detail="missing path")
                return
            if not isinstance(content, str):
                await self._send_event(connection, "error", detail="missing content")
                return
            conn_meta = getattr(self, '_conn_metadata', {}).get(connection, {})
            role = conn_meta.get("role", "")
            user_id = conn_meta.get("user_id", "")
            if not role or not user_id:
                await self._send_event(connection, "error", detail="not authenticated")
                return
            if ".." in path:
                await self._send_event(connection, "error", detail="invalid path")
                return
            source_dir = Path.home() / ".nanobot" / "users" / role / user_id / "source"
            target = (source_dir / path).resolve()
            if not str(target).startswith(str(source_dir.resolve())):
                await self._send_event(connection, "error", detail="access denied")
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            await self._send_event(connection, "source_saved", path=path)
            return

        await self._send_event(connection, "error", detail=f"unknown type: {t!r}")

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
        self._subs.clear()
        self._conn_chats.clear()
        self._conn_default.clear()
        self._issued_tokens.clear()
        self._api_tokens.clear()

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
        if msg.metadata.get("_tool_hint"):
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
        for connection in conns:
            await self._safe_send_to(connection, raw, label=" stream ")
