import React, { useState } from "react";
import "./App.css";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./context/AuthContext";
import Dock from "./components/Dock";
import StreakModal from "./components/StreakModal";
import LandingPage from "./components/layout/LandingPage";
import SettingsModal from "./components/SettingsModal.jsx";

// Pages
import Home from "./pages/Home";
import ScanPage from "./pages/ScanPage";
import MealsPage from "./pages/MealsPage";
import PlannerPage from "./pages/PlannerPage";
import ChatPage from "./pages/ChatPage";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-screen" style={{ padding: "40px", textAlign: "center" }}>
          <h2>Something went wrong.</h2>
          <button onClick={() => window.location.reload()} className="clay-btn">
            Reload App
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

/**
 * Inner shell — needs auth context so it can read isAuthenticated + viewMode.
 */
function AppShell() {
  const [activeTab, setActiveTab] = useState("home");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { isAuthenticated, viewMode, setViewMode } = useAuth();

  // Not in app mode → landing page
  if (viewMode !== "app") {
    return (
      <div id="app-container">
        <LandingPage
          onGetStarted={() => setViewMode("app")}
        />
        <StreakModal />
      </div>
    );
  }

  return (
    <div id="app-container">
      <main className="page-content">
        {activeTab === "home" && (
          <Home
            isSettingsOpenExternal={isSettingsOpen}
            setIsSettingsOpenExternal={setIsSettingsOpen}
          />
        )}
        {activeTab === "scan"    && <ScanPage />}
        {activeTab === "meals"   && <MealsPage />}
        {activeTab === "planner" && <PlannerPage />}
        {activeTab === "chat"    && <ChatPage />}
      </main>

      <Dock activeTab={activeTab} onTabChange={setActiveTab} />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
      <StreakModal />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ErrorBoundary>
          <AppShell />
        </ErrorBoundary>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
