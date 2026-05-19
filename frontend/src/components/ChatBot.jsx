/**
 * ChatBot — floating AI nutrition assistant connected to /ws/chat.
 *
 * Features:
 *  - Real-time streaming from Gemini 2.0 Flash via WebSocket
 *  - Message history with auto-scroll
 *  - "Snap & Ask" pre-population from MultiFoodDisplay
 *  - Typing indicator while AI is streaming
 */

import React, { useState, useEffect, useRef, useCallback } from "react";

const WS_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/^http/, "ws")
  : `ws://${window.location.host}`;

const COLORS = {
  bg: "rgba(15, 23, 42, 0.97)",
  surface: "rgba(30, 41, 59, 0.9)",
  border: "rgba(99, 102, 241, 0.3)",
  accent: "#6366f1",
  accentLight: "#a5b4fc",
  userBubble: "rgba(99,102,241,0.18)",
  aiBubble: "rgba(30,41,59,0.95)",
  text: "#f1f5f9",
  subtle: "#94a3b8",
};

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        gap: "8px",
        alignItems: "flex-end",
        marginBottom: "12px",
        animation: "fadeIn 0.2s ease",
      }}
    >
      {!isUser && (
        <div
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            background: `linear-gradient(135deg, ${COLORS.accent}, #8b5cf6)`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "13px",
            flexShrink: 0,
          }}
        >
          🥗
        </div>
      )}
      <div
        style={{
          maxWidth: "80%",
          padding: "10px 14px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          background: isUser ? COLORS.userBubble : COLORS.aiBubble,
          border: `1px solid ${isUser ? "rgba(99,102,241,0.4)" : "rgba(255,255,255,0.07)"}`,
          color: COLORS.text,
          fontSize: "0.88rem",
          lineHeight: "1.5",
          whiteSpace: "pre-wrap",
        }}
      >
        {msg.content}
        {msg.streaming && (
          <span
            style={{
              display: "inline-block",
              marginLeft: "4px",
              animation: "blink 1s infinite",
            }}
          >
            ▋
          </span>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div
      style={{
        display: "flex",
        gap: "6px",
        padding: "10px 14px",
        alignItems: "center",
      }}
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: "7px",
            height: "7px",
            borderRadius: "50%",
            background: COLORS.accentLight,
            animation: `bounce 1.2s ease ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

export default function ChatBot({
  token,
  prePopulate = null,
  onClearPrePopulate,
  fullPage = false,
}) {
  const [isOpen, setIsOpen] = useState(fullPage ? true : false);
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "ai",
      content:
        "Hi! I'm NutriSnap AI 🥗 — your personal nutrition coach. Ask me about your meal, macros, or health goals!",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsStatus, setWsStatus] = useState("disconnected"); // disconnected | connecting | connected | error

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const streamingMsgId = useRef(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Pre-populate from "Snap & Ask"
  useEffect(() => {
    if (prePopulate) {
      setInputValue(`Tell me about ${prePopulate} in my meal.`);
      setIsOpen(true);
      onClearPrePopulate?.();
    }
  }, [prePopulate, onClearPrePopulate]);

  // WebSocket connection
  const connect = useCallback(() => {
    if (!token) {
      console.warn("ChatBot: No token available for connection. Retrying in 2s...");
      setWsStatus("disconnected");
      setTimeout(connect, 2000);
      return;
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setWsStatus("connecting");
    const wsUrl = `${WS_BASE}/ws/chat?token=${token}`;
    console.log("ChatBot: Connecting to WebSocket...", wsUrl.split('?')[0]);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("ChatBot: WebSocket connected ✅");
      setWsStatus("connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          { id: Date.now(), role: "ai", content: `⚠ ${data.content}` },
        ]);
        setIsStreaming(false);
        return;
      }

      if (data.type === "reply") {
        if (!data.done) {
          // Streaming chunk — append to current streaming message
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.id === streamingMsgId.current) {
              return [
                ...prev.slice(0, -1),
                { ...last, content: last.content + data.content },
              ];
            }
            // First chunk — create streaming message
            const newId = `stream-${Date.now()}`;
            streamingMsgId.current = newId;
            return [
              ...prev,
              { id: newId, role: "ai", content: data.content, streaming: true },
            ];
          });
        } else {
          // Stream complete — remove streaming indicator
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.id === streamingMsgId.current) {
              return [...prev.slice(0, -1), { ...last, streaming: false }];
            }
            return prev;
          });
          setIsStreaming(false);
        }
      }
    };

    ws.onerror = () => setWsStatus("error");
    ws.onclose = () => setWsStatus("disconnected");
    wsRef.current = ws;
  }, [token]);

  // Connect when opened
  useEffect(() => {
    if (isOpen) connect();
    return () => {
      if (!isOpen && wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isOpen, connect]);

  const sendMessage = useCallback(() => {
    const text = inputValue.trim();
    if (!text || isStreaming) return;
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      connect();
      return;
    }

    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: text },
    ]);
    setInputValue("");
    setIsStreaming(true);
    streamingMsgId.current = null;

    wsRef.current.send(JSON.stringify({ type: "message", content: text }));
  }, [inputValue, isStreaming, connect]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const statusColor = {
    connected: "#22c55e",
    connecting: "#f59e0b",
    error: "#ef4444",
    disconnected: "#64748b",
  };

  return (
    <>
      {/* Floating toggle button — hidden in fullPage mode */}
      {!fullPage && (
        <button
          id="chatbot-toggle"
          onClick={() => setIsOpen((o) => !o)}
        aria-label="Toggle NutriSnap AI Chat"
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          zIndex: 9999,
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          border: "none",
          cursor: "pointer",
          background: `linear-gradient(135deg, ${COLORS.accent}, #8b5cf6)`,
          boxShadow: "0 4px 20px rgba(99,102,241,0.5)",
          fontSize: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "transform 0.2s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.1)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >
          {isOpen ? "✕" : "🥗"}
        </button>
      )}

      {/* Chat panel */}
      {(isOpen || fullPage) && (
        <div
          id="chatbot-panel"
          className={
            fullPage
              ? "h-full flex flex-col bg-zinc-950 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl"
              : "fixed bottom-24 right-6 z-[9998] w-96 h-[520px] flex flex-col bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl animate-in slide-in-from-bottom-5"
          }
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800 bg-black/40">
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{ fontSize: "22px" }}>🥗</div>
              <div>
                <div
                  style={{
                    fontWeight: 700,
                    color: COLORS.text,
                    fontSize: "0.92rem",
                  }}
                >
                  NutriSnap AI
                </div>
                <div
                  style={{ fontSize: "0.72rem", color: statusColor[wsStatus] }}
                >
                  {wsStatus === "connected"
                    ? "● Online"
                    : wsStatus === "connecting"
                      ? "● Connecting..."
                      : "● Offline"}
                </div>
              </div>
            </div>
            <div style={{ fontSize: "0.72rem", color: COLORS.subtle }}>
              Gemma 4 (Local)
            </div>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "14px 12px",
              scrollbarWidth: "thin",
              scrollbarColor: `${COLORS.border} transparent`,
            }}
          >
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {isStreaming && !messages.some((m) => m.streaming) && (
              <TypingIndicator />
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: "12px 14px",
              borderTop: `1px solid ${COLORS.border}`,
              display: "flex",
              gap: "8px",
              alignItems: "flex-end",
            }}
          >
            <textarea
              id="chatbot-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your meal..."
              rows={1}
              style={{
                flex: 1,
                resize: "none",
                border: `1px solid ${COLORS.border}`,
                borderRadius: "12px",
                padding: "9px 12px",
                background: COLORS.surface,
                color: COLORS.text,
                fontSize: "0.87rem",
                outline: "none",
                fontFamily: "inherit",
                lineHeight: "1.4",
                maxHeight: "100px",
                overflowY: "auto",
              }}
            />
            <button
              id="chatbot-send"
              onClick={sendMessage}
              disabled={isStreaming || !inputValue.trim()}
              style={{
                width: "38px",
                height: "38px",
                borderRadius: "50%",
                border: "none",
                background:
                  isStreaming || !inputValue.trim()
                    ? "rgba(99,102,241,0.3)"
                    : `linear-gradient(135deg, ${COLORS.accent}, #8b5cf6)`,
                color: "#fff",
                cursor:
                  isStreaming || !inputValue.trim() ? "not-allowed" : "pointer",
                fontSize: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                transition: "all 0.2s",
              }}
            >
              ➤
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
      `}</style>
    </>
  );
}
