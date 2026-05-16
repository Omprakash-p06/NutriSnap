import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import { authAPI } from "../services/api";
import ScanBox from "../components/scanning/ScanBox";
import MultiFoodDisplay from "../components/scanning/MultiFoodDisplay";
import CameraModal from "../components/CameraModal";
import GridBackground from "../components/common/GridBackground";

export default function ScanPage() {
  const {
    addXp,
    token,
    scanResult: result,
    setScanResult: setResult,
    scanImage: image,
    setScanImage: setImage,
    isAnalyzing,
    setIsAnalyzing,
  } = useAuth();
  const { addMeal } = useMealHistory();

  const [mode, setMode] = useState("scan");
  const [category, setCategory] = useState("Snacks");
  const [searchQuery, setSearchQuery] = useState("");
  const [multiplier, setMultiplier] = useState(1.0);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
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
      showNotification("Offline: Please connect to the internet.", "offline");
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
        showNotification("Couldn't identify that food clearly. Try typing it!", "warning");
        setMode("search");
      } else {
        const errMsg = `Analysis Failed: ${err.message}`;
        showNotification(errMsg, "error");
        console.error("SCAN ERROR:", err);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveToDiary = async () => {
    try {
      const payload = {
        food_name: result.title,
        calories: Math.round(result.calories * multiplier),
        protein: Math.round(result.protein * multiplier),
        carbs: Math.round(result.carbs * multiplier),
        fat: Math.round(result.fat * multiplier),
        category,
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

  return (
    <div className="page-scan">
      <GridBackground />

      <div className="page-scan__header">
        <h1 className="page-title">Scan Your Meal</h1>
        <p className="page-subtitle">Take a photo or search for any food item</p>
      </div>

      <ScanBox
        mode={mode}
        setMode={setMode}
        image={image}
        setImage={setImage}
        isAnalyzing={isAnalyzing}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        handleSearch={handleSearch}
        handleCapture={handleCapture}
        setIsCameraOpen={setIsCameraOpen}
        setResult={setResult}
      />

      {result && !isAnalyzing && (
        <div className="page-scan__results">
          <MultiFoodDisplay
            result={result}
            handleSaveToDiary={handleSaveToDiary}
            category={category}
            setCategory={setCategory}
          />
        </div>
      )}

      <CameraModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCapture}
      />

      {notification && (
        <div className={`notification-toast notification-toast--${notification.type}`}>
          <span>{notification.message}</span>
        </div>
      )}
    </div>
  );
}
