import type { ChatSummary } from "./types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(
  url: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(url, {
    ...(init ?? {}),
    headers: {
      ...(init?.headers ?? {}),
      Authorization: `Bearer ${token}`,
    },
    credentials: "same-origin",
  });
  if (!res.ok) {
    throw new ApiError(res.status, `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

function splitKey(key: string): { channel: string; chatId: string } {
  const idx = key.indexOf(":");
  if (idx === -1) return { channel: "", chatId: key };
  return { channel: key.slice(0, idx), chatId: key.slice(idx + 1) };
}

export async function listSessions(
  token: string,
  base: string = "",
  role?: string,
  userId?: string,
): Promise<ChatSummary[]> {
  type Row = {
    key: string;
    created_at: string | null;
    updated_at: string | null;
    preview?: string;
  };
  const params = new URLSearchParams();
  if (role) params.set("role", role);
  if (userId) params.set("user_id", userId);
  const qs = params.toString();
  const url = `${base}/api/sessions${qs ? `?${qs}` : ""}`;
  const body = await request<{ sessions: Row[] }>(url, token);
  return body.sessions.map((s) => ({
    key: s.key,
    ...splitKey(s.key),
    createdAt: s.created_at,
    updatedAt: s.updated_at,
    preview: s.preview ?? "",
  }));
}

/** Signed image URL attached to a historical user message. The server
 * emits these in place of raw on-disk paths so the client can render
 * previews without learning where media lives on disk. Each URL is a
 * self-authenticating ``/api/media/...`` route (see backend
 * ``_sign_media_path``) safe to drop into an ``<img src>`` attribute. */
export interface SessionMediaUrl {
  url: string;
  name?: string;
}

export async function fetchSessionMessages(
  token: string,
  key: string,
  base: string = "",
  role?: string,
  userId?: string,
): Promise<{
  key: string;
  created_at: string | null;
  updated_at: string | null;
  messages: Array<{
    role: string;
    content: string;
    timestamp?: string;
    tool_calls?: unknown;
    tool_call_id?: string;
    name?: string;
    /** Present on ``user`` turns that attached images. Paths have already
     * been stripped server-side; only the signed fetch URLs survive. */
    media_urls?: SessionMediaUrl[];
  }>;
}> {
  const params = new URLSearchParams();
  if (role) params.set("role", role);
  if (userId) params.set("user_id", userId);
  const qs = params.toString();
  const url = `${base}/api/sessions/${encodeURIComponent(key)}/messages${qs ? `?${qs}` : ""}`;
  return request(url, token);
}

export async function deleteSession(
  token: string,
  key: string,
  base: string = "",
  role?: string,
  userId?: string,
): Promise<boolean> {
  const params = new URLSearchParams();
  if (role) params.set("role", role);
  if (userId) params.set("user_id", userId);
  const qs = params.toString();
  const url = `${base}/api/sessions/${encodeURIComponent(key)}/delete${qs ? `?${qs}` : ""}`;
  const body = await request<{ deleted: boolean }>(url, token);
  return body.deleted;
}
