import { motion } from "framer-motion";

/**
 * WaterWave
 * An animated SVG wave that represents the current hydration level.
 */
export default function WaterWave({ percent = 0 }) {
  // Logic to calculate the vertical height of the wave filling
  const safePercent = isNaN(percent) ? 0 : percent;
  const waveHeight = 100 - Math.min(100, safePercent);

  return (
    <div
      className="water-wave-container"
      style={{
        width: "100px",
        height: "100px",
        borderRadius: "24px",
        overflow: "hidden",
        position: "relative",
        background: "rgba(255, 255, 255, 0.1)",
        border: "2px solid rgba(255, 255, 255, 0.2)",
        boxShadow: "0 8px 32px rgba(31, 38, 135, 0.15)",
        backdropFilter: "blur(4px)",
      }}
    >
      <motion.svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: "100%",
        }}
      >
        <motion.path
          animate={{
            d: [
              `M 0 ${waveHeight} Q 25 ${waveHeight - 5} 50 ${waveHeight} T 100 ${waveHeight} V 100 H 0 Z`,
              `M 0 ${waveHeight} Q 25 ${waveHeight + 5} 50 ${waveHeight} T 100 ${waveHeight} V 100 H 0 Z`,
              `M 0 ${waveHeight} Q 25 ${waveHeight - 5} 50 ${waveHeight} T 100 ${waveHeight} V 100 H 0 Z`,
            ],
          }}
          transition={{
            repeat: Infinity,
            duration: 2,
            ease: "easeInOut",
          }}
          fill="#3ECFA0"
          style={{ opacity: 0.8 }}
        />

        {/* Secondary overlapping wave for depth */}
        <motion.path
          animate={{
            d: [
              `M 0 ${waveHeight + 2} Q 25 ${waveHeight + 7} 50 ${waveHeight + 2} T 100 ${waveHeight + 2} V 100 H 0 Z`,
              `M 0 ${waveHeight + 2} Q 25 ${waveHeight - 3} 50 ${waveHeight + 2} T 100 ${waveHeight + 2} V 100 H 0 Z`,
              `M 0 ${waveHeight + 2} Q 25 ${waveHeight + 7} 50 ${waveHeight + 2} T 100 ${waveHeight + 2} V 100 H 0 Z`,
            ],
          }}
          transition={{
            repeat: Infinity,
            duration: 3,
            ease: "easeInOut",
            delay: 0.5,
          }}
          fill="#2AB18F"
          style={{ opacity: 0.5 }}
        />
      </motion.svg>

      {/* Percentage label */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          fontSize: "1.2rem",
          fontWeight: "800",
          color: safePercent > 50 ? "#fff" : "var(--text)",
          textShadow: safePercent > 50 ? "0 1px 4px rgba(0,0,0,0.2)" : "none",
          zIndex: 10,
        }}
      >
        {Math.round(safePercent)}%
      </div>
    </div>
  );
}
