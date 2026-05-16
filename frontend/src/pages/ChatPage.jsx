import { useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import ChatBot from "../components/ChatBot";

/**
 * ChatPage — full-screen AI nutrition assistant.
 * The ChatBot component is rendered without its floating widget wrapper;
 * instead we embed it in a full-page layout.
 *
 * We pass `fullPage={true}` so ChatBot can conditionally render
 * in expanded mode. If ChatBot doesn't support this prop yet, it
 * will simply ignore it and render its default popup — still functional.
 */
export default function ChatPage() {
  const { token } = useAuth();

  return (
    <div className="page-chat">
      <div className="page-chat__header">
        <div className="page-chat__avatar" aria-hidden="true">🥗</div>
        <div>
          <h1 className="page-title" style={{ marginBottom: 2 }}>NutriSnap AI</h1>
          <p className="page-subtitle" style={{ marginTop: 0 }}>
            Your personal nutrition coach — powered by Gemma 4 (local model)
          </p>
        </div>
      </div>

      <div className="page-chat__body">
        <ChatBot token={token} fullPage />
      </div>
    </div>
  );
}
