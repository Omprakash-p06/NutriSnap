import { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext();

export const XP_THRESHOLDS = [
  0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000,
];

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Settings State
  const [userSettings, setUserSettings] = useState({
    dailyCalorieGoal: 2000,
    proteinGoal: 150,
    carbsGoal: 200,
    fatGoal: 70,
  });

  // Gamification Flags
  const [justLeveledUp, setJustLeveledUp] = useState(false);
  const [viewMode, setViewMode] = useState("marketing"); // 'app' | 'marketing'

  // Initial Sync from Backend and Local
  useEffect(() => {
    const savedToken = localStorage.getItem("nutrisnap-token");

    if (savedToken) {
      setToken(savedToken);

      // Fetch fresh profile and settings from cloud
      fetch("/api/users/me", {
        headers: { Authorization: `Bearer ${savedToken}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Token expired or invalid");
          return res.json();
        })
        .then((user) => {
          setCurrentUser(user);
          setUserSettings({
            dailyCalorieGoal: user.dailyCalorieGoal || 2000,
            proteinGoal: user.proteinGoal || 150,
            carbsGoal: user.carbsGoal || 200,
            fatGoal: user.fatGoal || 70,
          });
          setViewMode("app");
        })
        .catch((err) => {
          console.error("Profile Sync Error:", err);
          logoutSession();
          setViewMode("marketing");
        });
    } else {
      setViewMode("marketing");
    }
  }, []);

  const loginSession = async (email, password) => {
    const data = await authAPI.login(email, password);
    setToken(data.token);
    localStorage.setItem("nutrisnap-token", data.token);

    // Fetch full profile
    const res = await fetch("/api/users/me", {
      headers: { Authorization: `Bearer ${data.token}` },
    });
    const user = await res.json();
    setCurrentUser(user);
    setViewMode("app");
    toggleAuthModal(false);
    return user;
  };

  const loginAsGuest = () => {
    // Guest mode remains local/mock for now or could call a guest endpoint
    const guestUser = {
      email: "guest@nutrisnap.local",
      full_name: "Guest",
      xp: 0,
      level: 1,
    };
    setToken("guest-token");
    setCurrentUser(guestUser);
    localStorage.setItem("nutrisnap-token", "guest-token");
    setViewMode("app");
    toggleAuthModal(false);
  };

  const updateUserSettings = async (newSettings) => {
    if (!currentUser || token === "guest-token") {
      setUserSettings((prev) => ({ ...prev, ...newSettings }));
      return;
    }

    // Optimistic Update
    const prevSettings = { ...userSettings };
    setUserSettings((prev) => ({ ...prev, ...newSettings }));

    try {
      const response = await fetch("/api/users/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newSettings),
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      // Backend returns full user object, extract settings or just use the returned ones
      setUserSettings({
        dailyCalorieGoal: data.dailyCalorieGoal || 2000,
        proteinGoal: data.proteinGoal || 150,
        carbsGoal: data.carbsGoal || 200,
        fatGoal: data.fatGoal || 70,
      });
    } catch (err) {
      console.error("Settings Update Failed:", err);
      setUserSettings(prevSettings); // Rollback
    }
  };

  const logoutSession = () => {
    setToken(null);
    setCurrentUser(null);
    localStorage.removeItem("nutrisnap-token");
    localStorage.removeItem("nutrisnap-user");
  };

  // Gamification Engine
  const addXp = (amount) => {
    if (!currentUser) return;

    setCurrentUser((prevUser) => {
      const newXp = prevUser.xp + amount;
      let newLevel = prevUser.level;
      let didLevelUp = false;

      // Calculate if XP pushed us over the next threshold
      if (newLevel < XP_THRESHOLDS.length && newXp >= XP_THRESHOLDS[newLevel]) {
        newLevel += 1;
        didLevelUp = true;
      }

      const updatedUser = { ...prevUser, xp: newXp, level: newLevel };

      // Save global persistence
      localStorage.setItem("nutrisnap-user", JSON.stringify(updatedUser));

      if (didLevelUp) {
        setJustLeveledUp(true);
      }

      return updatedUser;
    });
  };

  const clearLevelUp = () => setJustLeveledUp(false);

  const toggleAuthModal = (val) => setIsAuthModalOpen(val);

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        token,
        isAuthenticated: !!token,
        loginAsGuest,
        loginSession,
        logoutSession,
        addXp,
        justLeveledUp,
        clearLevelUp,
        userSettings,
        updateUserSettings,
        viewMode,
        setViewMode,
        isAuthModalOpen,
        toggleAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
