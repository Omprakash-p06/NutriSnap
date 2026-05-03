import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";
import SpotlightCard from "../common/SpotlightCard";

/**
 * SubstitutionCard
 * Displays healthy alternatives suggested by AI.
 */
export default function SubstitutionCard({ suggestions = [] }) {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="substitutions-container" style={{ marginTop: "20px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "12px",
        }}
      >
        <Sparkles size={18} color="var(--primary-amber)" />
        <h4 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>
          Smart Swaps
        </h4>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "15px",
        }}
      >
        {suggestions.map((item, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <SpotlightCard
              className="glass-card"
              glowColor="rgba(255, 191, 0, 0.1)"
              style={{ padding: "12px" }}
            >
              <div
                style={{
                  fontSize: "0.9rem",
                  fontWeight: 700,
                  marginBottom: "4px",
                  color: "var(--primary-amber)",
                }}
              >
                {item.name}
              </div>
              <div
                style={{ fontSize: "0.75rem", opacity: 0.7, lineHeight: 1.3 }}
              >
                {item.reason}
              </div>
              <motion.div
                whileHover={{ x: 3 }}
                style={{
                  marginTop: "8px",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  opacity: 0.8,
                  cursor: "pointer",
                }}
              >
                Try this <ArrowRight size={12} />
              </motion.div>
            </SpotlightCard>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
