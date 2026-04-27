import { motion } from 'framer-motion';

/**
 * ShinyText
 * A shimmering text effect that adds a premium feel to buttons and labels.
 */
export default function ShinyText({ 
  text, 
  disabled = false, 
  speed = 3, 
  className = "",
  baseColor = "var(--text)"
}) {
  const animationProps = !disabled ? {
    animate: {
      backgroundPosition: ["200% 0", "-200% 0"],
    },
    transition: {
      repeat: Infinity,
      duration: speed,
      ease: "linear",
    }
  } : {};

  return (
    <motion.span
      {...animationProps}
      className={`shiny-text ${className}`}
      style={{
        backgroundImage: `linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.8) 50%, transparent 70%)`,
        backgroundColor: baseColor,
        backgroundSize: "200% 100%",
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        display: "inline-block",
        backgroundBlendMode: "screen"
      }}
    >
      {text}
    </motion.span>
  );
}
