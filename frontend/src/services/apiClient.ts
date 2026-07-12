// Thin API client wrapper. Uses fetch with VITE_API_BASE_URL.
// Services can call this OR the mock store, depending on VITE_USE_MOCKS.
const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const USE_MOCKS = (import.meta.env.VITE_USE_MOCKS ?? "false") === "true";

// ─── Token store ──────────────────────────────────────────────────────────────
const TOKEN_KEY = "assetflow.token";

export function getToken(): string | null {
  return typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_KEY) : null;
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

// ─── Core request ─────────────────────────────────────────────────────────────
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...init, headers });

  // 401 → clear credentials and redirect to login (outside React tree)
  // Skip redirect on public pages where 401 is expected (not logged in yet)
  const PUBLIC_PATHS = ["/login", "/signup", "/forgot-password"];
  const isPublicPage = PUBLIC_PATHS.some((p) => window.location.pathname.startsWith(p));
  if (res.status === 401) {
    setToken(null);
    window.localStorage.removeItem("assetflow.userId");
    if (!isPublicPage) {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    }
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = text || res.statusText || "Request failed";
    try {
      const payload = JSON.parse(text) as { detail?: unknown; message?: unknown };
      const detail = payload.detail ?? payload.message;
      if (typeof detail === "string") message = detail;
      else if (detail && typeof detail === "object" && "message" in detail) {
        const nested = (detail as { message?: unknown }).message;
        if (typeof nested === "string") message = nested;
      }
    } catch {
      // Keep raw text when response is not JSON.
    }
    throw new Error(message);
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ─── Public client ────────────────────────────────────────────────────────────
export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// Simulated network latency for mock services
export const mockDelay = (ms = 200) => new Promise((r) => setTimeout(r, ms));
