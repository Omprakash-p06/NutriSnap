import "./Home.css";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

// Context & Hooks
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import { authAPI } from "../services/api";

// Components
import CameraModal from "../components/CameraModal";
import LevelUpModal from "../components/LevelUpModal";
import SettingsModal from "../components/SettingsModal.jsx";
import { DashboardPage } from "./DashboardPage.jsx";

// New Modular Components
import GridBackground from "../components/common/GridBackground";
import LandingPage from "../components/layout/LandingPage";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import MealList from "../components/dashboard/MealList";
import ScanBox from "../components/scanning/ScanBox";
import ResultsCard from "../components/scanning/ResultsCard";
import HydrationWidget from "../components/dashboard/HydrationWidget";
import InsightCards from "../components/dashboard/InsightCards";
import CommunityFeed from "../components/social/CommunityFeed";
import ChatBot from "../components/ChatBot";

export default function Home() {
  const {
    isAuthenticated,
    addXp,
    userSettings,
    currentUser,
    viewMode,
    setViewMode,
    token,
  } = useAuth();
  const { todayMeals, todayCalories, addMeal, deleteMeal } = useMealHistory();

  // Mode & Data states
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [multiplier, setMultiplier] = useState(1.0);

  // View/Modal states
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [mode, setMode] = useState("scan");
  const [category, setCategory] = useState("Snacks");
  const [searchQuery, setSearchQuery] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const showNotification = (message, type = "info") => {
    setNotification({ message, type });
  };

  const handleCapture = async (dataUrl) => {
    setImage(dataUrl);
    await analyzePayload("image", dataUrl);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (searchQuery.trim().length > 0) {
      await analyzePayload("text", searchQuery);
    }
  };

  const analyzePayload = async (type, payload) => {
    if (!navigator.onLine) {
      showNotification(
        "Offline: Please connect to the internet to analyze meals.",
        "offline",
      );
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      let data;
      if (type === "image") {
        data = await authAPI.scanImage(payload);
      } else {
        data = await authAPI.searchFood(payload);
      }
      setResult(data);
      setMultiplier(1.0);
      setSearchQuery("");
    } catch (err) {
      if (err.message === "AI_UNCERTAINTY") {
        showNotification(
          "We couldn't identify that food clearly. Try typing it!",
          "warning",
        );
        setMode("search");
      } else {
        showNotification(`Analysis Failed: ${err.message}`, "error");
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveToDiary = async () => {
    if (!isAuthenticated) {
      showNotification("Please login first to save meals!", "warning");
      return;
    }

    try {
      // 1. Prepare payload for real backend
      const payload = {
        food_name: result.title,
        calories: Math.round(result.calories * multiplier),
        protein: Math.round(result.protein * multiplier),
        carbs: Math.round(result.carbs * multiplier),
        fat: Math.round(result.fat * multiplier),
        category: category,
        mass_g: result.mass_g ? Math.round(result.mass_g * multiplier) : 0,
      };

      const res = await fetch("/api/logs/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to save to cloud");

      // 2. Local update (optional but good for speed)
      addMeal({ ...result, category }, multiplier);

      addXp(50);
      setResult(null);
      setImage(null);
      setSearchQuery("");
      setMultiplier(1.0);
      setCategory("Snacks");
      showNotification("Meal saved successfully!", "success");
    } catch (err) {
      console.error("Save failed:", err);
      showNotification("Failed to save meal. Please try again.", "error");
    }
  };

  const chartData = result
    ? [
        { name: "Protein", value: Math.round(result.protein * multiplier) },
        { name: "Carbs", value: Math.round(result.carbs * multiplier) },
        { name: "Fat", value: Math.round(result.fat * multiplier) },
      ]
    : [];

  return (
    <div className="home-container">
      <GridBackground />

      {/* HEADER: DASHBOARD vs. HERO */}
      <AnimatePresence mode="wait">
        {!result && !image && !isAnalyzing && (
          <motion.div
            key="header-section"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.4 }}
            style={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            {isAuthenticated && viewMode === "app" ? (
              <section
                style={{ width: "100%", maxWidth: "900px", margin: "20px 0" }}
              >
                <InsightCards />
                <div
                  className="dashboard-layout-grid"
                  style={{
                    display: "flex",
                    gap: "30px",
                    flexWrap: "wrap",
                    justifyContent: "center",
                  }}
                >
                  <DashboardHeader
                    todayCalories={todayCalories}
                    userSettings={userSettings}
                    setIsSettingsOpen={setIsSettingsOpen}
                  />
                  <div className="v-divider"></div>
                  <MealList todayMeals={todayMeals} deleteMeal={deleteMeal} />
                </div>
                <div style={{ margin: "20px 0" }}>
                  <HydrationWidget />
                </div>
                <DashboardPage />
                <CommunityFeed />
              </section>
            ) : (
              <LandingPage onGetStarted={() => setViewMode("app")} />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* SEARCH / SCAN SECTION */}
      <ScanBox
        mode={mode}
        setMode={setMode}
        image={image}
        setImage={setImage}
        isAnalyzing={isAnalyzing}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        handleSearch={handleSearch}
        setIsCameraOpen={setIsCameraOpen}
        setResult={setResult}
      />

      {/* RESULTS SECTION */}
      {result && !isAnalyzing && (
        <ResultsCard
          result={result}
          multiplier={multiplier}
          setMultiplier={setMultiplier}
          category={category}
          setCategory={setCategory}
          handleSaveToDiary={handleSaveToDiary}
          chartData={chartData}
        />
      )}

      {/* Modals & Overlays */}
      <CameraModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCapture}
      />
      <LevelUpModal />
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {notification && (
        <div className="notification-toast">
          <span>{notification.message}</span>
        </div>
      )}

      {isAuthenticated && <ChatBot token={token} />}
    </div>
  );
}
