import { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext();

export const XP_THRESHOLDS = [
  0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000,
];

const DEFAULT_SETTINGS = {
  dailyCalorieGoal: 2000,
  proteinGoal: 150,
  carbsGoal: 200,
  fatGoal: 70,
  waterGoal: 2500,
  streak: 0,
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(() => {
    const savedUser = localStorage.getItem("nutrisnap-user");
    return savedUser
      ? JSON.parse(savedUser)
      : {
          email: "guest@nutrisnap.ai",
          full_name: "Guest User",
          xp: 0,
          level: 1,
        };
  });
  const [token, setToken] = useState(() => localStorage.getItem("nutrisnap-token"));
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Settings State
  const [userSettings, setUserSettings] = useState(DEFAULT_SETTINGS);

  // Gamification Flags
  const [justLeveledUp, setJustLeveledUp] = useState(false);
  const [viewMode, setViewMode] = useState("marketing"); // Start on marketing/landing page
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isStreakModalOpen, setIsStreakModalOpen] = useState(false);

  // Scanning State (moved to context for global control)
  const [scanResult, setScanResult] = useState(null);
  const [scanImage, setScanImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // User Profile State (Gender, Weight, Height)
  const [userProfile, setUserProfile] = useState(() => {
    const saved = localStorage.getItem("nutrisnap-profile");
    return saved ? JSON.parse(saved) : null;
  });

  const toLocalProfile = (user) => {
    if (!user) return null;

    return {
      full_name: user.full_name || "",
      age: user.age ?? "",
      sex: user.gender || "male",
      weight: user.weight_kg ?? "",
      height: user.height_cm ?? "",
      activityLevel: user.activity_level ? String(user.activity_level) : "1.2",
      goal: user.goal || "maintain",
      dietaryPreferences:
        user.settings?.dietaryPreferences || user.dietaryPreferences || [],
    };
  };

  const persistUser = (user) => {
    setCurrentUser(user);
    localStorage.setItem("nutrisnap-user", JSON.stringify(user));
    setUserProfile(toLocalProfile(user));
    localStorage.setItem("nutrisnap-profile", JSON.stringify(toLocalProfile(user)));

    if (user?.settings) {
      setUserSettings((prev) => ({ ...prev, ...user.settings }));
    }
  };

  // Initial Sync — disabled for simplified MVP
  useEffect(() => {
    const syncProfile = async () => {
      if (!token) return;

      try {
        const profile = await authAPI.getMe();
        persistUser(profile);
      } catch (err) {
        console.error("Failed to sync profile:", err);
      }
    };

    syncProfile();
  }, [token]);

  const resetScan = () => {
    setScanResult(null);
    setScanImage(null);
    setIsAnalyzing(false);
  };

  const loginSession = async (email, password) => {
    try {
      const res = await authAPI.login(email, password);
      const fullUser = res.user;

      setToken(res.token);
      localStorage.setItem("nutrisnap-token", res.token);
      persistUser(fullUser);
      
      setViewMode("app");
      resetScan();
      setIsAuthModalOpen(false);
      return fullUser;
    } catch (err) {
      console.error("Login failed:", err);
      throw err;
    }
  };

  const loginAsGuest = () => {
    setCurrentUser({
      email: "guest@nutrisnap.ai",
      full_name: "Guest User",
      xp: 0,
      level: 1,
    });
    setToken(null);
    setUserProfile(null);
    setUserSettings(DEFAULT_SETTINGS);
    localStorage.removeItem("nutrisnap-token");
    localStorage.removeItem("nutrisnap-user");
    localStorage.removeItem("nutrisnap-profile");
    setViewMode("app");
    resetScan();
  };

  const updateUserSettings = async (newSettings) => {
    const updatedSettings = { ...userSettings, ...newSettings };

    if (!token) {
      setUserSettings(updatedSettings);
      return updatedSettings;
    }

    const updatedUser = await authAPI.updateMe({ settings: updatedSettings });
    setUserSettings(updatedSettings);
    persistUser(updatedUser);
    return updatedSettings;
  };

  const updateProfile = async (newProfile) => {
    // Robust validation to prevent NaN propagation
    const validatedProfile = {
      ...newProfile,
      age: parseInt(newProfile.age) || 25,
      weight: parseFloat(newProfile.weight) || 70,
      height: parseFloat(newProfile.height) || 170,
      activityLevel: parseFloat(newProfile.activityLevel) || 1.2,
      sex: newProfile.sex || 'male',
      goal: newProfile.goal || 'maintain'
    };

    const payload = {
      full_name: newProfile.full_name || currentUser?.full_name,
      age: validatedProfile.age,
      gender: validatedProfile.sex,
      weight_kg: validatedProfile.weight,
      height_cm: validatedProfile.height,
      activity_level: validatedProfile.activityLevel.toString(),
      goal: validatedProfile.goal,
      settings: newProfile.dietaryPreferences
        ? { dietaryPreferences: newProfile.dietaryPreferences }
        : undefined,
    };

    if (!token) {
      setUserProfile(validatedProfile);
      localStorage.setItem("nutrisnap-profile", JSON.stringify(validatedProfile));
      return validatedProfile;
    }

    const updatedUser = await authAPI.updateMe(payload);
    persistUser(updatedUser);
    
    // Auto-update goals based on new profile
    const { weight, height, age, sex, activityLevel, goal: userGoal } = validatedProfile;
    
    const bmr = (10 * weight) + (6.25 * height) - (5 * age) + (sex === 'male' ? 5 : -161);
    const tdee = bmr * activityLevel;
    
    // Goal adjustment
    let targetCalories = tdee;
    if (userGoal === 'lose') targetCalories -= 500;
    if (userGoal === 'gain') targetCalories += 300;

    // Ensure we never have negative or NaN calories
    targetCalories = Math.max(1200, Math.round(targetCalories) || 2000);

    // Protein based on activity level (0.8 - 2.0 g/kg)
    const proteinMap = {
      '1.2': 0.8,
      '1.375': 1.1,
      '1.55': 1.4,
      '1.725': 1.7,
      '1.9': 2.0
    };
    const proteinPerKg = proteinMap[activityLevel.toString()] || 1.2;
    const proteinGoal = Math.round(weight * proteinPerKg) || 150;

    // Water intake (35ml per kg)
    const waterGoal = Math.round(weight * 35) || 2500; // in ml

    updateUserSettings({
      dailyCalorieGoal: targetCalories,
      proteinGoal: proteinGoal,
      waterGoal: waterGoal,
      carbsGoal: Math.round((targetCalories * 0.45) / 4),
      fatGoal: Math.round((targetCalories * 0.30) / 9),
    });

    return validatedProfile;
  };

  const bmi = userProfile ? (userProfile.weight / ((userProfile.height / 100) ** 2)).toFixed(1) : null;
  const tdee = userProfile ? (() => {
    const bmr = (10 * userProfile.weight) + (6.25 * userProfile.height) - (5 * userProfile.age) + (userProfile.sex === 'male' ? 5 : -161);
    return Math.round(bmr * userProfile.activityLevel);
  })() : null;

  const logoutSession = () => {
    setCurrentUser({
      email: "guest@nutrisnap.ai",
      full_name: "Guest User",
      xp: 0,
      level: 1,
    });
    setToken(null);
    setUserProfile(null);
    setUserSettings(DEFAULT_SETTINGS);
    setIsOnboardingOpen(false);
    setIsStreakModalOpen(false);
    setIsAuthModalOpen(false);
    localStorage.removeItem("nutrisnap-token");
    localStorage.removeItem("nutrisnap-user");
    localStorage.removeItem("nutrisnap-profile");
    setViewMode("marketing");
    resetScan();
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
        tdee,
        viewMode,
        setViewMode,
        isAuthModalOpen,
        toggleAuthModal,
        isOnboardingOpen,
        setIsOnboardingOpen,
        isStreakModalOpen,
        setIsStreakModalOpen,
        scanResult,
        setScanResult,
        scanImage,
        setScanImage,
        isAnalyzing,
        setIsAnalyzing,
        resetScan,
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
