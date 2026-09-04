const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type ProviderInfo = {
  id: "openai" | "anthropic" | "gemini" | "xai" | "zai";
  name: string;
  available: boolean;
  default_model: string;
};

export type User = { id: number; email: string };
export type TokenResponse = { access_token: string; token_type: string };
export type EVUDocument = {
  id: number;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  chunk_count: number;
  created_at: string;
};

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed: ${response.status}`);
  return data as T;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Login failed");
  return data as TokenResponse;
}

export function register(email: string, password: string): Promise<User> {
  return api<User>("/api/v1/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function getMe(token: string) {
  return api<User>("/api/v1/auth/me", { headers: { Authorization: `Bearer ${token}` } });
}

export function getProviders() {
  return api<ProviderInfo[]>("/api/v1/providers");
}

export function getConversations(token: string) {
  return api<{ id: number; title: string; created_at: string }[]>("/api/v1/conversations", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getConversation(token: string, conversationId: number) {
  return api<{
    id: number;
    title: string;
    created_at: string;
    messages: { id: number; role: string; content: string; created_at: string }[];
  }>(`/api/v1/conversations/${conversationId}`, { headers: { Authorization: `Bearer ${token}` } });
}

export function createConversation(token: string, title = "New conversation") {
  return api<{ id: number; title: string; created_at: string }>("/api/v1/conversations", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ title }),
  });
}

export function getDocuments(token: string) {
  return api<EVUDocument[]>("/api/v1/documents", { headers: { Authorization: `Bearer ${token}` } });
}

export async function uploadDocument(token: string, file: File): Promise<EVUDocument> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_URL}/api/v1/documents/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Upload failed");
  return data as EVUDocument;
}

export async function deleteDocument(token: string, documentId: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Delete failed");
  }
}

export async function streamChat(
  path: string,
  token: string,
  body: unknown,
  onDelta: (delta: string) => void
): Promise<void> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Streaming request failed: ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";
      for (const event of events) {
        const line = event.split("\n").find((item) => item.startsWith("data: "));
        if (!line) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") return;
        const data = JSON.parse(payload) as { delta?: string; error?: string };
        if (data.error) throw new Error(data.error);
        if (data.delta) onDelta(data.delta);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export { API_URL };

export type AgentToolResult = {
  step: number;
  tool: string;
  input: string;
  output: string;
  success: boolean;
};

export type AgentResponse = {
  response: string;
  provider: string;
  model: string | null;
  agent_used: boolean;
  rag_used: boolean;
  steps: AgentToolResult[];
  sources: {
    document_id: number;
    filename: string;
    chunk_index: number;
    score: number;
  }[];
};

export async function runAgent(
  token: string,
  body: {
    message: string;
    provider: string;
    model?: string | null;
    use_rag?: boolean;
    max_steps?: number;
  }
): Promise<AgentResponse> {
  return api<AgentResponse>("/api/v1/agent/run", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
}