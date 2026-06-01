"""Declarative HTTP route dispatcher for the WebSocket channel.

Replaces the monolithic if/elif chain in ``_dispatch_http`` with a
pattern-based route table.  Each route is a compiled regex with named
capture groups; when a request path matches, the captured groups are
passed as keyword arguments to the handler.

Usage::

    router = Router()
    router.add("/api/users/register", handle_users_register)
    router.add("/api/courses/(?P<course_id>[^/]+)", handle_course_detail)

    resp = await router.dispatch(request, got, context)
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Awaitable, Callable

from loguru import logger

from nanobot.api.utils import http_error

# A handler receives ``(request, **params)`` where *params* are the named
# groups from the regex match.  Sync handlers must return a Response;
# async handlers are ``await``ed.
SyncHandler = Callable[..., Any]
AsyncHandler = Callable[..., Awaitable[Any]]


def _accepted_params(fn: Callable[..., Any]) -> set[str]:
    """Return the set of keyword parameter names accepted by *fn*.

    Handles plain functions, bound methods, and ``**kwargs``-style
    callables.  Results are cached per-function for efficiency.
    """
    sig = inspect.signature(fn)
    params: set[str] = set()
    for p in sig.parameters.values():
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
            params.add(p.name)
        elif p.kind is p.VAR_KEYWORD:
            # Handler accepts **kwargs — pass everything.
            return set()
    return params


class Route:
    """A single compiled route entry."""

    __slots__ = ("pattern", "handler", "is_async", "name", "takes_request", "_accepted")

    def __init__(
        self,
        pattern: str,
        handler: SyncHandler | AsyncHandler,
        *,
        is_async: bool = False,
        name: str = "",
        takes_request: bool = True,
    ) -> None:
        self.pattern = re.compile(f"^{pattern}$")
        self.handler = handler
        self.is_async = is_async
        self.name = name or pattern
        self.takes_request = takes_request
        self._accepted = _accepted_params(handler)


class Router:
    """Declarative HTTP route table with regex matching.

    Routes are tried in registration order — first match wins.
    """

    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add(
        self,
        pattern: str,
        handler: SyncHandler | AsyncHandler,
        *,
        is_async: bool = False,
        name: str = "",
        takes_request: bool = True,
    ) -> None:
        """Register a route.

        Args:
            pattern: Regex pattern with named groups (e.g. ``/api/courses/(?P<id>[^/]+)``).
            handler: Callable to invoke on match.
            is_async: Whether the handler is a coroutine function.
            name: Optional debug label.
            takes_request: Whether the handler expects the request object
                as its first argument.  Set to ``False`` for handlers that
                only need the URL parameters (e.g. media fetch).
        """
        self._routes.append(
            Route(pattern, handler, is_async=is_async, name=name, takes_request=takes_request)
        )

    async def dispatch(
        self,
        request: Any,
        path: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Match *path* against the route table and invoke the first hit.

        Args:
            request: The raw HTTP request object.
            path: Normalized path (no query string).
            context: Extra keyword arguments forwarded to every handler
                (e.g. ``storage=..., check_token=...``).

        Returns:
            The handler's return value, or ``None`` if no route matched.
        """
        ctx = context or {}
        for route in self._routes:
            m = route.pattern.match(path)
            if m is None:
                continue
            params = m.groupdict()
            # Only pass context keys the handler actually accepts, so
            # handlers that don't expect ``storage`` or ``check_token``
            # don't choke on unexpected keyword arguments.
            if route._accepted:
                filtered = {k: v for k, v in ctx.items() if k in route._accepted}
            else:
                filtered = ctx  # handler accepts **kwargs
            try:
                if route.takes_request:
                    if route.is_async:
                        return await route.handler(request, **params, **filtered)
                    return route.handler(request, **params, **filtered)
                else:
                    if route.is_async:
                        return await route.handler(**params, **filtered)
                    return route.handler(**params, **filtered)
            except Exception as e:
                logger.error(
                    "[router] handler {} error: {} {}",
                    route.name,
                    type(e).__name__,
                    e,
                )
                return http_error(500, str(e))
        return None
