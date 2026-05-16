import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Flame, X, Trophy, Star, Target, Calendar } from "lucide-react";
import { useAuth, XP_THRESHOLDS } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import ShinyText from "./common/ShinyText";

export default function StreakModal() {
  const { isStreakModalOpen, setIsStreakModalOpen, currentUser } = useAuth();
  const { calculateStreak } = useMealHistory();
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    if (isStreakModalOpen) {
      calculateStreak().then(setStreak);
    }
  }, [isStreakModalOpen]);

  if (!isStreakModalOpen || !currentUser) return null;

  const currentLevel = currentUser.level || 1;
  const nextXp = XP_THRESHOLDS[currentLevel] || currentUser.xp + 100;
  const prevXp = XP_THRESHOLDS[currentLevel - 1] || 0;
  const progress = Math.min(100, Math.max(0, ((currentUser.xp - prevXp) / (nextXp - prevXp)) * 100));

  return (
    <div style={styles.overlay} onClick={() => setIsStreakModalOpen(false)}>
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className="glass-card"
        style={styles.modal}
        onClick={(e) => e.stopPropagation()}
      >
        <button style={styles.closeBtn} onClick={() => setIsStreakModalOpen(false)}>
          <X size={24} />
        </button>

        <div style={styles.header}>
          <div style={styles.streakCircle}>
            <Flame size={48} color="#FF6B5A" fill="#FF6B5A" />
            <div style={styles.streakNum}>{streak}</div>
          </div>
          <h2 style={styles.title}>Day Streak!</h2>
          <p style={styles.subtitle}>You're on fire! Keep logging to grow your streak.</p>
        </div>

        <div style={styles.statsGrid}>
          <div style={styles.statItem}>
            <Trophy size={20} color="#FFB347" />
            <div style={styles.statLabel}>Level</div>
            <div style={styles.statValue}>{currentLevel}</div>
          </div>
          <div style={styles.statItem}>
            <Star size={20} color="#3ECFA0" />
            <div style={styles.statLabel}>Total XP</div>
            <div style={styles.statValue}>{currentUser.xp}</div>
          </div>
          <div style={styles.statItem}>
            <Target size={20} color="#6B3FA0" />
            <div style={styles.statLabel}>Next Level</div>
            <div style={styles.statValue}>{nextXp - currentUser.xp} XP</div>
          </div>
        </div>

        <div style={styles.xpSection}>
          <div style={styles.xpHeader}>
            <span style={styles.xpLabel}>Level Progress</span>
            <span style={styles.xpValue}>{progress.toFixed(0)}%</span>
          </div>
          <div style={styles.xpBarContainer}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              style={styles.xpBarFill}
            />
          </div>
        </div>

        <div style={styles.badgesSection}>
          <h3 style={styles.sectionTitle}>Recent Badges</h3>
          <div style={styles.badgesRow}>
            <div style={styles.badgeIcon} title="Early Bird">🌅</div>
            <div style={styles.badgeIcon} title="Macro Master">📊</div>
            <div style={styles.badgeIcon} title="Hydration Hero">💧</div>
            <div style={styles.badgeIcon} title="Consistency King" style={{ opacity: 0.3 }}>👑</div>
          </div>
        </div>

        <button
          className="clay-btn"
          style={styles.actionBtn}
          onClick={() => setIsStreakModalOpen(false)}
        >
          Keep it Up!
        </button>
      </motion.div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: "rgba(0,0,0,0.7)",
    backdropFilter: "blur(8px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 2000,
  },
  modal: {
    width: "90%",
    maxWidth: "400px",
    padding: "32px",
    textAlign: "center",
    position: "relative",
    background: "var(--glass-bg)",
    border: "1px solid var(--glass-border)",
  },
  closeBtn: {
    position: "absolute",
    top: "16px",
    right: "16px",
    background: "none",
    border: "none",
    color: "var(--text-muted)",
    cursor: "pointer",
  },
  header: {
    marginBottom: "24px",
  },
  streakCircle: {
    width: "100px",
    height: "100px",
    borderRadius: "50%",
    background: "rgba(255,107,90,0.1)",
    margin: "0 auto 16px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    border: "2px solid rgba(255,107,90,0.2)",
  },
  streakNum: {
    fontSize: "1.5rem",
    fontWeight: "900",
    color: "var(--primary-coral)",
    marginTop: "-4px",
  },
  title: {
    fontSize: "1.75rem",
    margin: "0 0 8px",
    color: "var(--text)",
  },
  subtitle: {
    fontSize: "0.9rem",
    color: "var(--text-muted)",
    margin: 0,
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "12px",
    marginBottom: "24px",
  },
  statItem: {
    background: "rgba(255,255,255,0.05)",
    padding: "12px",
    borderRadius: "16px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "4px",
  },
  statLabel: {
    fontSize: "0.7rem",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  statValue: {
    fontSize: "1.1rem",
    fontWeight: "800",
    color: "var(--text)",
  },
  xpSection: {
    marginBottom: "24px",
    textAlign: "left",
  },
  xpHeader: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: "8px",
    fontSize: "0.85rem",
    fontWeight: "700",
  },
  xpLabel: {
    color: "var(--text-muted)",
  },
  xpValue: {
    color: "var(--primary-mint)",
  },
  xpBarContainer: {
    height: "8px",
    background: "rgba(255,255,255,0.1)",
    borderRadius: "4px",
    overflow: "hidden",
  },
  xpBarFill: {
    height: "100%",
    background: "linear-gradient(90deg, var(--accent-mint), var(--primary-amber))",
  },
  badgesSection: {
    marginBottom: "24px",
  },
  sectionTitle: {
    fontSize: "0.9rem",
    textAlign: "left",
    marginBottom: "12px",
    color: "var(--text-muted)",
  },
  badgesRow: {
    display: "flex",
    gap: "12px",
    justifyContent: "flex-start",
  },
  badgeIcon: {
    width: "48px",
    height: "48px",
    background: "rgba(255,255,255,0.05)",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "1.5rem",
    cursor: "help",
  },
  actionBtn: {
    width: "100%",
    padding: "16px",
    fontSize: "1.1rem",
  },
};
