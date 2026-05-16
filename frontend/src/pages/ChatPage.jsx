import { useAuth } from "../context/AuthContext";
import ChatBot from "../components/ChatBot";

export default function ChatPage() {
  const { token } = useAuth();

  return (
    <div className="page-container page-chat max-w-4xl mx-auto pt-4 px-4 flex flex-col" style={{ height: "calc(100vh - 140px)" }}>
      <div className="text-center mb-4 mt-2">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zinc-900 border border-zinc-800 shadow-xl mb-3 text-3xl">
          🥗
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight mb-1">NutriSnap AI</h1>
        <p className="text-gray-500 text-sm">
          Your personal nutrition coach — powered by Gemma 4
        </p>
      </div>

      <div className="flex-1 w-full relative" style={{ minHeight: 0 }}>
        <ChatBot token={token} fullPage={true} />
      </div>
    </div>
  );
}
