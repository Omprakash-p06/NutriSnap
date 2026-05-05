import { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext();

export const XP_THRESHOLDS = [
  0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000,
];

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState({
    email: "guest@nutrisnap.ai",
    full_name: "Guest User",
    xp: 0,
    level: 1,
  });
  const [token, setToken] = useState("guest-token");
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
  const [viewMode, setViewMode] = useState("marketing"); // Start on marketing/landing page

  // User Profile State (Gender, Weight, Height)
  const [userProfile, setUserProfile] = useState(() => {
    const saved = localStorage.getItem("nutrisnap-profile");
    return saved ? JSON.parse(saved) : null;
  });

  // Initial Sync — disabled for simplified MVP
  useEffect(() => {
    // No-op
  }, []);

  const loginSession = async (email, password) => {
    // No-op for simplified MVP
    return currentUser;
  };

  const loginAsGuest = () => {
    setViewMode("app");
  };

  const updateUserSettings = async (newSettings) => {
    // Always local for simplified MVP
    setUserSettings((prev) => ({ ...prev, ...newSettings }));
  };

  const updateProfile = (newProfile) => {
    setUserProfile(newProfile);
    localStorage.setItem("nutrisnap-profile", JSON.stringify(newProfile));
  };

  const bmi = userProfile ? (userProfile.weight / ((userProfile.height / 100) ** 2)).toFixed(1) : null;

  const logoutSession = () => {
    // No-op or just reset to guest
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
        userProfile,
        updateProfile,
        bmi,
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
