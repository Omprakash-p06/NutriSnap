import { useAuth, XP_THRESHOLDS } from "../../context/AuthContext";
import { Flame, Sun, Moon } from "lucide-react";
import DecryptedText from "../common/DecryptedText";
import ShinyText from "../common/ShinyText";
import { useTheme } from "../../context/ThemeContext";

export default function Navbar() {
  const { currentUser, viewMode, setViewMode, setIsStreakModalOpen } = useAuth();
  const { dark, toggleTheme } = useTheme();
  const isMarketingMode = viewMode === "marketing";

  const getNextThreshold = () => {
    if (!currentUser) return 0;
    const currentLvl = currentUser.level || 1;
    return XP_THRESHOLDS[currentLvl] || "MAX";
  };

  return (
    <nav className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
      <h2
        className="text-2xl font-black uppercase tracking-wider cursor-pointer text-foreground"
        onClick={() => setViewMode("marketing")}
      >
        <DecryptedText text="NutriSnap" />
      </h2>

      <div className="hidden md:flex items-center gap-6">
        {isMarketingMode ? (
          <>
            <button className="text-zinc-400 hover:text-foreground transition">Features</button>
            <button className="text-zinc-400 hover:text-foreground transition">How it Works</button>
            <button
              onClick={() => setViewMode("app")}
              className="text-[#FF6B5A] font-bold tracking-wide"
            >
              Back to Dashboard
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setViewMode("marketing")}
              className="text-zinc-400 hover:text-foreground transition"
            >
              Showcase
            </button>
            <button className="text-foreground font-bold">Dashboard</button>
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-foreground hover:bg-zinc-800 transition-colors"
          aria-label="Toggle Theme"
        >
          {dark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {viewMode === "marketing" && (
          <button
            onClick={() => setViewMode("app")}
            className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-full hover:bg-zinc-800 text-sm font-bold transition text-foreground"
          >
            App Home
          </button>
        )}

        {/* Gamification Badge */}
        <div 
          className="flex items-center gap-3 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-full shadow-lg cursor-pointer hover:bg-zinc-800 transition-colors"
          onClick={() => setIsStreakModalOpen(true)}
        >
          <div className="flex items-center gap-1.5 px-3 py-1 bg-gradient-to-br from-[#FF6B5A] to-amber-500 rounded-full text-white">
            <Flame size={14} />
            <span className="font-black text-xs">
              <ShinyText text={currentUser?.level?.toString() || "1"} baseColor="#fff" speed={4} />
            </span>
          </div>

          <div className="flex flex-col min-w-[60px]">
            <span className="text-xs font-bold text-zinc-300">
              {currentUser?.xp || 0} <span className="text-zinc-600">/ {getNextThreshold()}</span>
            </span>
            {/* Discreet progress bar */}
            <div className="w-full h-1 bg-zinc-800 rounded-full mt-1 overflow-hidden">
              <div
                className="h-full bg-[#FF6B5A]"
                style={{
                  width: `${Math.min(100, Math.max(0, (((currentUser?.xp || 0) - (XP_THRESHOLDS[(currentUser?.level || 1) - 1] || 0)) / ((XP_THRESHOLDS[currentUser?.level || 1] || (currentUser?.xp || 0) + 100) - (XP_THRESHOLDS[(currentUser?.level || 1) - 1] || 0))) * 100))}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
