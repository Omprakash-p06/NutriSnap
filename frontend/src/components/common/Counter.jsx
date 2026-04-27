import { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useTransform, useMotionValue } from 'framer-motion';

/**
 * Counter — An animated slot-machine style number counter.
 * Inlined from react-bits pattern for full control without external dependencies.
 */
export default function Counter({
  value = 0,
  places = [100, 10, 1],
  fontSize = 80,
  padding = 5,
  gap = 10,
  textColor = 'white',
  fontWeight = 900,
}) {
  return (
    <div
      style={{
        display: 'flex',
        overflow: 'hidden',
        lineHeight: 1,
        fontWeight,
        fontSize,
        color: textColor,
        gap,
      }}
    >
      {places.map((place, i) => (
        <Digit
          key={i}
          place={place}
          value={value}
          fontSize={fontSize}
          padding={padding}
          textColor={textColor}
          fontWeight={fontWeight}
        />
      ))}
    </div>
  );
}

function Digit({ place, value, fontSize, padding, textColor, fontWeight }) {
  const digit = Math.floor((value / place) % 10);
  const motionVal = useMotionValue(digit);
  const smoothVal = useSpring(motionVal, { stiffness: 100, damping: 20, mass: 1 });
  const y = useTransform(smoothVal, (v) => `${-v * (fontSize + padding * 2)}px`);

  useEffect(() => {
    motionVal.set(digit);
  }, [digit, motionVal]);

  return (
    <div
      style={{
        height: fontSize + padding * 2,
        overflow: 'hidden',
        position: 'relative',
        width: fontSize * 0.75 + padding,
      }}
    >
      <motion.div style={{ y, position: 'absolute' }}>
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            style={{
              height: fontSize + padding * 2,
              boxSizing: 'border-box',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize,
              fontWeight,
              color: textColor,
              paddingTop: padding,
              paddingBottom: padding,
            }}
          >
            {i}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
