import { useState } from "react";
import "./Home.css";
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import { authAPI } from "../services/api";
import ScanBox from "../components/scanning/ScanBox";
import MultiFoodDisplay from "../components/scanning/MultiFoodDisplay";
import CameraModal from "../components/CameraModal";

export default function ScanPage() {
  const { addXp, token } = useAuth();
  const { addMeal } = useMealHistory();

  // Local scan state — these were incorrectly expected from AuthContext
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Defensive check for debugging
  if (typeof setImage !== 'function') {
    console.error("CRITICAL: setImage is not a function in ScanPage scope!", typeof setImage);
  }

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
    console.log("ScanPage: handleCapture called with dataUrl length:", dataUrl?.length);
    if (typeof setImage === 'function') {
      setImage(dataUrl);
    } else {
      console.error("ScanPage: setImage is not a function in handleCapture closure");
    }
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
      } else if (err.message === "No food found") {
        showNotification("Dish not found — try a more specific name (e.g. 'curd rice with pickle').", "warning");
      } else {
        const errMsg = `Search failed: ${err.message}`;
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
    <div className="page-container page-scan max-w-4xl mx-auto pt-6 px-4">
      <div className="text-center mb-10 mt-6">
        <h1 className="text-4xl font-bold text-foreground tracking-tight mb-2">Scan Your Meal</h1>
        <p className="text-zinc-400 text-lg">Take a photo or search for any food item</p>
      </div>

      <div className="flex flex-col items-center">
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
          category={category}
          setCategory={setCategory}
        />

        {result && !isAnalyzing && (
          <div className="w-full max-w-2xl mt-8 glass-panel">
            <MultiFoodDisplay
              result={result}
              handleSaveToDiary={handleSaveToDiary}
              category={category}
              setCategory={setCategory}
            />
          </div>
        )}
      </div>

      <CameraModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCapture}
      />

      {notification && (
        <div className={`fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-zinc-900 border border-zinc-700 text-white shadow-2xl z-[999] animate-bounce`}>
          <span>{notification.message}</span>
        </div>
      )}
    </div>
  );
}
