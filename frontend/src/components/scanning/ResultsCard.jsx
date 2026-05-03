import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Flame } from "lucide-react";
import SpotlightCard from "../common/SpotlightCard";
import DecryptedText from "../common/DecryptedText";
import PortionSlider from "../PortionSlider";
import SubstitutionCard from "./SubstitutionCard";

const Counter = ({ value }) => {
  return <span>{Math.round(value)}</span>; // Simplified for extraction, though framer-motion approach is better if kept separate
};

const MacroBar = ({ label, value, max, color }) => {
  return (
    <div className="macro-group">
      <div className="macro-label-row">
        <span>{label}</span>
        <span>{value}g</span>
      </div>
      <div className="macro-track">
        <motion.div
          className="macro-fill"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, (value / max) * 100)}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </div>
  );
};

export default function ResultsCard({
  result,
  multiplier,
  setMultiplier,
  category,
  setCategory,
  handleSaveToDiary,
  chartData,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, type: "spring", stiffness: 100 }}
    >
      <SpotlightCard className="glass-card results-card">
        <h2 className="text-gradient" style={{ margin: "0 0 15px 0" }}>
          <DecryptedText text={result.title} />
        </h2>

        <div
          style={{
            display: "flex",
            justifyContent: "space-around",
            margin: "20px 0",
          }}
        >
          <div
            className="clay-badge"
            style={{
              backgroundColor: "#FF6B5A",
              width: "auto",
              padding: "0 20px",
              borderRadius: "25px",
              fontSize: "1.2rem",
            }}
          >
            <Flame size={20} style={{ marginRight: "8px" }} />
            <Counter value={result.calories * multiplier} /> Cal
          </div>
        </div>

        {/* Animated Macro Slices */}
        <div style={{ padding: "0 10px", marginBottom: "25px" }}>
          <MacroBar
            label="Protein"
            value={result.protein * multiplier}
            max={100}
            color="#FF6B5A"
          />
          <MacroBar
            label="Carbs"
            value={result.carbs * multiplier}
            max={250}
            color="#FFB347"
          />
          <MacroBar
            label="Fat"
            value={result.fat * multiplier}
            max={100}
            color="#3ECFA0"
          />
        </div>

        <div
          style={{
            width: "100%",
            height: 180,
            overflow: "hidden",
            borderRadius: "12px",
            margin: "20px 0",
          }}
        >
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <XAxis dataKey="name" stroke="var(--text)" />
              <YAxis stroke="var(--text)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--bg)",
                  borderRadius: "8px",
                }}
              />
              <Bar
                dataKey="value"
                fill="url(#barGradient)"
                radius={[4, 4, 0, 0]}
              />
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#FF6B5A" />
                  <stop offset="100%" stopColor="#FFB347" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <PortionSlider onMultiplierChange={(val) => setMultiplier(val)} />

        <SubstitutionCard suggestions={result.suggestions} />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            width: "100%",
            maxWidth: "400px",
            marginTop: "20px",
          }}
        >
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="category-select"
          >
            <option>Breakfast</option>
            <option>Lunch</option>
            <option>Dinner</option>
            <option>Snacks</option>
          </select>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSaveToDiary}
            className="clay-btn"
            style={{ flex: 1, marginTop: 0, background: "#6B3FA0" }}
          >
            Save to Diary
          </motion.button>
        </div>
      </SpotlightCard>
    </motion.div>
  );
}
