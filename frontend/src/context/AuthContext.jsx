import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const XP_THRESHOLDS = [0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000];

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);
  
  // Settings State
  const [userSettings, setUserSettings] = useState({
    dailyCalorieGoal: 2000,
    proteinGoal: 150,
    carbsGoal: 200,
    fatGoal: 70
  });
  
  // Gamification Flags
  const [justLeveledUp, setJustLeveledUp] = useState(false);
  const [viewMode, setViewMode] = useState('marketing'); // 'app' | 'marketing'

  // Initial Sync from Backend and Local
  useEffect(() => {
    const savedToken = localStorage.getItem('nutrisnap-token');
    const savedUser = localStorage.getItem('nutrisnap-user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      const user = JSON.parse(savedUser);
      setCurrentUser(user);
      
      // Fetch fresh settings from cloud
      fetch(`/api/user/settings?email=${encodeURIComponent(user.email)}`)
        .then(res => res.json())
        .then(data => {
          if (!data.error) setUserSettings(data);
          setViewMode('app');
        })
        .catch(err => {
          console.error('Settings Sync Error:', err);
          setViewMode('app');
        });
    } else {
      setViewMode('marketing');
    }
  }, []);

  const loginAsGuest = () => {
    const guestUser = {
      email: 'guest@nutrisnap.local',
      name: 'Guest',
      xp: 0,
      level: 1
    };
    setToken('guest-token');
    setCurrentUser(guestUser);
    localStorage.setItem('nutrisnap-token', 'guest-token');
    localStorage.setItem('nutrisnap-user', JSON.stringify(guestUser));
    setViewMode('app');
    
    // Set default standard settings locally
    setUserSettings({
      dailyCalorieGoal: 2000,
      proteinGoal: 150,
      carbsGoal: 200,
      fatGoal: 70
    });
  };

  const updateUserSettings = async (newSettings) => {
    if (!currentUser) return;
    
    // Optimistic Update
    const prevSettings = { ...userSettings };
    setUserSettings(prev => ({ ...prev, ...newSettings }));

    try {
      const response = await fetch('/api/user/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: currentUser.email, ...newSettings })
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      setUserSettings(data);
    } catch (err) {
      console.error('Settings Update Failed:', err);
      setUserSettings(prevSettings); // Rollback
    }
  };

  const logoutSession = () => {
    setToken(null);
    setCurrentUser(null);
    localStorage.removeItem('nutrisnap-token');
    localStorage.removeItem('nutrisnap-user');
  };

  // Gamification Engine
  const addXp = (amount) => {
    if (!currentUser) return;
    
    setCurrentUser(prevUser => {
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
      localStorage.setItem('nutrisnap-user', JSON.stringify(updatedUser));
      
      if (didLevelUp) {
        setJustLeveledUp(true);
      }

      return updatedUser;
    });
  };

  const clearLevelUp = () => setJustLeveledUp(false);

  return (
    <AuthContext.Provider value={{ 
      currentUser, 
      token, 
      isAuthenticated: !!token,
      loginAsGuest, 
      logoutSession,
      addXp,
      justLeveledUp,
      clearLevelUp,
      userSettings,
      updateUserSettings,
      viewMode,
      setViewMode
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
