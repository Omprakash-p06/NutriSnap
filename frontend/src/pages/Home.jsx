import "./Home.css";
import { useEffect } from "react";

// Context & Hooks
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";

// Components
import LevelUpModal from "../components/LevelUpModal";
import OnboardingModal from "../components/OnboardingModal.jsx";
import AuthModal from "../components/AuthModal.jsx";
import GridBackground from "../components/common/GridBackground";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import DailyCheckpoints from "../components/dashboard/DailyCheckpoints";
import InsightCards from "../components/dashboard/InsightCards";

export default function Home({ isSettingsOpenExternal, setIsSettingsOpenExternal }) {
  const {
    userSettings,
    userProfile,
    viewMode,
    setIsOnboardingOpen,
  } = useAuth();
  
  const { todayMeals, todayCalories, todayMacros } = useMealHistory();
  const setIsSettingsOpen = setIsSettingsOpenExternal;

  // Show onboarding if they enter the app without a profile
  useEffect(() => {
    if (viewMode === "app" && !userProfile) {
      setIsOnboardingOpen(true);
    }
  }, [viewMode, userProfile, setIsOnboardingOpen]);

  return (
    <div className="home-container page-home">
      <GridBackground />

      <div style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}>
        <section style={{ width: "100%", maxWidth: "900px", margin: "20px 0" }}>
          
          <DashboardHeader
            todayCalories={todayCalories}
            userSettings={userSettings}
            setIsSettingsOpen={setIsSettingsOpen}
          />
          
          <div style={{ marginTop: "24px" }}>
            <InsightCards />
          </div>

          <div style={{ marginTop: "24px" }}>
            <DailyCheckpoints
              todayCalories={todayCalories}
              todayMeals={todayMeals}
              todayMacros={todayMacros}
            />
          </div>
          
        </section>
      </div>

      <LevelUpModal />
      <OnboardingModal />
      <AuthModal />
    </div>
  );
}
