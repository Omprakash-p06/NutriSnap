import { motion, AnimatePresence } from "framer-motion";
import { Camera, Search, Trash2, Zap, Globe, Sunrise, Sun, Moon, Apple } from "lucide-react";
import ShinyText from "../common/ShinyText";
import Magnet from "../common/Magnet";
import VoiceControl from "./VoiceControl";

/**
 * ScanBox component for food intake input.
 * Handles both camera capture and text-based search.
 */

const MEAL_CATEGORIES = [
  { value: "Breakfast", icon: Sunrise, color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
  { value: "Lunch",     icon: Sun,     color: "#3ecfa0", bg: "rgba(62,207,160,0.12)" },
  { value: "Dinner",    icon: Moon,    color: "#818cf8", bg: "rgba(129,140,248,0.12)" },
  { value: "Snacks",    icon: Apple,   color: "#FF6B5A", bg: "rgba(255,107,90,0.12)" },
];

export default function ScanBox({
  mode,
  setMode,
  image,
  setImage,
  isAnalyzing,
  searchQuery,
  setSearchQuery,
  handleSearch,
  handleCapture,
  setIsCameraOpen,
  setResult,
  category,
  setCategory,
}) {
  return (
    <section className="glass-panel scan-section">
      {/* ── Mode Toggle ── */}
      <div className="scan-mode-toggle">
        <motion.button
          id="scan-mode-btn"
          className={`scan-mode-btn ${mode === "scan" ? "scan-mode-btn--active-scan" : ""}`}
          onClick={() => setMode("scan")}
          whileTap={{ scale: 0.96 }}
          layout
        >
          <Camera size={17} />
          <span>Scan</span>
        </motion.button>

        <motion.button
          id="search-mode-btn"
          className={`scan-mode-btn ${mode === "search" ? "scan-mode-btn--active-search" : ""}`}
          onClick={() => setMode("search")}
          whileTap={{ scale: 0.96 }}
          layout
        >
          <Globe size={17} />
          <span>Search</span>
        </motion.button>
      </div>

      <AnimatePresence mode="wait">
        {mode === "scan" ? (
          <motion.div
            key="scan"
            className="actions-box"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {image ? (
              <div
                className={`scan-container ${isAnalyzing ? "pulsing-glow" : ""}`}
                style={{ width: "100%", maxWidth: "400px" }}
              >
                <img
                  src={image}
                  className="preview-image"
                  style={{ filter: isAnalyzing ? "blur(2px)" : "none" }}
                  alt="Food captured"
                />
                <AnimatePresence>
                  {isAnalyzing && (
                    <motion.div
                      className="scan-line"
                      initial={{ top: 0 }}
                      animate={{ top: "100%" }}
                      exit={{ opacity: 0 }}
                    />
                  )}
                </AnimatePresence>
                {isAnalyzing && (
                  <div style={{ textAlign: "center", marginTop: "15px" }}>
                    <p style={{ margin: 0, fontWeight: 700, color: "var(--primary-coral)" }}>
                      Analyzing with SAM2 &amp; EfficientNet...
                    </p>
                    <p style={{ margin: "4px 0 0 0", fontSize: "0.8rem", opacity: 0.7 }}>
                      Estimating volume &amp; nutritional mass
                    </p>
                  </div>
                )}
                {!isAnalyzing && (
                  <button
                    type="button"
                    onClick={() => {
                      setImage(null);
                      if (setResult) setResult(null);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "5px",
                      margin: "15px auto 0",
                      background: "transparent",
                      border: "none",
                      color: "#FF6B5A",
                      cursor: "pointer",
                    }}
                  >
                    <Trash2 size={16} /> Remove Image
                  </button>
                )}
              </div>
            ) : (
              <div className="scan-action-btns">
                <Magnet padding={50} magnetStrength={0.2}>
                  <motion.button
                    id="take-photo-btn"
                    whileHover={{ scale: 1.03, y: -3 }}
                    whileTap={{ scale: 0.97 }}
                    className="scan-action-btn scan-action-btn--primary"
                    disabled={isAnalyzing}
                    onClick={() => setIsCameraOpen(true)}
                  >
                    <Camera size={22} className="scan-action-btn__icon scan-action-btn__icon--coral" />
                    <ShinyText text="Take Photo" />
                  </motion.button>
                </Magnet>

                <motion.label
                  whileHover={{ scale: 1.03, y: -3 }}
                  whileTap={{ scale: 0.97 }}
                  className="scan-action-btn scan-action-btn--secondary"
                >
                  <Search size={18} className="scan-action-btn__icon scan-action-btn__icon--amber" />
                  Upload File
                  <input
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    disabled={isAnalyzing}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        const url = URL.createObjectURL(e.target.files[0]);
                        if (handleCapture) {
                          handleCapture(url);
                        } else {
                          setImage(url);
                        }
                      }
                    }}
                  />
                </motion.label>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.form
            key="search"
            className="search-box"
            onSubmit={handleSearch}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {/* Internet search hint */}
            <div className="search-hint">
              <Globe size={13} style={{ opacity: 0.6 }} />
              <span>Search any dish — we'll fetch nutrition from the internet</span>
            </div>

            {/* Input row */}
            <div style={{ display: "flex", gap: "10px", width: "100%", alignItems: "center" }}>
              <input
                type="text"
                placeholder="e.g., Chicken Biryani, 2 idli..."
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                disabled={isAnalyzing}
                style={{ flex: 1 }}
              />
              <VoiceControl
                isAnalyzing={isAnalyzing}
                onResult={(text) => setSearchQuery(text)}
              />
            </div>

            {/* Meal category pills */}
            <div className="meal-category-section">
              <p className="meal-category-label">Log as</p>
              <div className="meal-category-pills">
                {MEAL_CATEGORIES.map(({ value, icon: Icon, color, bg }) => (
                  <button
                    key={value}
                    type="button"
                    id={`category-pill-${value.toLowerCase()}`}
                    className={`meal-pill ${category === value ? "meal-pill--active" : ""}`}
                    style={category === value ? { borderColor: color, background: bg, color } : {}}
                    onClick={() => setCategory && setCategory(value)}
                  >
                    <Icon size={13} />
                    {value}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <Magnet padding={50} magnetStrength={0.2}>
              <motion.button
                id="search-food-btn"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                className="clay-btn search-submit-btn"
                disabled={isAnalyzing || !searchQuery.trim()}
              >
                {isAnalyzing ? (
                  <span className="search-submit-btn__loading">
                    <span className="search-loading-dot" />
                    <span className="search-loading-dot" />
                    <span className="search-loading-dot" />
                    Searching...
                  </span>
                ) : (
                  <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                    <Zap size={17} />
                    <ShinyText text="Find &amp; Log Dish" />
                  </span>
                )}
              </motion.button>
            </Magnet>
          </motion.form>
        )}
      </AnimatePresence>
    </section>
  );
}
