'use client';

import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from 'motion/react';
import { Children, cloneElement, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

function DockItem({ children, className = '', onClick, mouseX, spring, distance, magnification, baseItemSize }) {
  const ref = useRef(null);
  const isHovered = useMotionValue(0);

  const mouseDistance = useTransform(mouseX, val => {
    const rect = ref.current?.getBoundingClientRect() ?? {
      x: 0,
      width: baseItemSize
    };
    return val - rect.x - baseItemSize / 2;
  });

  const targetSize = useTransform(
    mouseDistance,
    [-distance, 0, distance],
    [baseItemSize, magnification, baseItemSize]
  );
  const size = useSpring(targetSize, spring);

  return (
    <motion.div
      ref={ref}
      style={{
        width: size,
        height: size
      }}
      onHoverStart={() => isHovered.set(1)}
      onHoverEnd={() => isHovered.set(0)}
      onFocus={() => isHovered.set(1)}
      onBlur={() => isHovered.set(0)}
      onClick={onClick}
      className={`relative flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 border-2 shadow-md flex-shrink-0 text-zinc-800 dark:text-zinc-50 hover:bg-zinc-50 dark:hover:bg-zinc-800/80 hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors duration-200 ${className}`}
      tabIndex={0}
      role="button"
      aria-haspopup="true">
      {Children.map(children, child => cloneElement(child, { isHovered }))}
    </motion.div>
  );
}

function DockLabel({ children, className = '', ...rest }) {
  const { isHovered } = rest;
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const labelRef = useRef(null);

  useEffect(() => {
    const unsubscribe = isHovered.on('change', latest => {
      setIsVisible(latest === 1);
      
      // Calculate position when tooltip becomes visible
      if (latest === 1 && labelRef.current) {
        const rect = labelRef.current.getBoundingClientRect();
        setTooltipPosition({
          top: rect.top - 30, // Position above the label
          left: rect.left + rect.width / 2 // Center horizontally on the label
        });
      }
    });
    return () => unsubscribe();
  }, [isHovered]);

  const tooltipContent = (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 0 }}
          animate={{ opacity: 1, y: -10 }}
          exit={{ opacity: 0, y: 0 }}
          transition={{ duration: 0.2 }}
          className={`${className} fixed w-fit whitespace-nowrap rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 px-2 py-0.5 text-xs text-zinc-800 dark:text-zinc-50 pointer-events-none z-50`}
          role="tooltip"
          style={{
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            transform: 'translateX(-50%)'
          }}>
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      <div ref={labelRef} style={{ display: 'none' }} />
      {typeof document !== 'undefined' && createPortal(tooltipContent, document.body)}
    </>
  );
}

function DockIcon({ children, className = '' }) {
  return <div className={`flex items-center justify-center ${className}`}>{children}</div>;
}

export default function Dock({
  items,
  className = '',
  spring = { mass: 0.1, stiffness: 150, damping: 12 },
  magnification = 70,
  distance = 200,
  panelHeight = 64,
  dockHeight = 256,
  baseItemSize = 50
}) {
  const mouseX = useMotionValue(Infinity);
  const isHovered = useMotionValue(0);

  const maxHeight = useMemo(
    () => Math.max(dockHeight, magnification + magnification / 2 + 4),
    [magnification, dockHeight]
  );
  const heightRow = useTransform(isHovered, [0, 1], [panelHeight, maxHeight]);
  const height = useSpring(heightRow, spring);

  return (
    <motion.div
      style={{ height, scrollbarWidth: 'none' }}
      className="mx-2 flex max-w-full items-center justify-center">
      <motion.div
        onMouseMove={({ pageX }) => {
          isHovered.set(1);
          mouseX.set(pageX);
        }}
        onMouseLeave={() => {
          isHovered.set(0);
          mouseX.set(Infinity);
        }}
        className={`${className} flex items-center justify-center w-fit gap-4 px-2`}
        style={{ height: panelHeight, pointerEvents: 'auto' }}
        role="toolbar"
        aria-label="Application dock">
        {items.map((item, index) => (
          <DockItem
            key={index}
            onClick={item.onClick}
            className={item.className}
            mouseX={mouseX}
            spring={spring}
            distance={distance}
            magnification={magnification}
            baseItemSize={baseItemSize}>
            <DockIcon>{item.icon}</DockIcon>
            <DockLabel>{item.label}</DockLabel>
          </DockItem>
        ))}
      </motion.div>
    </motion.div>
  );
}
