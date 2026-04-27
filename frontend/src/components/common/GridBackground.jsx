import { motion } from 'framer-motion';

/**
 * GridBackground
 * A subtle, moving grid background that adds depth to the application.
 */
export default function GridBackground() {
  return (
    <div 
      className="grid-background-container"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1,
        pointerEvents: 'none',
        overflow: 'hidden',
        background: 'var(--bg)',
        transition: 'background 0.3s ease'
      }}
    >
      <motion.div
        animate={{
          backgroundPosition: ['0px 0px', '40px 40px'],
        }}
        transition={{
          repeat: Infinity,
          duration: 10,
          ease: "linear",
        }}
        style={{
          width: '200%',
          height: '200%',
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          backgroundImage: `
            linear-gradient(var(--border) 1px, transparent 1px),
            linear-gradient(90deg, var(--border) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
          opacity: 0.15,
          maskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)',
        }}
      />
    </div>
  );
}
