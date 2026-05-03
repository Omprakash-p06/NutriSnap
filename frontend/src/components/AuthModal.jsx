import { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../context/AuthContext";
import { authAPI } from "../services/api";

export default function AuthModal() {
  const { isAuthModalOpen, toggleAuthModal, loginSession } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        await loginSession(email, password);
      } else {
        await authAPI.register(name, email, password);
        // After successful signup, log them in
        await loginSession(email, password);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const res = await authAPI.googleAuth(credentialResponse.credential);
      loginSession(res.token, res.user);
    } catch (err) {
      setError("Google Login Failed");
    }
  };

  return (
    <div style={styles.overlay}>
      <div className="glass-card" style={styles.modal}>
        <button style={styles.closeBtn} onClick={() => toggleAuthModal(false)}>
          ✕
        </button>

        <h2
          style={{ textAlign: "center", marginBottom: "20px" }}
          className="text-gradient"
        >
          {isLogin ? "Welcome Back" : "Create Account"}
        </h2>

        <div style={styles.tabs}>
          <button
            style={{ ...styles.tab, opacity: isLogin ? 1 : 0.5 }}
            onClick={() => setIsLogin(true)}
          >
            Log In
          </button>
          <button
            style={{ ...styles.tab, opacity: !isLogin ? 1 : 0.5 }}
            onClick={() => setIsLogin(false)}
          >
            Sign Up
          </button>
        </div>

        {error && <p style={styles.error}>{error}</p>}

        <form onSubmit={handleSubmit} style={styles.form}>
          {!isLogin && (
            <input
              style={styles.input}
              type="text"
              placeholder="Your Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          )}
          <input
            style={styles.input}
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button
            className="clay-btn"
            type="submit"
            disabled={loading}
            style={{ width: "100%", marginTop: "10px" }}
          >
            {loading ? "Processing..." : isLogin ? "Log In" : "Sign Up"}
          </button>
        </form>

        <div style={styles.divider}>
          <hr style={{ flex: 1, borderColor: "var(--border)" }} />
          <span style={{ margin: "0 10px", opacity: 0.5 }}>OR</span>
          <hr style={{ flex: 1, borderColor: "var(--border)" }} />
        </div>

        <div style={{ display: "flex", justifyContent: "center" }}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError("Google Login Failed")}
            theme="filled_black"
            shape="pill"
          />
        </div>
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
    backgroundColor: "rgba(0, 0, 0, 0.4)",
    backdropFilter: "blur(4px)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 1000,
  },
  modal: {
    width: "90%",
    maxWidth: "400px",
    position: "relative",
  },
  closeBtn: {
    position: "absolute",
    top: "15px",
    right: "15px",
    background: "transparent",
    border: "none",
    color: "var(--text)",
    fontSize: "1.2rem",
    cursor: "pointer",
  },
  tabs: {
    display: "flex",
    justifyContent: "center",
    gap: "20px",
    marginBottom: "20px",
  },
  tab: {
    background: "transparent",
    border: "none",
    color: "var(--text)",
    fontSize: "1.1rem",
    fontWeight: "bold",
    cursor: "pointer",
    paddingBottom: "5px",
    borderBottom: "2px solid var(--text)",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "15px",
  },
  input: {
    padding: "12px 15px",
    borderRadius: "8px",
    border: "1px solid var(--border)",
    background: "var(--bg)",
    color: "var(--text)",
    fontSize: "1rem",
    outline: "none",
  },
  divider: {
    display: "flex",
    alignItems: "center",
    margin: "25px 0",
  },
  error: {
    color: "#FF6B5A",
    textAlign: "center",
    margin: "0 0 15px 0",
    fontSize: "0.9rem",
  },
};
