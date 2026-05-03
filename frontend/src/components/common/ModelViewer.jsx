import { useRef, useCallback, useEffect, useState, Suspense } from "react";
import { motion } from "framer-motion";

/**
 * ModelViewer — A 3D model viewer using model-viewer web component.
 * Wraps the <model-viewer> custom element with lazy loading and mouse parallax.
 */
export default function ModelViewer({
  url,
  width = 400,
  height = 400,
  modelXOffset = 0,
  modelYOffset = 0,
  enableMouseParallax = false,
  enableHoverRotation = false,
  environmentPreset = "neutral",
  fadeIn = true,
  autoRotate = false,
  autoRotateSpeed = 0.35,
  showScreenshotButton = false,
  alt = "3D Model",
}) {
  const containerRef = useRef(null);
  const [loaded, setLoaded] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  useEffect(() => {
    // Check if model-viewer script is already loaded
    if (customElements.get("model-viewer")) {
      setScriptLoaded(true);
      return;
    }
    // Load model-viewer from CDN
    const script = document.createElement("script");
    script.type = "module";
    script.src =
      "https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js";
    script.onload = () => setScriptLoaded(true);
    document.head.appendChild(script);
  }, []);

  const handleMouseMove = useCallback(
    (e) => {
      if (!enableMouseParallax || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      const mv = containerRef.current.querySelector("model-viewer");
      if (mv) {
        mv.style.transform = `perspective(600px) rotateY(${x * 20}deg) rotateX(${-y * 20}deg)`;
      }
    },
    [enableMouseParallax],
  );

  const handleMouseLeave = useCallback(() => {
    if (!containerRef.current) return;
    const mv = containerRef.current.querySelector("model-viewer");
    if (mv)
      mv.style.transform = "perspective(600px) rotateY(0deg) rotateX(0deg)";
  }, []);

  const envMap = {
    forest: "neutral",
    neutral: "neutral",
    sunset: "neutral",
    city: "neutral",
  };

  return (
    <div
      ref={containerRef}
      style={{ width, height, position: "relative", display: "inline-block" }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {(!scriptLoaded || !loaded) && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(18,16,31,0.5)",
            borderRadius: 16,
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              border: "3px solid rgba(255,107,90,0.3)",
              borderTopColor: "#FF6B5A",
              animation: "spin 0.8s linear infinite",
            }}
          />
        </div>
      )}
      {scriptLoaded && (
        <model-viewer
          src={url}
          alt={alt}
          auto-rotate={autoRotate ? "" : undefined}
          auto-rotate-delay="0"
          rotation-per-second={`${autoRotateSpeed * 30}deg`}
          environment-image="neutral"
          shadow-intensity="1"
          camera-controls
          style={{
            width: "100%",
            height: "100%",
            borderRadius: 16,
            opacity: loaded ? 1 : 0,
            transition: fadeIn ? "opacity 0.5s ease" : "none",
          }}
          onLoad={() => setLoaded(true)}
        />
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
