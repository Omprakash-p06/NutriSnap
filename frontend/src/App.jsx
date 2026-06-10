import { useState } from "react";
import Navbar from "./components/layout/Navbar";
import { useAuth, AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import LandingPage from "./components/layout/LandingPage";
import { DashboardPage } from "./pages/DashboardPage";
import ScanPage from "./pages/ScanPage";
import MealsPage from "./pages/MealsPage";
import PlannerPage from "./pages/PlannerPage";
import ChatPage from "./pages/ChatPage";
import Dock from "./components/Dock";
import GlassSurface from "./components/GlassSurface";
import { VscHome, VscDeviceCamera, VscChecklist, VscCalendar, VscComment, VscSettings } from "react-icons/vsc";
import SettingsModal from "./components/SettingsModal";
import StreakModal from "./components/StreakModal";
import OnboardingModal from "./components/OnboardingModal";
import ChatBot from "./components/ChatBot";

function AppShell() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { viewMode, setViewMode, token } = useAuth();
  const [activeTab, setActiveTab] = useState("dashboard");

  // Not in app mode → landing page
  if (viewMode !== "app") {
    return (
      <div id="app-container" className="bg-background text-foreground min-h-screen">
        <LandingPage onGetStarted={() => setViewMode("app")} />
      </div>
    );
  }

  // Define tab navigation
  const tabs = [
    { id: "dashboard", icon: <VscHome size={22} />, label: "Dashboard" },
    { id: "scan", icon: <VscDeviceCamera size={22} />, label: "Scan Meal" },
    { id: "meals", icon: <VscChecklist size={22} />, label: "My Meals" },
    { id: "planner", icon: <VscCalendar size={22} />, label: "Planner" },
    { id: "chat", icon: <VscComment size={22} />, label: "AI Chat" },
  ];

  const dockItems = [
    ...tabs.map((tab) => ({
      icon: tab.icon,
      label: tab.label,
      onClick: () => setActiveTab(tab.id),
      className: activeTab === tab.id ? "!border-accent !text-accent" : "",
    })),
    {
      icon: <VscSettings size={22} />,
      label: "Settings",
      onClick: () => setIsSettingsOpen(true),
      className: "",
    }
  ];

  return (
    <div className="bg-background text-foreground min-h-screen pb-28 relative">
      <Navbar setIsSettingsOpen={setIsSettingsOpen} />

      {/* Main Content Area */}
      <main className="w-full h-full relative z-10">
        {activeTab === "dashboard" && <DashboardPage />}
        {activeTab === "scan" && <ScanPage />}
        {activeTab === "meals" && <MealsPage />}
        {activeTab === "planner" && <PlannerPage />}
        {activeTab === "chat" && <ChatPage />}
      </main>

      {/* Dock Navigation wrapped in GlassSurface */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999] h-[110px] flex items-center">
        <GlassSurface
          width="auto"
          height={80}
          borderRadius={32}
          opacity={0.8}
          brightness={60}
          className="p-1 px-2 !bg-zinc-950/80 border border-zinc-800 shadow-2xl"
        >
          <Dock
            items={dockItems}
            panelHeight={64}
            baseItemSize={48}
            magnification={50}
          />
        </GlassSurface>
      </div>

      {/* ChatBot Floating Component — hidden when Chat tab is active (fullPage ChatBot handles it) */}
      {activeTab !== "chat" && <ChatBot token={token} />}

      {/* Modals */}
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <StreakModal />
      <OnboardingModal />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </ThemeProvider>
  );
}
