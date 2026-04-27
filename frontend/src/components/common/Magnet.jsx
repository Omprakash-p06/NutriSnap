import { useRef, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Magnet
 * Wraps child elements to create a magnetic pull effect towards the cursor.
 */
export default function Magnet({ 
  children, 
  padding = 100, // Distance (px) at which the magnet effect starts
  disabled = false, 
  magnetStrength = 0.5 // Higher is stronger pull
}) {
  const [isActive, setIsActive] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const magnetRef = useRef(null);

  const handleMouseMove = (e) => {
    if (disabled || !magnetRef.current) return;
    
    const { clientX, clientY } = e;
    const { width, height, left, top } = magnetRef.current.getBoundingClientRect();
    
    // Center point of the element
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    
    const distanceX = clientX - centerX;
    const distanceY = clientY - centerY;
    
    // Check if cursor is within padding distance
    const absoluteDistance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
    
    if (absoluteDistance < padding + Math.max(width, height) / 2) {
      setIsActive(true);
      setPosition({ 
        x: distanceX * magnetStrength, 
        y: distanceY * magnetStrength 
      });
    } else {
      setIsActive(false);
      setPosition({ x: 0, y: 0 });
    }
  };

  const handleMouseLeave = () => {
    setIsActive(false);
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.div
      ref={magnetRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: position.x, y: position.y }}
      transition={{ 
        type: "spring", 
        stiffness: 150, 
        damping: 15, 
        mass: 0.1 
      }}
      style={{ display: 'inline-block' }}
    >
      {children}
    </motion.div>
  );
}
