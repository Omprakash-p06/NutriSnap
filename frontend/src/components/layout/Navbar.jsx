import { useTheme } from "../../context/ThemeContext";
import { useAuth, XP_THRESHOLDS } from "../../context/AuthContext";
import { Flame, Sun, Moon } from "lucide-react";
import DecryptedText from "../common/DecryptedText";
import ShinyText from "../common/ShinyText";
import Magnet from "../common/Magnet";

export default function Navbar() {
  const { dark, toggleTheme } = useTheme();
  const { isAuthenticated, currentUser, loginAsGuest, viewMode, setViewMode } =
    useAuth();
  const isMarketingMode = viewMode === "marketing" || !isAuthenticated;

  const getNextThreshold = () => {
    if (!currentUser) return 0;
    const currentLvl = currentUser.level || 1;
    return XP_THRESHOLDS[currentLvl] || "MAX";
  };

  return (
    <nav
      className="navbar"
      style={
        isMarketingMode
          ? {
              background: "var(--glass-bg)",
              borderBottom: "1px solid var(--border)",
              backdropFilter: "blur(16px)",
            }
          : {}
      }
    >
      <h2
        className="logo"
        onClick={() => setViewMode("marketing")}
        style={{
          cursor: "pointer",
          fontFamily: "'Barlow Condensed', sans-serif",
          fontWeight: 900,
          fontSize: "1.7rem",
          letterSpacing: "0.02em",
          textTransform: "uppercase",
        }}
      >
        <DecryptedText text="NutriSnap" className="text-gradient" />
      </h2>

      <div className="nav-links">
        {isMarketingMode ? (
          <>
            <a className="nav-link" style={{ color: "var(--text-muted)" }}>
              Features
            </a>
            <a className="nav-link" style={{ color: "var(--text-muted)" }}>
              How it Works
            </a>
            {isAuthenticated && (
              <a
                className="nav-link active"
                onClick={() => setViewMode("app")}
                style={{ color: "#FF6B5A", fontWeight: 800, cursor: "pointer" }}
              >
                Back to Dashboard
              </a>
            )}
          </>
        ) : (
          <>
            <a
              className="nav-link"
              onClick={() => setViewMode("marketing")}
              style={{ cursor: "pointer" }}
            >
              Showcase
            </a>
            <a className="nav-link active">Dashboard</a>
            <a className="nav-link">Community</a>
          </>
        )}
      </div>

      <div className="nav-actions">
        <button
          onClick={toggleTheme}
          className="theme-toggle"
          title="Toggle Dark Mode"
          style={isMarketingMode ? { color: "var(--text)" } : {}}
        >
          {dark ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        {isAuthenticated ? (
          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            {viewMode === "marketing" && (
              <button
                className="clay-btn"
                onClick={() => setViewMode("app")}
                style={{
                  fontFamily: "'Barlow Condensed', sans-serif",
                  padding: "8px 20px",
                  fontSize: "0.9rem",
                }}
              >
                App Home
              </button>
            )}
            {/* Gamification Badge Chip */}
            <div
              className="clay-chip"
              style={{ minWidth: "160px", paddingRight: "12px" }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 10px",
                  background:
                    "linear-gradient(135deg, var(--primary-coral), var(--primary-amber))",
                  borderRadius: "16px",
                  color: "#fff",
                  boxShadow: "0 2px 8px rgba(255, 107, 90, 0.2)",
                }}
              >
                <Flame size={16} fill="#fff" />
                <span style={{ fontWeight: 800, fontSize: "0.85rem" }}>
                  <ShinyText
                    text={currentUser?.level?.toString()}
                    baseColor="#fff"
                    speed={4}
                  />
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  flex: 1,
                  marginLeft: "2px",
                }}
              >
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    opacity: 0.85,
                  }}
                >
                  {currentUser?.xp}{" "}
                  <span style={{ opacity: 0.5, fontWeight: 500 }}>
                    / {getNextThreshold()}
                  </span>
                </span>
              </div>

              {/* Discreet progress bar */}
              <div className="xp-bar-container">
                <div
                  className="xp-bar-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, ((currentUser?.xp - (XP_THRESHOLDS[currentUser?.level - 1] || 0)) / ((XP_THRESHOLDS[currentUser?.level] || currentUser?.xp + 100) - (XP_THRESHOLDS[currentUser?.level - 1] || 0))) * 100))}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        ) : (
          <Magnet padding={80} magnetStrength={0.2}>
            <button
              className="clay-btn"
              onClick={loginAsGuest}
              style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 900,
                fontSize: "1.1rem",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              Get Started
            </button>
          </Magnet>
        )}
      </div>
    </nav>
  );
}
