import { motion, AnimatePresence } from "framer-motion";
import { Camera, Search, Trash2, Zap, Mic } from "lucide-react";
import ShinyText from "../common/ShinyText";
import Magnet from "../common/Magnet";
import VoiceControl from "./VoiceControl";

/**
 * ScanBox component for food intake input.
 * Handles both camera capture and text-based search.
 */
export default function ScanBox({
  mode,
  setMode,
  image,
  setImage,
  isAnalyzing,
  searchQuery,
  setSearchQuery,
  handleSearch,
  setIsCameraOpen,
  setResult,
}) {
  return (
    <section className="glass-panel scan-section">
      {/* Toggle Controls */}
      <div className="segmented-control">
        <button
          className={`segment-btn ${mode === "scan" ? "active" : ""}`}
          onClick={() => {
            setMode("scan");
          }}
        >
          <Camera
            size={18}
            style={{ marginRight: "8px", verticalAlign: "middle" }}
          />
          Scan
        </button>
        <button
          className={`segment-btn ${mode === "search" ? "active" : ""}`}
          onClick={() => {
            setMode("search");
          }}
        >
          <Search
            size={18}
            style={{ marginRight: "8px", verticalAlign: "middle" }}
          />
          Search
        </button>
      </div>

      {mode === "scan" ? (
        <div className="actions-box">
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
                  <p
                    style={{
                      margin: 0,
                      fontWeight: 700,
                      color: "var(--primary-coral)",
                    }}
                  >
                    Analyzing with SAM2 & EfficientNet...
                  </p>
                  <p
                    style={{
                      margin: "4px 0 0 0",
                      fontSize: "0.8rem",
                      opacity: 0.7,
                    }}
                  >
                    Estimating volume & nutritional mass
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                gap: "20px",
                flexDirection: "column",
                width: "100%",
                maxWidth: "300px",
              }}
            >
              <Magnet padding={50} magnetStrength={0.2}>
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className="clay-btn"
                  disabled={isAnalyzing}
                  style={{
                    padding: "20px",
                    fontSize: "1.2rem",
                    margin: 0,
                    width: "100%",
                  }}
                  onClick={() => setIsCameraOpen(true)}
                >
                  <ShinyText text="Take Photo" />
                </motion.button>
              </Magnet>

              <motion.label
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                className="clay-btn"
                style={{
                  cursor: "pointer",
                  textAlign: "center",
                  background: "transparent",
                  color: "var(--text)",
                  border: "2px solid var(--primary-amber)",
                }}
              >
                Upload File
                <input
                  type="file"
                  accept="image/*"
                  style={{ display: "none" }}
                  disabled={isAnalyzing}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setImage(URL.createObjectURL(e.target.files[0]));
                    }
                  }}
                />
              </motion.label>
            </div>
          )}
        </div>
      ) : (
        <form className="search-box" onSubmit={handleSearch}>
          {image && (
            <div style={{ textAlign: "center", marginBottom: "10px" }}>
              <img
                src={image}
                style={{ width: "100px", borderRadius: "10px" }}
                alt="Reference"
              />
              <button
                type="button"
                onClick={() => setImage(null)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "5px",
                  margin: "5px auto",
                  background: "transparent",
                  border: "none",
                  color: "#FF6B5A",
                  cursor: "pointer",
                }}
              >
                <Trash2 size={14} /> Remove Image
              </button>
            </div>
          )}

          <div
            style={{
              display: "flex",
              gap: "10px",
              width: "100%",
              alignItems: "center",
            }}
          >
            <input
              type="text"
              placeholder="e.g., 2 Scrambled Eggs..."
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
          <Magnet padding={50} magnetStrength={0.2}>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="clay-btn"
              disabled={isAnalyzing || !searchQuery.trim()}
              style={{ background: "#3ECFA0", width: "100%" }}
            >
              {isAnalyzing ? (
                "Searching API..."
              ) : (
                <span
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                  }}
                >
                  <Zap size={18} /> <ShinyText text="Log Food" />
                </span>
              )}
            </motion.button>
          </Magnet>
        </form>
      )}
    </section>
  );
}
