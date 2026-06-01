"""Authentication and user management for the WebSocket channel."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import shutil
import time
from pathlib import Path
from typing import Any

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.api.utils import (
    bearer_token,
    http_error,
    http_json_response,
    http_response,
    parse_query,
    query_first,
)

_MAX_ISSUED_TOKENS = 10_000


def _issue_route_secret_matches(headers: Any, configured_secret: str) -> bool:
    """Return True if the token-issue HTTP request carries credentials matching the secret."""
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


class AuthManager:
    """Manages tokens, user registration and validation."""

    def __init__(
        self,
        *,
        token: str = "",
        token_issue_secret: str = "",
        token_ttl_s: int = 300,
        websocket_requires_token: bool = True,
        ws_path: str = "/",
    ):
        self._token = token.strip()
        self._token_issue_secret = token_issue_secret.strip()
        self._token_ttl_s = token_ttl_s
        self._websocket_requires_token = websocket_requires_token
        self._ws_path = ws_path

        # Single-use tokens consumed at WebSocket handshake.
        self._issued_tokens: dict[str, float] = {}
        # Multi-use tokens for the embedded webui's REST surface.
        self._api_tokens: dict[str, float] = {}
        # Token metadata: role, user_id associated with each token.
        self._token_metadata: dict[str, dict[str, str]] = {}

    # -- Token management ----------------------------------------------------

    def _purge_expired(self) -> None:
        """Remove expired tokens from both pools and metadata."""
        now = time.monotonic()
        for pool in (self._issued_tokens, self._api_tokens):
            for token_key, expiry in list(pool.items()):
                if now > expiry:
                    pool.pop(token_key, None)
                    self._token_metadata.pop(token_key, None)

    def issue_token(self, *, role: str = "", user_id: str = "") -> str:
        """Issue a new token registered in both pools. Returns the token string."""
        self._purge_expired()
        if (
            len(self._issued_tokens) >= _MAX_ISSUED_TOKENS
            or len(self._api_tokens) >= _MAX_ISSUED_TOKENS
        ):
            raise RuntimeError("too many outstanding tokens")

        token = f"nbwt_{secrets.token_urlsafe(32)}"
        expiry = time.monotonic() + float(self._token_ttl_s)
        self._issued_tokens[token] = expiry
        self._api_tokens[token] = expiry

        if role or user_id:
            self._token_metadata[token] = {"role": role, "user_id": user_id}

        return token

    def take_issued_token(self, token_value: str | None) -> bool:
        """Validate and consume one issued token (single use)."""
        if not token_value:
            return False
        self._purge_expired()
        expiry = self._issued_tokens.pop(token_value, None)
        if expiry is None:
            return False
        if time.monotonic() > expiry:
            return False
        return True

    def check_api_token(self, request: WsRequest) -> bool:
        """Validate a request against the API token pool (multi-use, TTL-bound)."""
        self._purge_expired()
        token = bearer_token(request.headers) or query_first(
            parse_query(request.path), "token"
        )
        if not token:
            return False
        expiry = self._api_tokens.get(token)
        if expiry is None or time.monotonic() > expiry:
            self._api_tokens.pop(token, None)
            return False
        return True

    def get_token_metadata(self, token: str) -> dict[str, str]:
        """Return metadata for a token without removing it."""
        return self._token_metadata.get(token, {})

    def pop_token_metadata(self, token: str) -> dict[str, str]:
        """Pop and return metadata for a token (used during WS handshake)."""
        return self._token_metadata.pop(token, {})

    # -- HTTP handlers -------------------------------------------------------

    def handle_token_issue_http(self, connection: Any, request: WsRequest) -> Any:
        """Handle legacy token issue endpoint."""
        if self._token_issue_secret:
            if not _issue_route_secret_matches(request.headers, self._token_issue_secret):
                return connection.respond(401, "Unauthorized")
        else:
            logger.warning(
                "websocket: token_issue_path is set but token_issue_secret is empty; "
                "any client can obtain connection tokens — set token_issue_secret for production."
            )
        self._purge_expired()
        if len(self._issued_tokens) >= _MAX_ISSUED_TOKENS:
            logger.error(
                "websocket: too many outstanding issued tokens ({}), rejecting issuance",
                len(self._issued_tokens),
            )
            return http_json_response({"error": "too many outstanding tokens"}, status=429)

        token = self.issue_token()
        return http_json_response({"token": token, "expires_in": self._token_ttl_s})

    def handle_webui_bootstrap(
        self, connection: Any, request: WsRequest | None = None, *, model_name: str | None = None
    ) -> Response:
        """Handle WebUI bootstrap: mint tokens for the embedded UI."""
        self._purge_expired()
        if (
            len(self._issued_tokens) >= _MAX_ISSUED_TOKENS
            or len(self._api_tokens) >= _MAX_ISSUED_TOKENS
        ):
            return http_response(
                http_json_response({"error": "too many outstanding tokens"}, status=429).body,
                status=429,
                content_type="application/json; charset=utf-8",
            )

        role = ""
        user_id = ""
        if request:
            query = parse_query(request.path)
            role = query_first(query, "role") or ""
            user_id = query_first(query, "user_id") or ""

        try:
            token = self.issue_token(role=role, user_id=user_id)
        except RuntimeError:
            return http_json_response({"error": "too many outstanding tokens"}, status=429)

        logger.info(
            "bootstrap: issued token with role={}, user_id={}, metadata_stored={}",
            role, user_id, token in self._token_metadata,
        )

        resp: dict[str, Any] = {
            "token": token,
            "ws_path": self._ws_path,
            "expires_in": self._token_ttl_s,
            "model_name": model_name,
        }
        if role:
            resp["role"] = role
        if user_id:
            resp["user_id"] = user_id
        return http_json_response(resp)

    # -- WS handshake authorization ------------------------------------------

    def authorize_websocket_handshake(
        self, connection: Any, query: dict[str, list[str]]
    ) -> Any:
        """Authorize a WebSocket handshake. Returns None on success, or an HTTP error response."""
        supplied = query_first(query, "token")

        if self._token:
            if supplied and hmac.compare_digest(supplied, self._token):
                return None
            if supplied and self.take_issued_token(supplied):
                return None
            return connection.respond(401, "Unauthorized")

        if self._websocket_requires_token:
            if supplied and self.take_issued_token(supplied):
                return None
            return connection.respond(401, "Unauthorized")

        if supplied:
            self.take_issued_token(supplied)
        return None

    # -- User management -----------------------------------------------------

    @staticmethod
    def create_user_workspace(role: str, user_id: str) -> None:
        """Create user workspace with USER.md and directory structure."""
        templates_dir = Path.home() / ".nanobot" / "templates" / role
        if not templates_dir.is_dir():
            logger.warning("Template directory not found: {}", templates_dir)
            return

        users_dir = Path.home() / ".nanobot" / "users" / role / user_id
        if users_dir.exists():
            return

        users_dir.mkdir(parents=True, exist_ok=True)
        user_md = templates_dir / "USER.md"
        if user_md.is_file():
            shutil.copy2(user_md, users_dir / "USER.md")
        (users_dir / "sessions").mkdir(exist_ok=True)
        (users_dir / "source").mkdir(exist_ok=True)
        (users_dir / "memory").mkdir(exist_ok=True)
        logger.info("Created workspace for user: {} (role={})", user_id, role)

    async def handle_users_register(
        self, request: WsRequest, *, storage: Any
    ) -> Response:
        """Handle user registration."""
        query = parse_query(request.path)
        role = query_first(query, "role") or ""
        user_id = query_first(query, "user_id") or ""
        display_name = query_first(query, "display_name") or user_id
        password = query_first(query, "password") or ""

        if not role or not user_id:
            return http_error(400, "role and user_id are required")
        if role not in ("student", "teacher", "researcher"):
            return http_error(400, "Invalid role")
        if len(user_id) > 64:
            return http_error(400, "user_id too long (max 64)")
        if not password:
            return http_error(400, "password is required")

        existing = await storage.get_user(role, user_id)
        if existing:
            return http_error(409, "User already exists")

        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

        user_data = {
            "role": role,
            "user_id": user_id,
            "display_name": display_name,
            "password_hash": password_hash,
            "password_salt": salt,
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        user = await storage.create_user(user_data)
        self.create_user_workspace(role, user_id)

        logger.info("Registered user: {} (role={})", user_id, role)
        return http_json_response({"ok": True, "user": user})

    async def handle_users_validate(
        self, request: WsRequest, *, storage: Any
    ) -> Response:
        """Handle user validation / login."""
        query = parse_query(request.path)
        role = query_first(query, "role") or ""
        user_id = query_first(query, "user_id") or ""
        password = query_first(query, "password") or ""

        if not role or not user_id:
            return http_error(400, "role and user_id are required")

        user = await storage.get_user(role, user_id)
        if not user:
            return http_error(404, "User not found")

        if password and user.get("password_hash"):
            salt = user.get("password_salt", "")
            expected_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            if expected_hash != user.get("password_hash"):
                return http_error(401, "Invalid password")

        try:
            token = self.issue_token()
        except RuntimeError:
            return http_json_response({"error": "too many outstanding tokens"}, status=429)

        return http_json_response({"ok": True, "user": user, "token": token})
