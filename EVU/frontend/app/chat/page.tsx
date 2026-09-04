"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getProviders, ProviderInfo, streamChat } from "../../lib/api";

type Conversation = { id: number; title: string; created_at: string };
type Message = { id: number; role: string; content: string; created_at: string };

export default function ChatPage() {
  const router = useRouter();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [provider, setProvider] = useState<ProviderInfo["id"]>("openai");
  const [model, setModel] = useState("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("evu_token");
    if (!token) router.replace("/");
    getProviders()
      .then((items) => {
        setProviders(items);
        const first = items.find((item) => item.available) || items[0];
        if (first) {
          setProvider(first.id);
          setModel(first.default_model);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load AI providers"));
  }, [router]);

  function selectProvider(id: ProviderInfo["id"]) {
    setProvider(id);
    const selected = providers.find((item) => item.id === id);
    if (selected) setModel(selected.default_model);
  }

  async function ensureConversation() {
    if (conversation) return conversation;
    const token = localStorage.getItem("evu_token");
    if (!token) throw new Error("Please log in again.");
    const created = await api<Conversation>("/api/v1/conversations", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ title: "EVU Chat" }),
    });
    setConversation(created);
    return created;
  }

  async function send(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const selected = providers.find((item) => item.id === provider);
    if (!selected?.available) {
      setError(`${selected?.name || provider} is not configured. Add its API key to backend/.env first.`);
      return;
    }

    const text = input.trim();
    setInput("");
    setError("");
    setLoading(true);
    const now = new Date().toISOString();
    const tempUserId = Date.now();
    const tempAssistantId = tempUserId + 1;

    try {
      const conv = await ensureConversation();
      const token = localStorage.getItem("evu_token");
      if (!token) throw new Error("Please log in again.");

      setMessages((prev) => [
        ...prev,
        { id: tempUserId, role: "user", content: text, created_at: now },
        { id: tempAssistantId, role: "assistant", content: "", created_at: now },
      ]);

      await streamChat(
        `/api/v1/conversations/${conv.id}/stream`,
        token,
        { message: text, provider, model: model || null },
        (delta) => {
          setMessages((prev) => prev.map((message) =>
            message.id === tempAssistantId
              ? { ...message, content: message.content + delta }
              : message,
          ));
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
      setMessages((prev) => prev.filter((message) => message.id !== tempAssistantId));
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("evu_token");
    router.replace("/");
  }

  return (
    <main className="chat">
      <header className="topbar">
        <strong>✦ EVU</strong>
        <div className="provider-controls">
          <select value={provider} onChange={(e) => selectProvider(e.target.value as ProviderInfo["id"])} disabled={loading}>
            {providers.map((item) => (
              <option key={item.id} value={item.id} disabled={!item.available}>
                {item.name}{item.available ? "" : " (API key needed)"}
              </option>
            ))}
          </select>
          <input className="model-input" value={model} onChange={(e) => setModel(e.target.value)} placeholder="Model" disabled={loading} />
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      <section className="messages">
        {messages.length === 0 && <div className="muted">Choose an AI provider and start a conversation with EVU.</div>}
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.role === "user" ? "user" : "assistant"}`}>
            {m.content || (loading && m.role === "assistant" ? "EVU is typing…" : "")}
          </div>
        ))}
        {error && <div className="error">{error}</div>}
      </section>

      <form className="composer" onSubmit={send}>
        <div className="composer-inner">
          <textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder="Message EVU…" disabled={loading} />
          <button className="send" type="submit" disabled={loading}>Send</button>
        </div>
      </form>
    </main>
  );
}
