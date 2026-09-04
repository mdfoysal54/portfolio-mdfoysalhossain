"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import {
  api,
  deleteDocument,
  getDocuments,
  login,
  register,
  uploadDocument,
  createConversation,
  getConversation,
  getConversations,
  getMe,
  getProviders,
  ProviderInfo,
  streamChat,
  EVUDocument,
  runAgent,
  AgentToolResult,
} from "../lib/api";

type Conversation = {
  id: number;
  title: string;
  created_at: string;
};

type Message = {
  id: number;
  role: string;
  content: string;
  created_at: string;
};

type AuthResponse = {
  access_token?: string;
  token?: string;
  detail?: string;
};

export default function ChatPage() {
  const [token, setToken] = useState<string | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [provider, setProvider] = useState<string>("openai");
  const [model, setModel] = useState("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentMode, setAgentMode] = useState(false);
  const [agentSteps, setAgentSteps] = useState<AgentToolResult[]>([]);
  const [error, setError] = useState("");
  const [loadingPage, setLoadingPage] = useState(true);

  // Auth form states
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState("");

  // Step 6: uploaded documents become RAG knowledge for the signed-in user.
  const [documents, setDocuments] = useState<EVUDocument[]>([]);
  const [uploading, setUploading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadData(authToken: string) {
    try {
      setLoadingPage(true);
      await getMe(authToken);

      const [providerList, conversationList, documentList] = await Promise.all([
        getProviders().catch(() => []),
        getConversations(authToken).catch(() => []),
        getDocuments(authToken).catch(() => []),
      ]);

      setProviders(providerList || []);
      setConversations(conversationList || []);
      setDocuments(documentList || []);

      const firstAvailable =
        providerList?.find((item) => item.available) || providerList?.[0];

      if (firstAvailable) {
        setProvider(firstAvailable.id);
        setModel(firstAvailable.default_model);
      }

      if (conversationList && conversationList.length > 0) {
        const latest = conversationList[0];
        const detail = await getConversation(authToken, latest.id);
        setConversation(latest);
        setMessages(detail.messages || []);
      }
    } catch (err) {
      console.error("Initialization error:", err);
      localStorage.removeItem("evu_token");
      setToken(null);
    } finally {
      setLoadingPage(false);
    }
  }

  useEffect(() => {
    const stored =
      typeof window !== "undefined" ? localStorage.getItem("evu_token") : null;
    if (stored) {
      setToken(stored);
      loadData(stored);
    } else {
      setLoadingPage(false);
    }
  }, []);

  async function handleAuth(e: FormEvent) {
    e.preventDefault();
    setAuthError("");
    try {
      if (authMode === "register") {
        await register(authEmail, authPassword);
      }
      const session = await login(authEmail, authPassword);
      localStorage.setItem("evu_token", session.access_token);
      setToken(session.access_token);
      await loadData(session.access_token);
    } catch (err: unknown) {
      setAuthError(err instanceof Error ? err.message : "Authentication failed.");
    }
  }

  async function handleFileUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !token) return;
    setUploading(true);
    setError("");
    try {
      const uploaded = await uploadDocument(token, file);
      setDocuments((prev) => [uploaded, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function removeDocument(documentId: number) {
    if (!token) return;
    try {
      await deleteDocument(token, documentId);
      setDocuments((prev) => prev.filter((item) => item.id !== documentId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  }

  function selectProvider(id: string) {
    setProvider(id);
    const selected = providers.find((item) => item.id === id);
    if (selected) {
      setModel(selected.default_model);
    }
  }

  async function newChat() {
    if (!token) return;
    try {
      const created = await createConversation(token, "New conversation");
      setConversation(created);
      setMessages([]);
      setConversations((prev) => [created, ...prev]);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Could not create conversation."
      );
    }
  }

  async function selectConversation(selected: Conversation) {
    if (!token) return;
    setError("");
    try {
      const detail = await getConversation(token, selected.id);
      setConversation(selected);
      setMessages(detail.messages || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Could not load conversation."
      );
    }
  }

  async function send(event?: FormEvent, customText?: string) {
    if (event) event.preventDefault();
    const query = (customText ?? input).trim();

    if (!query || loading || !token) return;

    const selected = providers.find((item) => item.id === provider);
    if (selected && !selected.available) {
      setError(
        `${selected.name || provider} is not configured. Add API key in backend/.env.`
      );
      return;
    }

    setInput("");
    setError("");
    setLoading(true);
    setAgentSteps([]);

    const now = new Date().toISOString();
    const tempUserId = Date.now();
    const tempAssistantId = tempUserId + 1;

    try {
      let activeConversation = conversation;
      if (!activeConversation) {
        activeConversation = await createConversation(
          token,
          query.slice(0, 30) || "New conversation"
        );
        setConversation(activeConversation);
        setConversations((prev) => [activeConversation!, ...prev]);
      }

      setMessages((prev) => [
        ...prev,
        { id: tempUserId, role: "user", content: query, created_at: now },
        { id: tempAssistantId, role: "assistant", content: "", created_at: now },
      ]);

      if (agentMode) {
        const result = await runAgent(token, {
          message: query,
          provider,
          model: model || null,
          use_rag: true,
          max_steps: 4,
        });

        setAgentSteps(result.steps);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === tempAssistantId
              ? { ...msg, content: result.response }
              : msg
          )
        );
      } else {
        await streamChat(
          `/api/v1/conversations/${activeConversation.id}/stream`,
          token,
          {
            message: query,
            provider,
            model: model || null,
            use_rag: true,
          },
          (delta) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantId
                  ? { ...msg, content: msg.content + delta }
                  : msg
              )
            );
          }
        );
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Chat failed.");
      setMessages((prev) =>
        prev.filter((msg) => msg.id !== tempAssistantId)
      );
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("evu_token");
    setToken(null);
    setConversation(null);
    setConversations([]);
    setMessages([]);
  }

  if (loadingPage) {
    return (
      <div className="page">
        <div className="muted">Loading EVU...</div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="page">
        <div className="card">
          <div className="logo">✦ EVU</div>
          <div className="muted">Unified AI Workspace</div>

          <div className="tabs">
            <button
              type="button"
              className={authMode === "login" ? "active" : ""}
              onClick={() => {
                setAuthMode("login");
                setAuthError("");
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={authMode === "register" ? "active" : ""}
              onClick={() => {
                setAuthMode("register");
                setAuthError("");
              }}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleAuth}>
            <label htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              type="email"
              required
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
              placeholder="user@example.com"
            />

            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              required
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              placeholder="••••••••"
            />

            {authError && <div className="error">{authError}</div>}

            <button className="primary" type="submit">
              {authMode === "login" ? "Sign In" : "Create Account"}
            </button>

            <div className="auth-switch">
              {authMode === "login"
                ? "Don't have an account? "
                : "Already registered? "}
              <span
                className="link-btn"
                onClick={() => {
                  setAuthMode(authMode === "login" ? "register" : "login");
                  setAuthError("");
                }}
              >
                {authMode === "login" ? "Register" : "Sign In"}
              </span>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-layout">
      {/* Left Sidebar */}
      <aside className="sidebar">
        <div>
          <div className="sidebar-header">
            <span className="logo">EVU</span>
          </div>

          <button type="button" className="sidebar-btn" onClick={newChat}>
            + New Chat
          </button>

          <div className="sidebar-section-title">Recent Chats</div>
          <div className="conversation-list">
            {conversations.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`conversation-item ${
                  conversation?.id === item.id ? "active" : ""
                }`}
                onClick={() => selectConversation(item)}
              >
                {item.title || "Untitled Chat"}
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="user-badge">
            <div className="user-avatar">E</div>
            <span>User</span>
          </div>
          <button
            type="button"
            className="logout-icon-btn"
            onClick={logout}
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <main className="main-content">
        <header className="topbar">
          <div className="provider-controls">
            <select
              value={provider}
              onChange={(e) => selectProvider(e.target.value)}
              disabled={loading}
            >
              {providers.map((item) => (
                <option key={item.id} value={item.id} disabled={!item.available}>
                  {item.name} {!item.available ? " (No key)" : ""}
                </option>
              ))}
            </select>

            <input
              className="model-input"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="Model ID"
              disabled={loading}
            />
          </div>
          <div className="rag-controls">
            <label className="upload-label">
              {uploading ? "Indexing..." : "+ Add document"}
              <input
                type="file"
                accept=".txt,.md,.pdf,.docx,.csv,.json"
                onChange={handleFileUpload}
                disabled={uploading || loading}
              />
            </label>
            {documents.length > 0 && (
              <details className="document-menu">
                <summary>{documents.length} document{documents.length === 1 ? "" : "s"}</summary>
                <div className="document-list">
                  {documents.map((item) => (
                    <div key={item.id} className="document-item">
                      <span title={item.filename}>{item.filename}</span>
                      <button type="button" onClick={() => removeDocument(item.id)}>×</button>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        </header>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h1 className="empty-title">
                <span className="asterisk">✦</span> What would you like to explore?
              </h1>

              {/* Main Centered Claude-style Prompt Card */}
              <div className="center-box">
                <form
                  className="composer-card"
                  onSubmit={(e) => send(e)}
                >
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        send();
                      }
                    }}
                    placeholder="Type / for skills or start asking..."
                    disabled={loading}
                    rows={3}
                  />

                  <div className="composer-toolbar">
                    <div className="tool-pills">
                      <span className="tool-pill">+ Add</span>
                      <span className="tool-pill">Chat</span>
                    </div>

                    <div className="send-action">
                      <button
                        type="submit"
                        className="send-btn"
                        disabled={loading || !input.trim()}
                      >
                        ↑
                      </button>
                    </div>
                  </div>
                </form>
              </div>

              {/* Suggested quick chips */}
              <div className="suggestions-grid">
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => send(undefined, "Help me write clean Python code")}
                >
                  &lt;/&gt; Code
                </button>
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => send(undefined, "Explain a complex concept simply")}
                >
                  🎓 Learn
                </button>
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => send(undefined, "Brainstorm project architecture ideas")}
                >
                  📈 Strategize
                </button>
                <button
                  type="button"
                  className="suggestion-chip"
                  onClick={() => send(undefined, "Draft a professional technical summary")}
                >
                  ✍️ Write
                </button>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`msg-row ${
                    message.role === "user" ? "user-row" : "assistant-row"
                  }`}
                >
                  <div
                    className={`msg ${
                      message.role === "user" ? "user" : "assistant"
                    }`}
                  >
                    {message.content ||
                      (loading && message.role === "assistant"
                        ? "EVU is thinking…"
                        : "")}
                  </div>
                </div>
              ))}

              {error && <div className="error">{error}</div>}

              {agentSteps.length > 0 && (
                <details className="agent-trace">
                  <summary>EVU Agent steps ({agentSteps.length})</summary>
                  {agentSteps.map((step) => (
                    <div className="agent-step" key={`${step.step}-${step.tool}`}>
                      <strong>{step.step}. {step.tool}</strong>
                      <div>{step.success ? "Success" : "Failed"}</div>
                      <pre>{step.output}</pre>
                    </div>
                  ))}
                </details>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Bottom Pinned Input Bar (when conversation has messages) */}
        {messages.length > 0 && (
          <div className="bottom-dock">
            <form
              className="composer-card"
              onSubmit={(e) => send(e)}
            >
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="Reply to EVU..."
                disabled={loading}
                rows={2}
              />

              <div className="composer-toolbar">
                <div className="tool-pills">
                  <label className={`tool-pill agent-toggle ${agentMode ? "active" : ""}`}>
                    <input
                      type="checkbox"
                      checked={agentMode}
                      onChange={(e) => setAgentMode(e.target.checked)}
                      disabled={loading}
                    />
                    Agent mode
                  </label>
                  <span className="tool-pill">+ Add</span>
                </div>

                <div className="send-action">
                  <button
                    type="submit"
                    className="send-btn"
                    disabled={loading || !input.trim()}
                  >
                    ↑
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}