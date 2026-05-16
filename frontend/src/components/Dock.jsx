import { useState, useRef } from "react";
import "./Dock.css";

const DOCK_ITEMS = [
  {
    id: "home",
    emoji: "🏠",
    label: "Dashboard",
  },
  {
    id: "scan",
    emoji: "📸",
    label: "Scan Meal",
  },
  {
    id: "meals",
    emoji: "🍽️",
    label: "My Meals",
  },
  {
    id: "planner",
    emoji: "📅",
    label: "Planner",
  },
  {
    id: "chat",
    emoji: "💬",
    label: "AI Chat",
  },
];

/**
 * macOS-style animated Dock with magnification and GlassSurface background.
 * Neobrutalist + Claymorphist style — bold borders, hard shadows, warm colors.
 */
export default function Dock({ activeTab, onTabChange }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const dockRef = useRef(null);

  const getScale = (index) => {
    if (hoveredIndex === null) return 1;
    const distance = Math.abs(index - hoveredIndex);
    if (distance === 0) return 1.5;
    if (distance === 1) return 1.22;
    if (distance === 2) return 1.08;
    return 1;
  };

  const getTranslateY = (index) => {
    if (hoveredIndex === null) return 0;
    const distance = Math.abs(index - hoveredIndex);
    if (distance === 0) return -14;
    if (distance === 1) return -8;
    if (distance === 2) return -3;
    return 0;
  };

  return (
    <div className="dock-wrapper">
      {/* GlassSurface background */}
      <div className="dock-glass" aria-hidden="true">
        <svg width="0" height="0" style={{ position: "absolute" }}>
          <defs>
            <filter id="dock-glass-filter">
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.65"
                numOctaves="3"
                stitchTiles="stitch"
                result="noise"
              />
              <feDisplacementMap
                in="SourceGraphic"
                in2="noise"
                scale="8"
                xChannelSelector="R"
                yChannelSelector="G"
                result="displaced"
              />
              <feComposite in="displaced" in2="SourceGraphic" operator="in" />
            </filter>
          </defs>
        </svg>
      </div>

      <nav className="dock-container" ref={dockRef} role="navigation" aria-label="Main navigation">
        {DOCK_ITEMS.map((item, index) => {
          const scale = getScale(index);
          const translateY = getTranslateY(index);
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              id={`dock-tab-${item.id}`}
              className={`dock-item${isActive ? " dock-item--active" : ""}`}
              style={{
                transform: `scale(${scale}) translateY(${translateY}px)`,
                transition: "transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1)",
              }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
              onClick={() => onTabChange(item.id)}
              aria-label={item.label}
              aria-current={isActive ? "page" : undefined}
            >
              <span className="dock-item__tooltip">{item.label}</span>
              <span className="dock-item__emoji" role="img" aria-hidden="true">
                {item.emoji}
              </span>
              {isActive && <span className="dock-item__dot" aria-hidden="true" />}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
