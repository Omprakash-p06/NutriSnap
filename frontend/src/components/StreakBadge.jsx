import React from "react";
import { Flame } from "lucide-react";
import ShinyText from "./common/ShinyText";

export default function StreakBadge({ streak = 0 }) {
  if (streak === 0) return null;

  return (
    <div style={styles.badge}>
      <Flame size={18} color="#FF6B5A" />
      <span style={styles.count}>
        <ShinyText
          text={streak.toString()}
          baseColor="var(--primary-coral)"
          speed={3.5}
        />
      </span>
      <span style={styles.label}>day streak</span>
    </div>
  );
}

const styles = {
  badge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    background:
      "linear-gradient(135deg, rgba(255,107,90,0.12), rgba(255,179,71,0.12))",
    border: "1.5px solid var(--primary-coral)",
    borderRadius: "20px",
    padding: "6px 14px",
    cursor: "default",
  },
  count: {
    fontSize: "1.1rem",
    fontWeight: "800",
    color: "var(--primary-coral)",
    fontFamily: "var(--font-heading)",
    lineHeight: 1,
  },
  label: {
    fontSize: "0.8rem",
    fontWeight: "600",
    color: "var(--text-muted)",
  },
};
