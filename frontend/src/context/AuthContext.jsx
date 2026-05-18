import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

export const XP_THRESHOLDS = [
  0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000,
];

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isStreakModalOpen, setIsStreakModalOpen] = useState(false);
  const [justLeveledUp, setJustLeveledUp] = useState(false);
  const [viewMode, setViewMode] = useState("marketing");

  // Settings derived from backend profile, with sensible defaults
  const [userSettings, setUserSettings] = useState({
    dailyCalorieGoal: 2000,
    proteinGoal: 150,
    carbsGoal: 200,
    fatGoal: 70,
    waterGoal: 2500,
  });

  // User profile state (for OnboardingModal updates)
  const [userProfile, setUserProfile] = useState(() => {
    try {
      const saved = localStorage.getItem("nutrisnap-profile");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // ─── Auto-login guest on mount ───────────────────────────────────────────
  useEffect(() => {
    const initGuestSession = async () => {
      // Check if we already have a stored token (real user session)
      const storedToken = localStorage.getItem("nutrisnap-token");
      if (storedToken) {
        try {
          // Verify it's still valid by calling /auth/me or /users/me
          const res = await fetch("/api/users/me", {
            headers: { Authorization: `Bearer ${storedToken}` },
          });
          if (res.ok) {
            const user = await res.json();
            setToken(storedToken);
            setCurrentUser(user);
            _syncSettingsFromProfile(user);
            return;
          }
        } catch {
          // Token expired, fall through to guest
        }
        localStorage.removeItem("nutrisnap-token");
      }

      // Auto-issue guest JWT from backend
      console.log("AuthContext: Fetching guest token from /api/auth/guest...");
      try {
        const res = await fetch("/api/auth/guest");
        if (res.ok) {
          const data = await res.json();
          console.log("AuthContext: Guest token received successfully.");
          setToken(data.access_token);
          localStorage.setItem("nutrisnap-token", data.access_token);
          setCurrentUser({
            ...data.user,
            xp: data.user.xp ?? 1250,
            level: data.user.level ?? 4,
          });
          _syncSettingsFromProfile(data.user);
        } else {
          console.warn("AuthContext: Guest login failed with status:", res.status);
          const errorData = await res.json().catch(() => ({}));
          console.warn("AuthContext: Error details:", errorData);
          throw new Error("Guest login failed");
        }
      } catch (err) {
        console.error("AuthContext: Guest auto-login exception:", err);
        // Graceful degradation: show UI but features need backend
        setCurrentUser({
          email: "guest@nutrisnap.ai",
          full_name: "Guest User",
          xp: 0,
          level: 1,
        });
      }
    };

    initGuestSession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const _syncSettingsFromProfile = (user) => {
    if (!user) return;
    
    // Priority: Custom user-defined targets persisted in settings
    if (user.settings && user.settings.dailyCalorieGoal) {
      setUserSettings({
        dailyCalorieGoal: parseInt(user.settings.dailyCalorieGoal) || 2000,
        proteinGoal: parseInt(user.settings.proteinGoal) || 150,
        carbsGoal: parseInt(user.settings.carbsGoal) || 200,
        fatGoal: parseInt(user.settings.fatGoal) || 70,
        waterGoal: parseInt(user.settings.waterGoal) || Math.round((user.weight_kg || 70) * 35),
      });
      return;
    }

    const w = user.weight_kg;
    const h = user.height_cm;
    const a = user.age;
    const sex = user.gender;
    const activity = parseFloat(user.activity_level) || 1.55;
    const goal = user.goal || "maintain";

    if (w && h && a && sex) {
      const bmr =
        10 * w + 6.25 * h - 5 * a + (sex === "male" ? 5 : -161);
      const tdee = bmr * activity;
      let targetCal = tdee;
      if (goal === "lose") targetCal -= 500;
      if (goal === "gain") targetCal += 300;

      setUserSettings({
        dailyCalorieGoal: Math.round(targetCal),
        proteinGoal: Math.round(w * 1.6),
        carbsGoal: Math.round((targetCal * 0.45) / 4),
        fatGoal: Math.round((targetCal * 0.3) / 9),
        waterGoal: Math.round(w * 35),
      });
    }
  };

  // ─── Session management ───────────────────────────────────────────────────
  const loginSession = async (email, password) => {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("nutrisnap-token", data.access_token);
    setToken(data.access_token);
    setCurrentUser({ ...data.user, xp: data.user.xp ?? 0, level: data.user.level ?? 1 });
    _syncSettingsFromProfile(data.user);
    return data.user;
  };

  const loginAsGuest = () => setViewMode("app");

  const logoutSession = () => {
    localStorage.removeItem("nutrisnap-token");
    setToken(null);
    setCurrentUser(null);
    // Re-issue guest token
    fetch("/api/auth/guest")
      .then((r) => r.json())
      .then((data) => {
        setToken(data.access_token);
        setCurrentUser({ ...data.user, xp: data.user.xp ?? 1250, level: data.user.level ?? 4 });
      })
      .catch(() => {});
  };

  const updateUserSettings = (newSettings) =>
    setUserSettings((prev) => ({ ...prev, ...newSettings }));

  const updateUserProfile = async (newProfile) => {
    // 1. Prepare backend payload
    // Map activity numbers back to string enums for the backend
    const mapActivity = (val) => {
      const v = String(val);
      if (v === "1.2") return "sedentary";
      if (v === "1.375") return "light";
      if (v === "1.55") return "moderate";
      if (v === "1.725") return "active";
      if (v === "1.9") return "very_active";
      if (["sedentary", "light", "moderate", "active", "very_active"].includes(v)) return v;
      return undefined;
    };
    
    // Map goal back to enum for the backend
    const mapGoal = (val) => {
      if (val === "lose") return "weight_loss";
      if (val === "gain") return "muscle_gain";
      if (val === "maintain") return "maintenance";
      if (["weight_loss", "muscle_gain", "maintenance"].includes(val)) return val;
      return undefined;
    };

    const payload = {
      full_name: newProfile.name || newProfile.full_name,
      gender: newProfile.sex || newProfile.gender,
      weight_kg: newProfile.weight ? parseFloat(newProfile.weight || newProfile.weight_kg) : undefined,
      height_cm: newProfile.height ? parseFloat(newProfile.height || newProfile.height_cm) : undefined,
      age: newProfile.age ? parseInt(newProfile.age) : undefined,
      activity_level: mapActivity(newProfile.activityLevel || newProfile.activity_level),
      goal: mapGoal(newProfile.goal),
      location: newProfile.location,
      settings: newProfile.settings,
    };

    // Remove undefined/null and NaN values
    Object.keys(payload).forEach(key => {
      const val = payload[key];
      if (val === undefined || val === null || (typeof val === 'number' && isNaN(val))) {
        delete payload[key];
      }
    });

    if (token) {
      try {
        const res = await fetch("/api/users/me", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const updatedUser = await res.json();
          setCurrentUser(updatedUser);
          
          // Re-sync local profile format for components that rely on it
          // Map backend enums back to frontend multipliers
          const mapActivityBack = (val) => {
             if (val === "sedentary") return "1.2";
             if (val === "light") return "1.375";
             if (val === "moderate") return "1.55";
             if (val === "active") return "1.725";
             if (val === "very_active") return "1.9";
             return String(val);
          };
          const mapGoalBack = (val) => {
             if (val === "weight_loss") return "lose";
             if (val === "muscle_gain") return "gain";
             if (val === "maintenance") return "maintain";
             return String(val);
          };

          const localFormat = {
            name: updatedUser.full_name,
            sex: updatedUser.gender,
            weight: updatedUser.weight_kg,
            height: updatedUser.height_cm,
            age: updatedUser.age,
            activityLevel: mapActivityBack(updatedUser.activity_level),
            goal: mapGoalBack(updatedUser.goal),
            location: updatedUser.location,
            dietaryPreferences: updatedUser.settings?.dietaryPreferences || [],
          };
          setUserProfile(localFormat);
          localStorage.setItem("nutrisnap-profile", JSON.stringify(localFormat));
          _syncSettingsFromProfile(updatedUser);
          return updatedUser;
        }
      } catch (err) {
        console.error("AuthContext: Profile sync failed:", err);
      }
    }

    // Fallback/Guest local update
    setUserProfile(newProfile);
    localStorage.setItem("nutrisnap-profile", JSON.stringify(newProfile));
    _syncSettingsFromProfile({
      weight_kg: newProfile.weight,
      height_cm: newProfile.height,
      age: newProfile.age,
      gender: newProfile.sex,
      activity_level: String(newProfile.activityLevel),
      goal: newProfile.goal,
    });
  };

  const updateProfile = updateUserProfile; // Alias for backward compatibility


  // ─── Gamification ──────────────────────────────────────────────────────────
  const addXp = (amount) => {
    if (!currentUser) return;
    setCurrentUser((prev) => {
      const newXp = (prev.xp || 0) + amount;
      let newLevel = prev.level || 1;
      if (newLevel < XP_THRESHOLDS.length && newXp >= XP_THRESHOLDS[newLevel]) {
        newLevel += 1;
        setJustLeveledUp(true);
      }
      const updated = { ...prev, xp: newXp, level: newLevel };
      localStorage.setItem("nutrisnap-user", JSON.stringify(updated));
      return updated;
    });
  };

  const clearLevelUp = () => setJustLeveledUp(false);
  const toggleAuthModal = (val) => setIsAuthModalOpen(val);

  const bmi = userProfile
    ? (userProfile.weight / ((userProfile.height / 100) ** 2)).toFixed(1)
    : null;

  const tdee = userProfile
    ? (() => {
        const bmr =
          10 * userProfile.weight +
          6.25 * userProfile.height -
          5 * userProfile.age +
          (userProfile.sex === "male" ? 5 : -161);
        return Math.round(bmr * userProfile.activityLevel);
      })()
    : null;

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
        tdee,
        viewMode,
        setViewMode,
        isAuthModalOpen,
        toggleAuthModal,
        isStreakModalOpen,
        setIsStreakModalOpen,
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
