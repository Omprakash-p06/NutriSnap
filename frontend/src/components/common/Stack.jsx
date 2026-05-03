import { useRef, useState, useEffect } from "react";
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  AnimatePresence,
} from "framer-motion";

/**
 * Stack - A draggable/interactive stack of cards.
 * Inlined from react-bits pattern for full control without external deps.
 */
export default function Stack({
  cards = [],
  randomRotation = false,
  sensitivity = 200,
  sendToBackOnClick = true,
  autoplay = false,
  autoplayDelay = 3000,
  pauseOnHover = false,
}) {
  const [stack, setStack] = useState(
    cards.map((card, i) => ({ id: i, content: card })),
  );
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (!autoplay || (pauseOnHover && isHovered)) return;
    const interval = setInterval(() => {
      setStack((prev) => {
        const newStack = [...prev];
        const first = newStack.shift();
        newStack.push(first);
        return newStack;
      });
    }, autoplayDelay);
    return () => clearInterval(interval);
  }, [autoplay, autoplayDelay, pauseOnHover, isHovered]);

  const sendToBack = (id) => {
    setStack((prev) => {
      const idx = prev.findIndex((c) => c.id === id);
      if (idx === -1) return prev;
      const newStack = [...prev];
      const [card] = newStack.splice(idx, 1);
      return [card, ...newStack];
    });
  };

  return (
    <div
      style={{ position: "relative", width: "100%", height: "100%" }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {stack.map((card, index) => {
        const isTop = index === stack.length - 1;
        const rotation = randomRotation
          ? (Math.random() - 0.5) * 10
          : (index - stack.length / 2) * 3;
        const offsetX = (index - stack.length / 2) * 8;
        const offsetY = (stack.length - 1 - index) * -6;

        return (
          <StackCard
            key={card.id}
            card={card}
            isTop={isTop}
            rotation={rotation}
            offsetX={offsetX}
            offsetY={offsetY}
            sensitivity={sensitivity}
            onSendToBack={() => sendToBackOnClick && sendToBack(card.id)}
            zIndex={index}
          />
        );
      })}
    </div>
  );
}

function StackCard({
  card,
  isTop,
  rotation,
  offsetX,
  offsetY,
  sensitivity,
  onSendToBack,
  zIndex,
}) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useTransform(y, [-sensitivity, sensitivity], [15, -15]);
  const rotateY = useTransform(x, [-sensitivity, sensitivity], [-15, 15]);

  const springX = useSpring(rotateX, { stiffness: 300, damping: 30 });
  const springY = useSpring(rotateY, { stiffness: 300, damping: 30 });

  const handleMouseMove = (e) => {
    if (!isTop) return;
    const rect = e.currentTarget.getBoundingClientRect();
    x.set(e.clientX - rect.left - rect.width / 2);
    y.set(e.clientY - rect.top - rect.height / 2);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      style={{
        position: "absolute",
        inset: 0,
        rotateX: isTop ? springX : 0,
        rotateY: isTop ? springY : 0,
        rotate: rotation,
        x: offsetX,
        y: offsetY,
        zIndex,
        cursor: isTop ? "grab" : "default",
        transformStyle: "preserve-3d",
        borderRadius: "16px",
        overflow: "hidden",
        boxShadow: isTop
          ? "0 25px 60px rgba(0,0,0,0.4), 0 10px 20px rgba(0,0,0,0.2)"
          : "0 8px 20px rgba(0,0,0,0.2)",
        transition: "box-shadow 0.3s ease",
      }}
      whileHover={isTop ? { scale: 1.02 } : {}}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onSendToBack}
    >
      {card.content}
    </motion.div>
  );
}
