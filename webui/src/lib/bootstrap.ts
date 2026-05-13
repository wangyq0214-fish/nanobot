import type { BootstrapResponse, UserRole } from "./types";

/**
 * Fetch a short-lived token + the WebSocket path from the gateway's
 * ``/webui/bootstrap`` endpoint. Localhost-only on the server side.
 *
 * @param role - User role (student/teacher/researcher) for role-based routing
 * @param userId - User identifier for per-user workspace isolation
 */
export async function fetchBootstrap(
  baseUrl: string = "",
  role?: UserRole,
  userId?: string,
): Promise<BootstrapResponse> {
  const params = new URLSearchParams();
  if (role) params.set("role", role);
  if (userId) params.set("user_id", userId);
  const qs = params.toString();
  const url = `${baseUrl}/webui/bootstrap${qs ? `?${qs}` : ""}`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "same-origin",
  });
  if (!res.ok) {
    throw new Error(`bootstrap failed: HTTP ${res.status}`);
  }
  const body = (await res.json()) as BootstrapResponse;
  if (!body.token || !body.ws_path) {
    throw new Error("bootstrap response missing token or ws_path");
  }
  return body;
}

/** Derive a WebSocket URL from the current window location and the server-provided path.
 *
 * Keeps the path segment exactly as the server registered it: the root ``/``
 * stays ``/`` and non-root paths are not given an extra trailing slash. This
 * matters because some WS servers dispatch handshakes based on the literal
 * path, not a normalised form.
 */
export function deriveWsUrl(wsPath: string, token: string): string {
  const path = wsPath && wsPath.startsWith("/") ? wsPath : `/${wsPath || ""}`;
  const query = `?token=${encodeURIComponent(token)}`;
  if (typeof window === "undefined") {
    return `ws://127.0.0.1:8765${path}${query}`;
  }
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  const host = window.location.host;
  return `${scheme}://${host}${path}${query}`;
}

export interface UserApiResponse {
  ok: boolean;
  user?: {
    role: UserRole;
    userId: string;
    displayName: string;
    registeredAt: string;
  };
  error?: string;
}

/**
 * Register a new user with the gateway.
 */
export async function registerUser(
  baseUrl: string = "",
  role: UserRole,
  userId: string,
  displayName?: string,
): Promise<UserApiResponse> {
  const params = new URLSearchParams({
    role,
    user_id: userId,
    display_name: displayName || userId,
  });
  const res = await fetch(`${baseUrl}/api/users/register?${params}`);
  return res.json() as Promise<UserApiResponse>;
}

/**
 * Validate an existing user with the gateway.
 */
export async function validateUser(
  baseUrl: string = "",
  role: UserRole,
  userId: string,
): Promise<UserApiResponse> {
  const params = new URLSearchParams({ role, user_id: userId });
  const res = await fetch(`${baseUrl}/api/users/validate?${params}`);
  return res.json() as Promise<UserApiResponse>;
}
