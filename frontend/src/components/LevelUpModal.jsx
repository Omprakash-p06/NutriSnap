import { useAuth } from "../context/AuthContext";

export default function LevelUpModal() {
  const { justLeveledUp, clearLevelUp, currentUser } = useAuth();

  if (!justLeveledUp || !currentUser) return null;

  return (
    <div style={styles.overlay}>
      <div className="glass-card" style={styles.card}>
        <div style={styles.starburst}>⭐️</div>

        <h1
          style={{ fontSize: "3rem", margin: "10px 0 0 0" }}
          className="text-gradient"
        >
          LEVEL UP!
        </h1>

        <p style={{ fontSize: "1.2rem", margin: "10px 0 30px" }}>
          Amazing job logging your meals! You are now{" "}
          <strong style={{ color: "var(--primary-coral)" }}>
            Level {currentUser.level}
          </strong>
          !
        </p>

        <button
          className="clay-btn"
          onClick={clearLevelUp}
          style={{ padding: "15px 40px", fontSize: "1.2rem" }}
        >
          Awesome!
        </button>
      </div>
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
    backgroundColor: "rgba(0,0,0,0.7)",
    backdropFilter: "blur(10px)",
    zIndex: 9999,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    animation: "fadeIn 0.3s ease-out",
  },
  card: {
    maxWidth: "450px",
    textAlign: "center",
    padding: "50px 30px",
    animation: "popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
  },
  starburst: {
    fontSize: "6rem",
    margin: 0,
    lineHeight: 1,
    animation: "spinPulse 3s infinite linear",
  },
};
